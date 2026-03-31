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
