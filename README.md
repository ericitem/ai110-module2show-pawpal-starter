# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The scheduler goes beyond a basic priority filter with four algorithmic improvements:

**Recurring task logic**: Tasks carry a `frequency` (`daily`, `weekly`, `as needed`) and a `last_completed_date`. The `due_today()` method uses these to decide whether a task should appear in today's plan: daily tasks reappear the next day, weekly tasks reappear after 7 days, and `as needed` tasks are never auto-scheduled. When a task is marked complete, `mark_task_complete()` automatically creates the next occurrence using `timedelta` and replaces the old task in the pet's list.

**Conflict detection**: `detect_conflicts()` scans the scheduled plan for tasks sharing the same start time (`HH:MM`) across any pet. Rather than raising an error, it returns a list of human-readable warning strings so the owner can resolve conflicts without the app crashing.

**Time-based sorting**: `sort_by_time()` uses Python's `sorted()` with a lambda key to order tasks chronologically. Zero-padded `"HH:MM"` strings sort correctly as plain strings, so no time parsing is needed. Tasks without a start time are pushed to the end using the sentinel value `"99:99"`.

**Pet and status filtering**: `filter_tasks()` accepts an optional pet name and/or status (`"pending"` / `"completed"`) and returns a filtered view of the scheduled plan. Filtering is display-only: it never re-runs the scheduler or changes any task state.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
