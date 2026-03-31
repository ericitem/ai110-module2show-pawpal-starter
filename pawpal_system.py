from datetime import date


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: str, frequency: str = "daily"):
        """Initialize a care task with a title, duration, priority, and frequency."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.frequency = frequency
        self.last_completed_date: date | None = None

    @property
    def completed(self) -> bool:
        """True if this task was marked complete today."""
        return self.last_completed_date == date.today()

    def due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        if self.frequency == "as needed":
            return False
        if self.frequency == "daily":
            if self.last_completed_date is None:
                return True
            return self.last_completed_date != date.today()
        if self.frequency == "weekly":
            if self.last_completed_date is None:
                return True
            return (date.today() - self.last_completed_date).days > 6
        raise ValueError(f"Unknown frequency {self.frequency!r}. Must be 'daily', 'weekly', or 'as needed'.")

    def priority_rank(self) -> int:
        """Return a numeric rank for the task's priority (high=3, medium=2, low=1)."""
        valid = {"low": 1, "medium": 2, "high": 3}
        if self.priority not in valid:
            raise ValueError(f"Invalid priority {self.priority!r}. Must be 'low', 'medium', or 'high'.")
        return valid[self.priority]

    def mark_complete(self) -> None:
        """Mark the task as completed today."""
        self.last_completed_date = date.today()

    def __repr__(self):
        """Return a readable string representation of the task."""
        status = "done" if self.completed else "pending"
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority!r}, {self.frequency!r}, {status})"


class Pet:
    def __init__(self, name: str, species: str):
        """Initialize a pet with a name, species, and an empty task list."""
        self.name = name
        self.species = species
        self.tasks = []

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list. Raises ValueError on duplicate title."""
        for existing in self.tasks:
            if existing.title.lower() == task.title.lower():
                raise ValueError(
                    f"Task '{task.title}' already exists for {self.name}. Remove it first."
                )
        self.tasks.append(task)

    def get_tasks(self) -> list:
        """Return the full list of tasks assigned to this pet."""
        return self.tasks

    def __repr__(self):
        """Return a readable string representation of the pet."""
        return f"Pet({self.name!r}, {self.species!r}, {len(self.tasks)} tasks)"


class Owner:
    def __init__(self, name: str, available_minutes: int, min_priority: str):
        """Initialize an owner with scheduling constraints and an empty pet list."""
        self.name = name
        self.available_minutes = available_minutes
        self.min_priority = min_priority
        self.pets = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list:
        """Return a flat list of all tasks across every pet owned by this owner."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def __repr__(self):
        """Return a readable string representation of the owner."""
        return f"Owner({self.name!r}, {len(self.pets)} pets)"


class Scheduler:
    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner whose pets and constraints it will use."""
        self.owner = owner

    def build_plan(self) -> dict:
        """Build today's schedule. Returns {"scheduled": [...], "skipped": [...]}."""
        priority_order = {"low": 1, "medium": 2, "high": 3}
        min_rank = priority_order.get(self.owner.min_priority, 1)

        scheduled = []
        skipped = []
        eligible = []

        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if not task.due_today():
                    if task.frequency == "as needed":
                        reason = "scheduled as needed"
                    else:
                        reason = "not due today"
                    skipped.append({"task": task, "reason": reason, "pet": pet.name})
                elif task.priority_rank() < min_rank:
                    skipped.append({"task": task, "reason": "below minimum priority", "pet": pet.name})
                else:
                    eligible.append((task, pet.name))

        eligible.sort(key=lambda tp: (-tp[0].priority_rank(), tp[0].duration_minutes))

        total = 0
        for task, pet_name in eligible:
            if total + task.duration_minutes <= self.owner.available_minutes:
                total += task.duration_minutes
                reason = (
                    f"{task.priority.capitalize()} priority — "
                    f"fits within time budget ({total}/{self.owner.available_minutes} min used)"
                )
                scheduled.append({
                    "task": task,
                    "reason": reason,
                    "cumulative_minutes": total,
                    "pet": pet_name,
                })
            else:
                skipped.append({"task": task, "reason": "exceeds time budget", "pet": pet_name})

        return {"scheduled": scheduled, "skipped": skipped}

    def explain_plan(self, plan: dict) -> str:
        """Format the plan as a human-readable schedule string."""
        scheduled = plan["scheduled"]
        skipped = plan["skipped"]

        if not scheduled:
            return "No tasks scheduled today. Try lowering the minimum priority or adding more tasks."

        total = scheduled[-1]["cumulative_minutes"]
        pets = ", ".join(p.name for p in self.owner.pets)
        lines = [
            f"Owner  : {self.owner.name}",
            f"Pets   : {pets}",
            f"Budget : {total}/{self.owner.available_minutes} min used",
            "",
        ]
        for i, item in enumerate(scheduled, start=1):
            task = item["task"]
            lines.append(f"  {i}. {task.title} ({item['pet']})")
            lines.append(f"     Duration  : {task.duration_minutes} min")
            lines.append(f"     Priority  : {task.priority}")
            lines.append(f"     Frequency : {task.frequency}")
            lines.append(f"     Why       : {item['reason']}")
            lines.append("")

        if skipped:
            lines.append("Skipped tasks:")
            for item in skipped:
                lines.append(f"  - {item['task'].title} ({item['pet']}): {item['reason']}")
            lines.append("")

        return "\n".join(lines)

    def mark_task_complete(self, task: Task) -> None:
        """Mark the given task as completed."""
        task.mark_complete()

    def get_pending_tasks(self) -> list:
        """Return all incomplete tasks across the owner's pets."""
        return [t for t in self.owner.get_all_tasks() if not t.completed]

    def get_completed_tasks(self) -> list:
        """Return all completed tasks across the owner's pets."""
        return [t for t in self.owner.get_all_tasks() if t.completed]
