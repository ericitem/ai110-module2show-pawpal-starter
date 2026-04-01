# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan daily care tasks for one or more pets. The owner sets a time budget and minimum priority level; the scheduler selects, orders, and explains each task automatically.

## Features

### Core Workflow
- Enter owner info (name, available time, minimum priority)
- Add multiple pets (name, species)
- Add tasks per pet (title, duration, priority, frequency, optional start time)
- Generate a prioritized daily schedule with explanations

### Smarter Scheduling

**Priority-based scheduling with greedy time packing**
Tasks are sorted by priority (high → medium → low), then by duration (shorter first) when priorities tie. The scheduler greedily fills the owner's time budget, skipping any task that would overflow it.

**Recurring task logic**
Each task carries a `frequency` (`daily`, `weekly`, `as needed`) and a `last_completed_date`. `due_today()` uses these to decide whether a task belongs in today's plan. When a task is marked complete, the scheduler automatically creates the next occurrence using `timedelta` and replaces the old task.

**Conflict detection**
`detect_conflicts()` scans the scheduled plan for tasks sharing the same start time across any pet and returns human-readable warnings. The UI surfaces these as highlighted alerts so the owner can resolve double-bookings at a glance.

**Time-based sorting**
`sort_by_time()` orders tasks chronologically using zero-padded `"HH:MM"` strings. Tasks without a start time are pushed to the end. The task list in the UI is always displayed in this sorted order.

**Pet and status filtering**
`filter_tasks()` accepts an optional pet name and/or status (`pending` / `completed`) and returns a filtered view of the scheduled plan without re-running the scheduler or changing any task state.

**Urgency scoring**
`build_plan_by_urgency()` replaces the plain priority sort with a composite urgency score: `priority_rank × 10 + days_overdue`. This promotes tasks that are falling behind their recurrence schedule — a medium-priority grooming session that is 14 days overdue scores 34, beating a high-priority walk that was completed yesterday (score 30). Toggle urgency mode on in the sidebar to use it. See [AI-assisted development note](#ai-assisted-development-note) below for how this algorithm was designed collaboratively.

### Data Persistence

`Owner.save_to_json(path)` serializes the full owner → pets → tasks tree to a JSON file. `Owner.load_from_json(path)` reconstructs the complete object graph, including ISO-format dates for `last_completed_date` and `next_due_date`. The Streamlit app auto-loads `data.json` on startup and auto-saves whenever a fresh schedule is generated.

### Professional UI

- **Priority badges:** 🔴 High · 🟡 Medium · 🟢 Low displayed on every task
- **Task-type emoji:** titles containing keywords like "walk", "medication", "groom" are automatically decorated (🚶 💊 ✂️ 🎾 🏥 …)
- **Budget progress bar:** shows minutes used vs. available at a glance
- **Species emoji:** 🐶 🐱 🐰 🐦 in the pets list
- **Conflict warnings:** `⚠️` banners for double-booked time slots

## AI-Assisted Development Note

The urgency scoring feature (`build_plan_by_urgency`) illustrates the difference between AI as a code generator and AI as a design collaborator.

An open-ended prompt ("add a smarter scheduling mode") produced a suggestion that simply multiplied priority by a constant — essentially the same as the existing sort, producing identical orderings in all realistic cases.

A constrained, spec-driven prompt produced the composite score approach:

> *"Design a scheduling key that combines static priority with a dynamic component that grows as a task falls behind its recurrence schedule. The key should be a float so tasks on time and tasks one day overdue have distinct scores. Daily tasks should age at rate 1 point/day, weekly tasks at 1 point/day past their 7-day window."*

This prompt was written after identifying the specific limitation: a high-priority task completed every day was always ranked above a medium-priority task that kept being pushed out. The composite score is the solution to that stated problem. Writing the problem statement first — before asking the AI for code — is what made the AI's output immediately useful rather than requiring a full redesign.

## 📸 Demo

![PawPal+ screenshot](docs/screenshot.png)

> _Add a screenshot by saving it to `docs/screenshot.png` and committing it._

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the tests

```bash
pytest
```

## Project Structure

```
pawpal_system.py   # Backend: Task, Pet, Owner, Scheduler classes
app.py             # Frontend: Streamlit UI
main.py            # Terminal demo of all scheduler features
tests/
  test_pawpal.py   # 61 unit tests covering all scheduler behaviors
class-diagram.md   # Mermaid.js UML diagram
reflection.md      # Design decisions and project reflection
```

## System Design

See [`class-diagram.md`](class-diagram.md) for the full UML class diagram.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
