import json
from datetime import date, timedelta
from pathlib import Path


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: str, frequency: str = "daily", time: str | None = None):
        """Initialize a care task with a title, duration, priority, frequency, and optional start time (HH:MM)."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.frequency = frequency
        self.time = time  # optional start time in "HH:MM" format, e.g. "08:30"
        self.last_completed_date: date | None = None
        self.next_due_date: date | None = None  # set when a next occurrence is scheduled

    @property
    def completed(self) -> bool:
        """True if this task was marked complete today."""
        return self.last_completed_date == date.today()

    def due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        if self.next_due_date is not None:
            return self.next_due_date <= date.today()
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

    def urgency_score(self) -> float:
        """Composite score combining priority rank and days overdue.

        Formula: priority_rank * 10 + days_overdue

        Days overdue counts how many days past the task's expected recurrence
        interval have elapsed since it was last completed. A daily task last
        completed 3 days ago is 2 days overdue; a weekly task last completed
        10 days ago is 3 days overdue. 'as needed' tasks never accumulate age.

        Examples:
            - High priority, on time:       3 * 10 + 0  = 30
            - High priority, 5 days late:   3 * 10 + 5  = 35
            - Medium priority, never done:  2 * 10 + 1  = 21  (counts as 1 cycle overdue)
            - Low priority, 8 days late:    1 * 10 + 8  = 18

        A medium task that is badly overdue (score 22+) can outrank a
        high-priority task that is right on schedule (score 30 unchanged),
        which keeps the most time-sensitive care from being permanently
        deprioritized behind high-priority tasks that were completed recently.
        """
        rank = self.priority_rank()
        if self.frequency == "as needed":
            return float(rank * 10)
        expected_days = 1 if self.frequency == "daily" else 7
        if self.last_completed_date is None:
            days_overdue = float(expected_days)
        else:
            elapsed = (date.today() - self.last_completed_date).days
            days_overdue = float(max(0, elapsed - expected_days))
        return rank * 10 + days_overdue

    def mark_complete(self) -> None:
        """Mark the task as completed today."""
        self.last_completed_date = date.today()

    def create_next_occurrence(self) -> "Task":
        """Return a new Task instance scheduled for the next occurrence of this task.

        Calculates the next due date using timedelta based on the task's frequency:
        daily tasks recur in 1 day, weekly tasks recur in 7 days. The new instance
        copies all attributes (title, duration, priority, frequency, time) and sets
        next_due_date so due_today() returns False until that date arrives.

        Returns:
            A fresh Task with next_due_date set to today + 1 day (daily) or
            today + 7 days (weekly).

        Raises:
            No exception — caller is responsible for ensuring frequency is
            'daily' or 'weekly' before calling this method.
        """
        days = 1 if self.frequency == "daily" else 7
        next_task = Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            time=self.time,
        )
        next_task.next_due_date = date.today() + timedelta(days=days)
        return next_task

    def to_dict(self) -> dict:
        """Serialize this Task to a JSON-safe dictionary."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "frequency": self.frequency,
            "time": self.time,
            "last_completed_date": self.last_completed_date.isoformat() if self.last_completed_date else None,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a dictionary produced by to_dict()."""
        task = cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=data["priority"],
            frequency=data["frequency"],
            time=data.get("time"),
        )
        if data.get("last_completed_date"):
            task.last_completed_date = date.fromisoformat(data["last_completed_date"])
        if data.get("next_due_date"):
            task.next_due_date = date.fromisoformat(data["next_due_date"])
        return task

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

    def to_dict(self) -> dict:
        """Serialize this Pet (and all its tasks) to a JSON-safe dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Reconstruct a Pet (and its tasks) from a dictionary produced by to_dict()."""
        pet = cls(name=data["name"], species=data["species"])
        for task_data in data.get("tasks", []):
            # Bypass add_task() duplicate check: stored data is already validated.
            pet.tasks.append(Task.from_dict(task_data))
        return pet

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

    def to_dict(self) -> dict:
        """Serialize this Owner (and all pets and tasks) to a JSON-safe dictionary."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "min_priority": self.min_priority,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Reconstruct an Owner (and its full pet/task tree) from a to_dict() dictionary."""
        owner = cls(
            name=data["name"],
            available_minutes=data["available_minutes"],
            min_priority=data["min_priority"],
        )
        for pet_data in data.get("pets", []):
            owner.pets.append(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, path: str = "data.json") -> None:
        """Persist the owner, all pets, and all tasks to a JSON file.

        Dates are stored as ISO-format strings (YYYY-MM-DD) so they survive
        serialization and can be reconstructed exactly with date.fromisoformat().
        The file is written atomically by serializing to a string first so a
        failed write does not truncate an existing file mid-stream.
        """
        payload = json.dumps(self.to_dict(), indent=2)
        Path(path).write_text(payload)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load and reconstruct an Owner from a JSON file written by save_to_json().

        Raises FileNotFoundError if the file does not exist — callers should
        check with Path(path).exists() before calling.
        """
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)

    def __repr__(self):
        """Return a readable string representation of the owner."""
        return f"Owner({self.name!r}, {len(self.pets)} pets)"


class Scheduler:
    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner whose pets and constraints it will use."""
        self.owner = owner

    def build_plan(self) -> dict:
        """Build today's schedule. Returns {"scheduled": [...], "skipped": [...]}."""
        min_rank = {"low": 1, "medium": 2, "high": 3}.get(self.owner.min_priority, 1)

        scheduled = []
        skipped = []
        eligible = []

        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if not task.due_today():
                    reason = "scheduled as needed" if task.frequency == "as needed" else "not due today"
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

    def build_plan_by_urgency(self) -> dict:
        """Build today's schedule sorted by urgency score instead of plain priority.

        Urgency score = priority_rank * 10 + days_overdue (see Task.urgency_score()).
        This promotes tasks that are falling behind their recurrence schedule above
        same-priority tasks that are right on time, preventing important but
        consistently-completed tasks from always crowding out tasks that keep
        slipping.

        Returns the same {"scheduled": [...], "skipped": [...]} dict structure as
        build_plan() so callers can use either method interchangeably.
        """
        min_rank = {"low": 1, "medium": 2, "high": 3}.get(self.owner.min_priority, 1)

        scheduled = []
        skipped = []
        eligible = []

        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if not task.due_today():
                    reason = "scheduled as needed" if task.frequency == "as needed" else "not due today"
                    skipped.append({"task": task, "reason": reason, "pet": pet.name})
                elif task.priority_rank() < min_rank:
                    skipped.append({"task": task, "reason": "below minimum priority", "pet": pet.name})
                else:
                    eligible.append((task, pet.name))

        # Sort by descending urgency score, then ascending duration as tiebreaker.
        eligible.sort(key=lambda tp: (-tp[0].urgency_score(), tp[0].duration_minutes))

        total = 0
        for task, pet_name in eligible:
            if total + task.duration_minutes <= self.owner.available_minutes:
                total += task.duration_minutes
                score = task.urgency_score()
                reason = (
                    f"{task.priority.capitalize()} priority · urgency {score:.0f} — "
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

    def detect_conflicts(self, scheduled: list) -> list:
        """Return warning strings for any time slot shared by two or more scheduled tasks.

        Groups scheduled task dicts by their start time and flags any slot where
        more than one task is assigned. Conflict detection uses exact time-string
        matching ("HH:MM") — overlapping durations are not checked. Tasks with
        no 'time' value are ignored. Results are sorted chronologically.

        Args:
            scheduled: list of task dicts with 'task' and 'pet' keys, typically
                       plan['scheduled'] returned by build_plan().

        Returns:
            A list of warning strings, one per conflicting time slot, in the form
            "WARNING: conflict at HH:MM — Task A (Pet1), Task B (Pet2)".
            Returns an empty list if no conflicts are found. Never raises.
        """
        by_time = {}
        for item in scheduled:
            t = item["task"].time
            if t is not None:
                by_time.setdefault(t, []).append(item)

        warnings = []
        for time_slot, items in sorted(by_time.items()):
            if len(items) > 1:
                names = ", ".join(
                    f"{item['task'].title} ({item['pet']})" for item in items
                )
                warnings.append(f"WARNING: conflict at {time_slot} — {names}")
        return warnings

    def sort_by_time(self, tasks: list) -> list:
        """Return a new list of Task objects sorted chronologically by start time.

        Uses Python's sorted() with a lambda key that extracts each task's 'time'
        string. Because times are stored in zero-padded "HH:MM" format, lexicographic
        string comparison produces correct chronological order. Tasks with time=None
        receive the sentinel key "99:99" so they sort to the end of the list.

        Args:
            tasks: list of Task objects to sort. The original list is not modified.

        Returns:
            A new list of the same Task objects in ascending time order, with
            un-timed tasks appended last.
        """
        return sorted(tasks, key=lambda t: t.time if t.time is not None else "99:99")

    def filter_tasks(self, tasks: list, pet_name: str | None = None, status: str | None = None) -> list:
        """Filter a list of scheduled task dicts by pet name and/or completion status.

        Both filters are optional and can be combined. Filtering is display-only —
        it does not re-run the scheduler or alter any task state. The original list
        is not modified.

        Args:
            tasks:    list of task dicts with 'task' and 'pet' keys, typically
                      plan['scheduled'] returned by build_plan().
            pet_name: if provided, only items whose 'pet' matches this string are
                      kept. Case-sensitive. Pass None to include all pets.
            status:   'pending' keeps tasks where task.completed is False (not yet
                      done today). 'completed' keeps tasks where task.completed is
                      True (marked done today). Pass None to include all statuses.

        Returns:
            A new list containing only the items that match all supplied filters.
            Returns an empty list if no items match. Never raises.
        """
        result = tasks
        if pet_name is not None:
            result = [item for item in result if item["pet"] == pet_name]
        if status == "pending":
            result = [item for item in result if not item["task"].completed]
        elif status == "completed":
            result = [item for item in result if item["task"].completed]
        return result

    def mark_task_complete(self, task: Task) -> "Task | None":
        """Mark task complete. For daily/weekly tasks, schedules the next occurrence.

        The completed task is replaced in the pet's task list with a new instance
        due in 1 day (daily) or 7 days (weekly). Returns the new Task, or None
        for 'as needed' tasks.
        """
        task.mark_complete()
        if task.frequency not in ("daily", "weekly"):
            return None

        owning_pet = None
        for pet in self.owner.pets:
            if task in pet.tasks:
                owning_pet = pet
                break

        if owning_pet is None:
            return None

        next_task = task.create_next_occurrence()
        owning_pet.tasks.remove(task)
        owning_pet.tasks.append(next_task)
        return next_task

    def get_pending_tasks(self) -> list:
        """Return all incomplete tasks across the owner's pets."""
        return [t for t in self.owner.get_all_tasks() if not t.completed]

    def get_completed_tasks(self) -> list:
        """Return all completed tasks across the owner's pets."""
        return [t for t in self.owner.get_all_tasks() if t.completed]
