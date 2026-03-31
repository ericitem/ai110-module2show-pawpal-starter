class Owner:
    def __init__(self, name: str, available_minutes: int, min_priority: str):
        self.name = name
        self.available_minutes = available_minutes
        self.min_priority = min_priority

    def __repr__(self):
        return f"Owner({self.name!r}, {self.available_minutes}min, min_priority={self.min_priority!r})"


class Pet:
    def __init__(self, name: str, species: str, owner: Owner):
        self.name = name
        self.species = species
        self.owner = owner

    def __repr__(self):
        return f"Pet({self.name!r}, {self.species!r})"


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: str):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority

    def priority_rank(self) -> int:
        return {"low": 1, "medium": 2, "high": 3}.get(self.priority, 0)

    def __repr__(self):
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority!r})"


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks = []

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def build_plan(self) -> list:
        raise NotImplementedError

    def explain_plan(self, plan: list) -> str:
        raise NotImplementedError
