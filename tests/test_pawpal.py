from datetime import date, timedelta
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", duration_minutes=20, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    assert len(pet.get_tasks()) == 1


def test_due_today_daily_not_yet_completed():
    task = Task("Morning walk", duration_minutes=20, priority="high", frequency="daily")
    assert task.due_today() is True


def test_due_today_daily_completed_today():
    task = Task("Morning walk", duration_minutes=20, priority="high", frequency="daily")
    task.mark_complete()
    assert task.due_today() is False


def test_due_today_weekly_never_completed():
    task = Task("Grooming", duration_minutes=30, priority="medium", frequency="weekly")
    assert task.due_today() is True


def test_due_today_weekly_completed_6_days_ago():
    task = Task("Grooming", duration_minutes=30, priority="medium", frequency="weekly")
    task.last_completed_date = date.today() - timedelta(days=6)
    assert task.due_today() is False


def test_due_today_weekly_completed_7_days_ago():
    task = Task("Grooming", duration_minutes=30, priority="medium", frequency="weekly")
    task.last_completed_date = date.today() - timedelta(days=7)
    assert task.due_today() is True


def test_due_today_as_needed_never_scheduled():
    task = Task("Vet visit", duration_minutes=60, priority="high", frequency="as needed")
    assert task.due_today() is False


def test_completed_is_false_before_mark_complete():
    task = Task("Feeding", duration_minutes=10, priority="high")
    assert task.completed is False


def test_completed_is_true_after_mark_complete():
    task = Task("Feeding", duration_minutes=10, priority="high")
    task.mark_complete()
    assert task.completed is True


def test_due_today_daily_never_completed():
    task = Task("Morning walk", duration_minutes=20, priority="high", frequency="daily")
    task.last_completed_date = None
    assert task.due_today() is True


def test_add_task_duplicate_title_raises():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Morning walk", duration_minutes=20, priority="high"))
    with pytest.raises(ValueError, match="Morning walk"):
        pet.add_task(Task("Morning walk", duration_minutes=20, priority="high"))


def test_add_task_duplicate_title_case_insensitive_raises():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Morning walk", duration_minutes=20, priority="high"))
    with pytest.raises(ValueError, match="morning walk"):
        pet.add_task(Task("morning walk", duration_minutes=20, priority="high"))


def test_add_task_different_title_does_not_raise():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Morning walk", duration_minutes=20, priority="high"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    assert len(pet.get_tasks()) == 2


def test_add_task_same_title_different_pet_does_not_raise():
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    luna.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    assert len(mochi.get_tasks()) == 1
    assert len(luna.get_tasks()) == 1


def _make_owner_with_pets():
    """Helper: owner with two pets and a mix of tasks."""
    owner = Owner("Jordan", available_minutes=40, min_priority="low")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Morning walk", duration_minutes=20, priority="high", frequency="daily"))
    mochi.add_task(Task("Grooming", duration_minutes=30, priority="medium", frequency="weekly"))
    luna.add_task(Task("Medication", duration_minutes=5, priority="high", frequency="daily"))
    luna.add_task(Task("Vet visit", duration_minutes=60, priority="high", frequency="as needed"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def test_build_plan_returns_dict_with_scheduled_and_skipped():
    owner = _make_owner_with_pets()
    plan = Scheduler(owner).build_plan()
    assert "scheduled" in plan
    assert "skipped" in plan


def test_build_plan_as_needed_tasks_are_skipped():
    owner = _make_owner_with_pets()
    plan = Scheduler(owner).build_plan()
    skipped_titles = [item["task"].title for item in plan["skipped"]]
    assert "Vet visit" in skipped_titles


def test_build_plan_skipped_has_reason_and_pet():
    owner = _make_owner_with_pets()
    plan = Scheduler(owner).build_plan()
    for item in plan["skipped"]:
        assert "reason" in item
        assert "pet" in item


def test_build_plan_overflow_task_goes_to_skipped():
    owner = Owner("Jordan", available_minutes=10, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Long bath", duration_minutes=60, priority="high", frequency="daily"))
    owner.add_pet(mochi)
    plan = Scheduler(owner).build_plan()
    assert len(plan["scheduled"]) == 0
    skipped_reasons = [item["reason"] for item in plan["skipped"]]
    assert "exceeds time budget" in skipped_reasons


def test_build_plan_sorted_priority_desc_duration_asc():
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Long high", duration_minutes=30, priority="high", frequency="daily"))
    mochi.add_task(Task("Short high", duration_minutes=10, priority="high", frequency="daily"))
    mochi.add_task(Task("Medium task", duration_minutes=15, priority="medium", frequency="daily"))
    owner.add_pet(mochi)
    plan = Scheduler(owner).build_plan()
    scheduled_titles = [item["task"].title for item in plan["scheduled"]]
    assert scheduled_titles.index("Short high") < scheduled_titles.index("Long high")
    assert scheduled_titles.index("Long high") < scheduled_titles.index("Medium task")


def test_build_plan_below_min_priority_goes_to_skipped():
    owner = Owner("Jordan", available_minutes=60, min_priority="high")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Low task", duration_minutes=10, priority="low", frequency="daily"))
    mochi.add_task(Task("High task", duration_minutes=10, priority="high", frequency="daily"))
    owner.add_pet(mochi)
    plan = Scheduler(owner).build_plan()
    scheduled_titles = [item["task"].title for item in plan["scheduled"]]
    skipped_titles = [item["task"].title for item in plan["skipped"]]
    assert "High task" in scheduled_titles
    assert "Low task" in skipped_titles
