# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+ are:

1. **Set up their pet profile**: The user enters basic information about themselves and their pet, including the owner's name, the pet's name, and the species. This profile provides the context the scheduler needs to personalize the plan.

2. **Add care tasks**: The user defines individual care tasks for their pet, such as a morning walk, feeding, medication, or grooming. Each task has a title, an estimated duration in minutes, and a priority level (low, medium, or high) so the scheduler knows how to weigh it.

3. **Generate and view the daily schedule**: The user triggers the scheduler to produce an ordered, time-aware plan for the day. The schedule selects and sequences tasks based on priority and available time, and explains why each task was included and when it is scheduled.

The initial UML design consists of four classes: Owner, Pet, Task, and Scheduler.

**Owner** holds the constraints that govern the schedule: the owner's name, how many minutes they have available today, and the minimum priority level they care about. It has no behavior beyond storing that data.

**Pet** represents the animal being cared for. It stores the pet's name and species, and holds a reference back to its Owner so the scheduler knows whose constraints apply.

**Task** represents a single care activity. It stores the task title, how long it takes in minutes, and its priority (low, medium, or high). It has one method, `priority_rank()`, which converts the priority string into a number (1, 2, or 3) so tasks can be sorted.

**Scheduler** is the coordinator. It holds an Owner, a Pet, and a list of Tasks. Its `add_task()` method adds tasks to the candidate list. Its `build_plan()` method applies the owner's constraints: filtering out tasks below the minimum priority, sorting the rest by priority, and greedily filling up to the available time budget. Its `explain_plan()` method formats the resulting plan as human-readable text for display in the UI.

**b. Design changes**

Two changes were made after reviewing the initial skeleton.

**1. `Task.priority_rank()` now raises a `ValueError` for invalid input.**
The original design had `priority_rank()` return `0` silently if an unrecognized priority string was passed. This would cause a task to be quietly excluded from every plan with no indication of why. The fix raises a `ValueError` with a descriptive message so the problem is immediately visible instead of producing a hard-to-trace bug.

**2. `Scheduler` gained a `clear_tasks()` method.**
The initial design had no way to reset the task list once tasks were added. In a Streamlit app where the user can click "Generate schedule" multiple times, the same tasks would be re-added on each run and pile up in the list. Adding `clear_tasks()` lets the UI wipe the list before re-adding tasks, keeping each schedule generation clean and independent.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: available time, task priority, and task recurrence.

- **Available time** is the hard budget. `build_plan()` greedily adds tasks in order and stops when the next task would overflow `owner.available_minutes`. This is enforced first because no matter how important a task is, the owner cannot do it if they have no time.

- **Priority** is the primary sort key. Tasks are sorted high → medium → low, then by duration (shorter first) when priority ties. This ensures the most important care is always attempted before lower-priority items, and that within a priority band the owner can fit more tasks by starting with the smallest ones.

- **Recurrence** is the entry filter. `due_today()` runs before any priority or time check. A task that is not due today — because it was completed earlier today, because it was completed within the past 6 days (weekly), or because it is marked `as needed` — never enters the eligible pool at all. This prevents the plan from filling up with tasks that don't need to happen today.

Priority was chosen as the primary ordering criterion because a pet owner's most urgent concern is "did my pet get its medication?" not "did I use my time efficiently?" Time budget enforcement comes second because a plan that overcommits an owner is worse than a shorter plan that actually gets done.

**b. Tradeoffs**

**Conflict detection checks for exact start-time matches, not overlapping durations.**

The `detect_conflicts()` method flags two tasks as conflicting only if they share the same `time` value (e.g., both set to `"08:00"`). It does not check whether a task's duration causes it to overlap with the next one. For example, a 30-minute task starting at `"08:00"` and a second task starting at `"08:20"` would not be flagged, even though the first task would still be running when the second one begins.

This is a reasonable tradeoff for a pet care app at this stage for two reasons. First, most pet care tasks are interruptible or parallelizable: feeding a dog and giving a cat medication can reasonably happen in the same window without strict sequencing. Second, implementing overlap detection requires knowing both a start time and a duration for every task, then checking whether the interval `[start, start + duration)` for one task intersects with the interval for another. That logic is more complex to implement and harder to explain to a user than a simple "two things are scheduled at the same time" warning. The exact-match approach catches the most obvious scheduling mistakes — double-booking the same minute — while keeping the code and the user-facing output easy to understand.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used in three distinct phases of this project.

During **design**, I used AI to pressure-test the initial UML. After drafting the four-class diagram, I asked the AI to identify any missing methods or attributes that would be needed to implement the described behaviors. This surfaced `due_today()` and `create_next_occurrence()` early, before any code was written, which prevented a situation where the class structure would need to be restructured mid-implementation.

During **implementation**, I used AI to generate boilerplate for the more mechanical parts — the `__repr__` methods, the `filter_tasks` list comprehension, and the initial structure of the test helpers like `_make_owner_with_pets()`. These are correct-by-inspection but tedious to write. Having AI produce a first draft let me focus review effort on the logic that actually mattered: `build_plan()`, `due_today()`, and `mark_task_complete()`.

During **testing**, I used AI to enumerate edge cases I might have missed. After writing the initial happy-path tests, I asked: "What inputs or states could make each method return an unexpected result?" This produced the zero-budget test, the exactly-fits test, and the three-tasks-same-slot conflict test — all of which verified real behavior rather than just confirming the normal path worked.

The most helpful prompt pattern was specificity: "Given this method signature and docstring, what are all the distinct code paths that need a test?" produced better test ideas than "write tests for this."

**b. Judgment and verification**

When generating the `mark_task_complete()` method, the AI's first suggestion removed the completed task from the pet's list and appended the next occurrence, but it did not handle the case where the task does not belong to any of the owner's pets. The method silently returned `None` without marking the task complete at all.

I identified this by reading through the control flow manually: the method called `task.mark_complete()` first, then searched for the owning pet. If the search failed, the task was already marked complete but the pet's list was never updated — an inconsistent state that would cause the next call to `build_plan()` to include a completed task. I fixed it by verifying the owning pet exists before modifying any state and adding a test (`test_mark_task_complete_as_needed_returns_none`) that exercises the return value.

The broader lesson was that AI-generated methods that involve searching through a data structure and then mutating it are especially prone to partial-failure bugs. Reading the generated code as if writing a code review — not just checking that it runs — caught this before it became a runtime issue.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers four behavioral categories:

**Task state and recurrence (11 tests).** These verify that `due_today()` returns the correct answer across every combination of frequency and completion history: a daily task never completed, completed today, completed yesterday; a weekly task never completed, completed 6 days ago, completed 7 days ago; an `as needed` task; and a task with `next_due_date` set. These tests are the foundation because every other method in the system depends on `due_today()` working correctly.

**Pet task management (5 tests).** These verify that `add_task()` rejects duplicates (case-insensitively), allows the same title for different pets, and correctly reflects task count.

**`build_plan()` scheduling logic (8 tests).** These verify priority ordering, duration tiebreaking, time budget enforcement (including the zero-budget and exact-fit edge cases), minimum priority filtering, and the handling of `as needed` tasks. This is the core algorithm, so it needed the most thorough coverage.

**Advanced scheduler features (25 tests across 3 groups).** `sort_by_time` tests verify chronological ordering, untimed tasks sort last, and the original list is not mutated. `detect_conflicts` tests verify warnings are generated for shared time slots, contain the conflicting task names, and are not generated for tasks without a time value. `filter_tasks` tests verify filtering by pet name, by status, and by both simultaneously, including the empty-input and no-match cases.

These tests matter because each one targets a distinct code path. A test that only checks the happy path gives false confidence; the edge-case tests — zero budget, unknown pet name, three tasks in the same slot — are the ones most likely to expose a real off-by-one or missing guard.

**b. Confidence**

Confidence in the scheduler's correctness is high for the behaviors directly covered by tests. The 49 tests exercise every public method and the most likely failure modes.

The main gap is **integration between `mark_task_complete()` and `build_plan()`**: there are no tests that call `mark_task_complete()` and then immediately call `build_plan()` to verify the completed task no longer appears in the plan. The unit tests verify each method in isolation, but the chain of state changes that happens in a real user session — add tasks, generate plan, mark one complete, regenerate plan — is not tested end-to-end.

If there were more time, the next tests to write would be:
1. A full-session integration test: build a plan, mark a task complete, rebuild the plan, assert the completed task is absent and its successor is present.
2. A test for `due_today()` when `next_due_date` is in the past (before today), verifying it returns `True`.
3. A test verifying that `filter_tasks` with `status="completed"` returns nothing immediately after `build_plan()` (before any task is marked complete), confirming the initial state assumption that all scheduled tasks start as pending.

---

## 5. Reflection

**a. What went well**

The part of this project most worth pointing to is the test suite. Writing tests for the advanced scheduler features — especially `detect_conflicts` and `filter_tasks` — forced a level of precision that improved the implementation itself. While writing `test_detect_conflicts_tasks_without_time_are_ignored`, I realized the method's docstring said "tasks with no time value are ignored" but the code only skipped them implicitly by not adding them to the `by_time` dictionary. That implicit behavior was correct, but documenting it with a test made the contract explicit. The tests are not just verification; they serve as executable documentation of what each method is supposed to do.

**b. What you would improve**

The `build_plan()` method is doing too much in one place. It filters by recurrence, filters by minimum priority, sorts, and greedily packs tasks into the budget — all in a single loop. If a fifth constraint were added (say, preferred time windows), the method would grow significantly harder to follow. In a next iteration, the filtering and sorting steps would be extracted into separate private methods so the top-level `build_plan()` reads like a policy statement rather than an implementation. This is also a testability improvement: each step could be tested in isolation rather than only through the final output.

**c. Key takeaway**

The most important thing learned about working with AI on this project is that the AI is most useful when you already know what you want and need help producing it — and most risky when you don't. When the design was clear (generate a method that creates the next occurrence of a recurring task), the AI produced a correct first draft quickly. When the design was ambiguous (what exactly should happen when `mark_task_complete()` is called on a task that doesn't belong to any pet?), the AI produced plausible-looking code that had a subtle state inconsistency that a human had to catch.

The practical implication is that the "lead architect" role is not optional when using AI assistance. Deciding what the system should do, at what level of detail, and then verifying that the generated code actually does it — that responsibility cannot be delegated. AI accelerates the implementation of decisions; it does not replace the decisions themselves.
