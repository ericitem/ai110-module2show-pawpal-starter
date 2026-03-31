from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner
owner = Owner(name="Jordan", available_minutes=120, min_priority="low")

# Create two pets and assign them to the owner
mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")
owner.add_pet(mochi)
owner.add_pet(luna)

# Add tasks OUT OF ORDER by time to demonstrate sorting.
# Deliberate conflict: Mochi's "Feeding" and Luna's "Medication" both at 08:00.
mochi.add_task(Task("Evening walk",   duration_minutes=20, priority="medium", frequency="daily", time="18:00"))
mochi.add_task(Task("Morning walk",   duration_minutes=20, priority="high",   frequency="daily", time="07:30"))
mochi.add_task(Task("Grooming",       duration_minutes=30, priority="medium", frequency="weekly"))        # no time
mochi.add_task(Task("Afternoon play", duration_minutes=15, priority="low",    frequency="daily", time="14:00"))
mochi.add_task(Task("Feeding",        duration_minutes=10, priority="high",   frequency="daily", time="08:00"))

luna.add_task(Task("Litter cleaning", duration_minutes=10, priority="medium", frequency="daily", time="09:00"))
luna.add_task(Task("Medication",      duration_minutes=5,  priority="high",   frequency="daily", time="08:00"))  # same as Feeding
luna.add_task(Task("Enrichment play", duration_minutes=15, priority="low",    frequency="daily", time="16:00"))

# Build schedule
scheduler = Scheduler(owner)
plan = scheduler.build_plan()

print("=" * 40)
print("        TODAY'S SCHEDULE")
print("=" * 40)
print(scheduler.explain_plan(plan))

# --- Demo: detect_conflicts ---
print("=" * 40)
print("  CONFLICT DETECTION")
print("=" * 40)
conflicts = scheduler.detect_conflicts(plan["scheduled"])
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")
print()

# --- Demo: sort_by_time ---
print("=" * 40)
print("  MOCHI'S TASKS SORTED BY TIME")
print("=" * 40)
sorted_mochi = scheduler.sort_by_time(mochi.get_tasks())
for task in sorted_mochi:
    time_label = task.time if task.time else "no time set"
    print(f"  {time_label}  {task.title} ({task.duration_minutes} min, {task.priority})")

print()

# --- Demo: filter_tasks by pet name ---
print("=" * 40)
print("  SCHEDULED TASKS FOR LUNA ONLY")
print("=" * 40)
luna_tasks = scheduler.filter_tasks(plan["scheduled"], pet_name="Luna")
if luna_tasks:
    for item in luna_tasks:
        task = item["task"]
        print(f"  {task.time}  {task.title} ({task.duration_minutes} min)")
else:
    print("  No scheduled tasks for Luna.")

print()

# --- Demo: filter_tasks by status ---
print("=" * 40)
print("  PENDING TASKS (not yet completed)")
print("=" * 40)
pending = scheduler.filter_tasks(plan["scheduled"], status="pending")
for item in pending:
    task = item["task"]
    label = task.time if task.time else "no time"
    print(f"  {label}  {task.title} ({item['pet']})")

print()
print(f"  Total pending: {len(pending)}")
print("=" * 40)
