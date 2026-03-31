from datetime import date, timedelta
import pytest
from pawpal_system import Task, Pet


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
