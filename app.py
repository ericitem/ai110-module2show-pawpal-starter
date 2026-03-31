import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = []

# --- Section 1: Owner Setup ---
st.subheader("Owner Setup")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available time today (minutes)", min_value=1, max_value=480, value=60)
min_priority = st.selectbox("Minimum task priority", ["low", "medium", "high"], index=0)

if st.button("Save Owner"):
    st.session_state.owner = Owner(owner_name, int(available_minutes), min_priority)
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
        pet = Pet(pet_name, species)
        st.session_state.owner.add_pet(pet)
        st.session_state.pets.append(pet)
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])

    if st.button("Add Task"):
        selected_pet = next(p for p in st.session_state.pets if p.name == selected_pet_name)
        task = Task(task_title, int(duration), priority, frequency)
        try:
            selected_pet.add_task(task)
            st.success(f"Added '{task_title}' to {selected_pet_name}.")
        except ValueError as e:
            st.error(str(e))

    # Derive task table from pets directly (single source of truth)
    all_task_rows = []
    for p in st.session_state.pets:
        for t in p.get_tasks():
            all_task_rows.append({
                "pet": p.name,
                "title": t.title,
                "duration": t.duration_minutes,
                "priority": t.priority,
                "frequency": t.frequency,
            })
    if all_task_rows:
        st.write("**Current tasks:**")
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

if "plan" in st.session_state and st.session_state.plan is not None:
    plan = st.session_state.plan
    scheduled = plan["scheduled"]
    skipped = plan["skipped"]

    # --- Filters (display only) ---
    pet_options = ["All Pets"] + [p.name for p in st.session_state.pets]
    col_a, col_b = st.columns(2)
    with col_a:
        pet_filter = st.selectbox("Filter by pet", pet_options)
    with col_b:
        status_filter = st.radio("Filter by status", ["All", "Pending", "Completed"], horizontal=True)

    # Apply filters
    filtered = scheduled
    if pet_filter != "All Pets":
        filtered = [item for item in filtered if item["pet"] == pet_filter]
    if status_filter == "Pending":
        filtered = [item for item in filtered if item["task"].due_today()]
    elif status_filter == "Completed":
        filtered = [item for item in filtered if not item["task"].due_today()]

    # Display scheduled tasks
    if filtered:
        for i, item in enumerate(filtered, start=1):
            task = item["task"]
            st.markdown(f"**{i}. {task.title}** — {item['pet']}")
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
