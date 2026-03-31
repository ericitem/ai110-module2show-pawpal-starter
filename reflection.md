# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+ are:

1. **Set up their pet profile** — The user enters basic information about themselves and their pet, including the owner's name, the pet's name, and the species. This profile provides the context the scheduler needs to personalize the plan.

2. **Add care tasks** — The user defines individual care tasks for their pet, such as a morning walk, feeding, medication, or grooming. Each task has a title, an estimated duration in minutes, and a priority level (low, medium, or high) so the scheduler knows how to weigh it.

3. **Generate and view the daily schedule** — The user triggers the scheduler to produce an ordered, time-aware plan for the day. The schedule selects and sequences tasks based on priority and available time, and explains why each task was included and when it is scheduled.

The initial UML design consists of four classes: Owner, Pet, Task, and Scheduler.

**Owner** holds the constraints that govern the schedule — the owner's name, how many minutes they have available today, and the minimum priority level they care about. It has no behavior beyond storing that data.

**Pet** represents the animal being cared for. It stores the pet's name and species, and holds a reference back to its Owner so the scheduler knows whose constraints apply.

**Task** represents a single care activity. It stores the task title, how long it takes in minutes, and its priority (low, medium, or high). It has one method, `priority_rank()`, which converts the priority string into a number (1, 2, or 3) so tasks can be sorted.

**Scheduler** is the coordinator. It holds an Owner, a Pet, and a list of Tasks. Its `add_task()` method adds tasks to the candidate list. Its `build_plan()` method applies the owner's constraints — filtering out tasks below the minimum priority, sorting the rest by priority, and greedily filling up to the available time budget. Its `explain_plan()` method formats the resulting plan as human-readable text for display in the UI.

**b. Design changes**

Two changes were made after reviewing the initial skeleton.

**1. `Task.priority_rank()` now raises a `ValueError` for invalid input.**
The original design had `priority_rank()` return `0` silently if an unrecognized priority string was passed. This would cause a task to be quietly excluded from every plan with no indication of why. The fix raises a `ValueError` with a descriptive message so the problem is immediately visible instead of producing a hard-to-trace bug.

**2. `Scheduler` gained a `clear_tasks()` method.**
The initial design had no way to reset the task list once tasks were added. In a Streamlit app where the user can click "Generate schedule" multiple times, the same tasks would be re-added on each run and pile up in the list. Adding `clear_tasks()` lets the UI wipe the list before re-adding tasks, keeping each schedule generation clean and independent.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
