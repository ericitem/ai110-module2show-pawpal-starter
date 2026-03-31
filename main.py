from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner
owner = Owner(name="Jordan", available_minutes=90, min_priority="low")

# Create two pets and assign them to the owner
mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")
owner.add_pet(mochi)
owner.add_pet(luna)

# Add tasks to Mochi
mochi.add_task(Task("Morning walk",    duration_minutes=20, priority="high",   frequency="daily"))
mochi.add_task(Task("Feeding",         duration_minutes=10, priority="high",   frequency="daily"))
mochi.add_task(Task("Grooming",        duration_minutes=30, priority="medium", frequency="weekly"))

# Add tasks to Luna
luna.add_task(Task("Medication",       duration_minutes=5,  priority="high",   frequency="daily"))
luna.add_task(Task("Litter cleaning",  duration_minutes=10, priority="medium", frequency="daily"))
luna.add_task(Task("Enrichment play",  duration_minutes=15, priority="low",    frequency="daily"))

# Build and print today's schedule
scheduler = Scheduler(owner)
plan = scheduler.build_plan()

print("=" * 40)
print("        TODAY'S SCHEDULE")
print("=" * 40)
print(scheduler.explain_plan(plan))
print("=" * 40)
