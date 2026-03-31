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


def test_mark_task_complete_daily_creates_next_occurrence():
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    task = Task("Morning walk", duration_minutes=20, priority="high", frequency="daily")
    mochi.add_task(task)
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None
    assert next_task.title == "Morning walk"
    assert next_task.next_due_date == date.today() + timedelta(days=1)
    assert next_task in mochi.get_tasks()
    assert task not in mochi.get_tasks()


def test_mark_task_complete_weekly_creates_next_occurrence():
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    task = Task("Grooming", duration_minutes=30, priority="medium", frequency="weekly")
    mochi.add_task(task)
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None
    assert next_task.next_due_date == date.today() + timedelta(days=7)
    assert next_task in mochi.get_tasks()


def test_mark_task_complete_as_needed_returns_none():
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    task = Task("Vet visit", duration_minutes=60, priority="high", frequency="as needed")
    mochi.add_task(task)
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    result = scheduler.mark_task_complete(task)

    assert result is None
    assert task in mochi.get_tasks()


def test_next_occurrence_not_due_today():
    task = Task("Morning walk", duration_minutes=20, priority="high", frequency="daily")
    task.next_due_date = date.today() + timedelta(days=1)
    assert task.due_today() is False


def test_next_occurrence_due_today():
    task = Task("Morning walk", duration_minutes=20, priority="high", frequency="daily")
    task.next_due_date = date.today()
    assert task.due_today() is True


# ---------------------------------------------------------------------------
# sort_by_time
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    # Tasks added out of order; sorted() should reorder by HH:MM string.
    owner = Owner("Jordan", available_minutes=120, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Evening walk",  duration_minutes=20, priority="low",  frequency="daily", time="18:00"))
    mochi.add_task(Task("Afternoon nap", duration_minutes=15, priority="low",  frequency="daily", time="13:00"))
    mochi.add_task(Task("Morning feed",  duration_minutes=10, priority="high", frequency="daily", time="07:30"))
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time(mochi.get_tasks())
    times = [t.time for t in sorted_tasks]

    assert times == ["07:30", "13:00", "18:00"]


def test_sort_by_time_no_time_tasks_sort_last():
    # Tasks with time=None must appear after all timed tasks.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Grooming",     duration_minutes=30, priority="medium", frequency="weekly"))          # no time
    mochi.add_task(Task("Morning feed", duration_minutes=10, priority="high",   frequency="daily", time="08:00"))
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time(mochi.get_tasks())

    assert sorted_tasks[0].title == "Morning feed"
    assert sorted_tasks[-1].time is None


def test_sort_by_time_all_no_time_returns_same_count():
    # When no task has a time, the list is returned unchanged in length.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Task A", duration_minutes=10, priority="high",   frequency="daily"))
    mochi.add_task(Task("Task B", duration_minutes=20, priority="medium", frequency="daily"))
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    result = scheduler.sort_by_time(mochi.get_tasks())

    assert len(result) == 2


def test_sort_by_time_single_task_returns_list_of_one():
    # Edge case: a single task should come back in a one-element list.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Only task", duration_minutes=10, priority="high", frequency="daily", time="09:00"))
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)

    result = scheduler.sort_by_time(mochi.get_tasks())

    assert len(result) == 1
    assert result[0].time == "09:00"


def test_sort_by_time_does_not_modify_original_list():
    # sorted() must return a new list; original pet task order stays intact.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Late task",  duration_minutes=10, priority="low",  frequency="daily", time="20:00"))
    mochi.add_task(Task("Early task", duration_minutes=10, priority="high", frequency="daily", time="06:00"))
    owner.add_pet(mochi)
    original_order = [t.title for t in mochi.get_tasks()]
    scheduler = Scheduler(owner)

    scheduler.sort_by_time(mochi.get_tasks())

    assert [t.title for t in mochi.get_tasks()] == original_order


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------

def _make_plan_with_conflict():
    """Helper: two pets each with a task at 08:00, guaranteed conflict."""
    owner = Owner("Jordan", available_minutes=120, min_priority="low")
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")
    mochi.add_task(Task("Feeding",    duration_minutes=10, priority="high", frequency="daily", time="08:00"))
    luna.add_task( Task("Medication", duration_minutes=5,  priority="high", frequency="daily", time="08:00"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def test_detect_conflicts_returns_warning_for_shared_time():
    # Two tasks at the same time across different pets should be flagged.
    owner = _make_plan_with_conflict()
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    warnings = scheduler.detect_conflicts(plan["scheduled"])

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_warning_contains_task_names():
    # The warning string must name both conflicting tasks.
    owner = _make_plan_with_conflict()
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    warnings = scheduler.detect_conflicts(plan["scheduled"])

    assert "Feeding" in warnings[0]
    assert "Medication" in warnings[0]


def test_detect_conflicts_no_conflict_returns_empty_list():
    # All tasks at unique times — no warnings expected.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Task A", duration_minutes=10, priority="high",   frequency="daily", time="08:00"))
    mochi.add_task(Task("Task B", duration_minutes=10, priority="medium", frequency="daily", time="09:00"))
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    warnings = scheduler.detect_conflicts(plan["scheduled"])

    assert warnings == []


def test_detect_conflicts_tasks_without_time_are_ignored():
    # Tasks with time=None cannot conflict and must not produce warnings.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Task A", duration_minutes=10, priority="high",   frequency="daily"))
    mochi.add_task(Task("Task B", duration_minutes=10, priority="medium", frequency="daily"))
    owner.add_pet(mochi)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    warnings = scheduler.detect_conflicts(plan["scheduled"])

    assert warnings == []


def test_detect_conflicts_three_tasks_same_time_one_warning():
    # Three tasks in the same slot produce exactly one warning (one slot).
    owner = Owner("Jordan", available_minutes=120, min_priority="low")
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")
    mochi.add_task(Task("Task A", duration_minutes=5, priority="high", frequency="daily", time="08:00"))
    mochi.add_task(Task("Task B", duration_minutes=5, priority="high", frequency="daily", time="09:00"))
    luna.add_task( Task("Task C", duration_minutes=5, priority="high", frequency="daily", time="08:00"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    warnings = scheduler.detect_conflicts(plan["scheduled"])

    # Only the 08:00 slot is a conflict; 09:00 is unique.
    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_empty_scheduled_list():
    # An empty input must return an empty list without raising.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts([])

    assert warnings == []


# ---------------------------------------------------------------------------
# filter_tasks
# ---------------------------------------------------------------------------

def _make_scheduled_plan():
    """Helper: owner with two pets, returns a built plan ready for filtering."""
    owner = Owner("Jordan", available_minutes=120, min_priority="low")
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")
    mochi.add_task(Task("Morning walk", duration_minutes=20, priority="high",   frequency="daily", time="07:30"))
    mochi.add_task(Task("Feeding",      duration_minutes=10, priority="high",   frequency="daily", time="08:00"))
    luna.add_task( Task("Medication",   duration_minutes=5,  priority="high",   frequency="daily", time="08:30"))
    luna.add_task( Task("Litter",       duration_minutes=10, priority="medium", frequency="daily", time="09:00"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()
    return scheduler, plan


def test_filter_tasks_by_pet_name():
    # Only Luna's tasks should appear when filtering by pet_name="Luna".
    scheduler, plan = _make_scheduled_plan()

    result = scheduler.filter_tasks(plan["scheduled"], pet_name="Luna")

    assert all(item["pet"] == "Luna" for item in result)
    assert len(result) == 2


def test_filter_tasks_unknown_pet_returns_empty():
    # A pet name that doesn't exist should return an empty list, not raise.
    scheduler, plan = _make_scheduled_plan()

    result = scheduler.filter_tasks(plan["scheduled"], pet_name="Rex")

    assert result == []


def test_filter_tasks_by_status_pending():
    # All scheduled tasks start as pending (not completed today).
    scheduler, plan = _make_scheduled_plan()

    result = scheduler.filter_tasks(plan["scheduled"], status="pending")

    assert len(result) == len(plan["scheduled"])


def test_filter_tasks_by_status_completed_after_mark():
    # After marking one task complete, it should appear under status="completed".
    scheduler, plan = _make_scheduled_plan()
    target_task = plan["scheduled"][0]["task"]
    target_task.mark_complete()

    completed = scheduler.filter_tasks(plan["scheduled"], status="completed")
    pending   = scheduler.filter_tasks(plan["scheduled"], status="pending")

    assert len(completed) == 1
    assert len(pending) == len(plan["scheduled"]) - 1


def test_filter_tasks_combined_pet_and_status():
    # Combining pet_name and status should intersect both filters.
    scheduler, plan = _make_scheduled_plan()
    # Mark one of Luna's tasks complete.
    luna_item = next(item for item in plan["scheduled"] if item["pet"] == "Luna")
    luna_item["task"].mark_complete()

    result = scheduler.filter_tasks(plan["scheduled"], pet_name="Luna", status="completed")

    assert len(result) == 1
    assert result[0]["pet"] == "Luna"


def test_filter_tasks_no_filter_returns_all():
    # Calling filter_tasks with no arguments must return the full list.
    scheduler, plan = _make_scheduled_plan()

    result = scheduler.filter_tasks(plan["scheduled"])

    assert len(result) == len(plan["scheduled"])


def test_filter_tasks_empty_input_returns_empty():
    # An empty input list must return empty without raising.
    scheduler, plan = _make_scheduled_plan()

    result = scheduler.filter_tasks([])

    assert result == []


# ---------------------------------------------------------------------------
# build_plan edge cases
# ---------------------------------------------------------------------------

def test_build_plan_owner_with_no_pets():
    # An owner with no pets should return empty scheduled and skipped lists.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    plan = Scheduler(owner).build_plan()

    assert plan["scheduled"] == []
    assert plan["skipped"] == []


def test_build_plan_pet_with_no_tasks():
    # A pet registered but with no tasks contributes nothing to the plan.
    owner = Owner("Jordan", available_minutes=60, min_priority="low")
    owner.add_pet(Pet("Mochi", "dog"))
    plan = Scheduler(owner).build_plan()

    assert plan["scheduled"] == []
    assert plan["skipped"] == []


def test_build_plan_zero_available_minutes():
    # With zero budget, every task must land in skipped.
    owner = Owner("Jordan", available_minutes=0, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Walk", duration_minutes=20, priority="high", frequency="daily"))
    owner.add_pet(mochi)
    plan = Scheduler(owner).build_plan()

    assert plan["scheduled"] == []
    assert len(plan["skipped"]) == 1


def test_build_plan_budget_exactly_fits_one_task():
    # A task whose duration equals available_minutes should be scheduled.
    owner = Owner("Jordan", available_minutes=20, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Walk", duration_minutes=20, priority="high", frequency="daily"))
    owner.add_pet(mochi)
    plan = Scheduler(owner).build_plan()

    assert len(plan["scheduled"]) == 1
    assert plan["scheduled"][0]["task"].title == "Walk"


def test_build_plan_all_tasks_same_priority_sorted_by_duration():
    # When priority is equal, shorter tasks must come first.
    owner = Owner("Jordan", available_minutes=120, min_priority="low")
    mochi = Pet("Mochi", "dog")
    mochi.add_task(Task("Long task",   duration_minutes=30, priority="medium", frequency="daily"))
    mochi.add_task(Task("Short task",  duration_minutes=5,  priority="medium", frequency="daily"))
    mochi.add_task(Task("Medium task", duration_minutes=15, priority="medium", frequency="daily"))
    owner.add_pet(mochi)
    plan = Scheduler(owner).build_plan()
    titles = [item["task"].title for item in plan["scheduled"]]

    assert titles.index("Short task") < titles.index("Medium task")
    assert titles.index("Medium task") < titles.index("Long task")
