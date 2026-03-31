import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# --- Section 1: Owner Setup ---
st.subheader("Owner Setup")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available time today (minutes)", min_value=1, max_value=480, value=60)
min_priority = st.selectbox("Minimum task priority", ["low", "medium", "high"], index=0)

if st.button("Save Owner"):
    st.session_state.owner = Owner(owner_name, int(available_minutes), min_priority)
    st.session_state.pets = []
    st.session_state.plan = None
    st.session_state.scheduler = None
    st.success(f"Owner '{owner_name}' saved.")

st.divider()

# --- Section 2: Add Pets ---
st.subheader("Add a Pet")

if st.session_state.owner is None:
    st.info("Save an owner above before adding pets.")
else:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

    if st.button("Add Pet"):
        existing_names = [p.name.lower() for p in st.session_state.pets]
        if pet_name.strip().lower() in existing_names:
            st.error(f"A pet named '{pet_name}' already exists.")
        else:
            pet = Pet(pet_name.strip(), species)
            st.session_state.owner.add_pet(pet)
            st.session_state.pets.append(pet)
            st.session_state.plan = None
            st.success(f"Added {pet_name} the {species}.")

    if st.session_state.pets:
        st.write("**Your pets:**")
        for p in st.session_state.pets:
            st.write(f"- {p.name} ({p.species})")

st.divider()

# --- Section 3: Add Tasks ---
st.subheader("Add a Task")

if not st.session_state.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    pet_names = [p.name for p in st.session_state.pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
    with col5:
        task_time = st.text_input("Start time (HH:MM, optional)", placeholder="e.g. 08:30")

    if st.button("Add Task"):
        selected_pet = next(p for p in st.session_state.pets if p.name == selected_pet_name)
        time_val = task_time.strip() if task_time.strip() else None
        task = Task(task_title, int(duration), priority, frequency, time=time_val)
        try:
            selected_pet.add_task(task)
            st.session_state.plan = None  # invalidate cached plan
            st.success(f"Added '{task_title}' to {selected_pet_name}.")
        except ValueError as e:
            st.error(str(e))

    # Show current tasks sorted by start time using Scheduler.sort_by_time()
    all_task_rows = []
    if st.session_state.pets:
        _sched = Scheduler(st.session_state.owner)
        for p in st.session_state.pets:
            for t in _sched.sort_by_time(p.get_tasks()):
                all_task_rows.append({
                    "pet": p.name,
                    "time": t.time or "—",
                    "title": t.title,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                    "frequency": t.frequency,
                })
    if all_task_rows:
        st.write("**Current tasks (sorted by start time):**")
        st.table(all_task_rows)

st.divider()

# --- Section 4: Generate Schedule ---
st.subheader("Generate Schedule")

if st.button("Generate Schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    elif not st.session_state.pets:
        st.warning("Please add at least one pet.")
    elif not any(p.get_tasks() for p in st.session_state.pets):
        st.warning("Please add at least one task.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        plan = scheduler.build_plan()
        st.session_state.plan = plan
        st.session_state.scheduler = scheduler

if st.session_state.plan is not None:
    plan = st.session_state.plan
    scheduler = st.session_state.scheduler
    scheduled = plan["scheduled"]
    skipped = plan["skipped"]

    # --- Conflict detection ---
    conflicts = scheduler.detect_conflicts(scheduled)
    if conflicts:
        st.write("**Scheduling conflicts detected:**")
        for warning in conflicts:
            st.warning(warning)

    # --- Filters (display only) ---
    pet_options = ["All Pets"] + [p.name for p in st.session_state.pets]
    col_a, col_b = st.columns(2)
    with col_a:
        pet_filter = st.selectbox("Filter by pet", pet_options)
    with col_b:
        status_filter = st.radio("Filter by status", ["All", "Pending", "Completed"], horizontal=True)

    # Delegate filtering to Scheduler.filter_tasks()
    pet_name_arg = None if pet_filter == "All Pets" else pet_filter
    status_arg = None if status_filter == "All" else status_filter.lower()
    filtered = scheduler.filter_tasks(scheduled, pet_name=pet_name_arg, status=status_arg)

    # Display scheduled tasks
    if filtered:
        for i, item in enumerate(filtered, start=1):
            task = item["task"]
            time_label = f" · {task.time}" if task.time else ""
            st.markdown(f"**{i}. {task.title}** — {item['pet']}{time_label}")
            st.caption(
                f"{task.duration_minutes} min · {task.priority} priority · "
                f"{task.frequency} · {item['reason']}"
            )
    else:
        st.info("No tasks match the current filters.")

    # Display skipped tasks
    if skipped:
        with st.expander(f"Skipped tasks ({len(skipped)})"):
            for item in skipped:
                st.write(f"- **{item['task'].title}** ({item['pet']}): {item['reason']}")
