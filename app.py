import streamlit as st
from pathlib import Path
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

DATA_FILE = "data.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PRIORITY_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

TASK_EMOJI = {
    "walk": "🚶",
    "feed": "🍽️",
    "food": "🍽️",
    "medication": "💊",
    "medicine": "💊",
    "med": "💊",
    "groom": "✂️",
    "play": "🎾",
    "litter": "🪣",
    "vet": "🏥",
    "bath": "🛁",
    "brush": "🪮",
    "train": "🎓",
    "nap": "😴",
    "sleep": "😴",
}


def task_emoji(title: str) -> str:
    lower = title.lower()
    for keyword, emoji in TASK_EMOJI.items():
        if keyword in lower:
            return emoji
    return "📋"


def render_task_card(i: int, item: dict) -> None:
    """Render a single scheduled task as a structured card."""
    task = item["task"]
    badge = PRIORITY_BADGE.get(task.priority, task.priority)
    icon = task_emoji(task.title)
    time_label = f" · ⏰ {task.time}" if task.time else ""
    status_icon = "✅" if task.completed else "⏳"

    st.markdown(
        f"**{status_icon} {i}. {icon} {task.title}** — *{item['pet']}*{time_label}"
    )
    col1, col2, col3 = st.columns(3)
    col1.caption(f"{badge}")
    col2.caption(f"⏱ {task.duration_minutes} min")
    col3.caption(f"🔁 {task.frequency}")
    st.caption(f"↳ {item['reason']}")
    st.markdown("---")


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# ---------------------------------------------------------------------------
# Auto-load saved data on first run
# ---------------------------------------------------------------------------

if not st.session_state.data_loaded:
    if Path(DATA_FILE).exists():
        try:
            loaded_owner = Owner.load_from_json(DATA_FILE)
            st.session_state.owner = loaded_owner
            st.session_state.pets = loaded_owner.pets
            st.session_state.data_loaded = True
            st.toast(f"Loaded saved data for {loaded_owner.name}.", icon="💾")
        except Exception as e:
            st.warning(f"Could not load saved data: {e}")
    else:
        st.session_state.data_loaded = True

# ---------------------------------------------------------------------------
# Sidebar — persistence controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("💾 Data")
    if st.session_state.owner is not None:
        if st.button("Save data", use_container_width=True):
            st.session_state.owner.save_to_json(DATA_FILE)
            st.success("Saved.")
    if Path(DATA_FILE).exists():
        if st.button("Clear saved data", use_container_width=True):
            Path(DATA_FILE).unlink()
            st.session_state.owner = None
            st.session_state.pets = []
            st.session_state.plan = None
            st.session_state.scheduler = None
            st.rerun()

    st.divider()
    st.header("⚙️ Schedule Mode")
    urgency_mode = st.toggle(
        "Urgency mode",
        help="Urgency mode promotes overdue tasks above same-priority tasks that are on schedule.",
    )

# ---------------------------------------------------------------------------
# Section 1: Owner Setup
# ---------------------------------------------------------------------------

st.subheader("1 · Owner Setup")

default_name = st.session_state.owner.name if st.session_state.owner else "Jordan"
default_minutes = st.session_state.owner.available_minutes if st.session_state.owner else 60
default_priority_idx = ["low", "medium", "high"].index(
    st.session_state.owner.min_priority if st.session_state.owner else "low"
)

owner_name = st.text_input("Owner name", value=default_name)
available_minutes = st.number_input(
    "Available time today (minutes)", min_value=1, max_value=480, value=default_minutes
)
min_priority = st.selectbox(
    "Minimum task priority", ["low", "medium", "high"], index=default_priority_idx
)

if st.button("Save Owner"):
    st.session_state.owner = Owner(owner_name, int(available_minutes), min_priority)
    # Carry existing pets over to the updated owner object.
    for p in st.session_state.pets:
        st.session_state.owner.add_pet(p)
    st.session_state.plan = None
    st.session_state.scheduler = None
    st.success(f"Owner '{owner_name}' saved.")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add Pets
# ---------------------------------------------------------------------------

st.subheader("2 · Pets")

if st.session_state.owner is None:
    st.info("Save an owner above before adding pets.")
else:
    col_pname, col_species = st.columns(2)
    with col_pname:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col_species:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])

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
        species_emoji = {"dog": "🐶", "cat": "🐱", "rabbit": "🐰", "bird": "🐦", "other": "🐾"}
        for p in st.session_state.pets:
            icon = species_emoji.get(p.species, "🐾")
            st.write(f"{icon} **{p.name}** ({p.species}) — {len(p.get_tasks())} task(s)")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Add Tasks
# ---------------------------------------------------------------------------

st.subheader("3 · Tasks")

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
        priority = st.selectbox(
            "Priority",
            ["low", "medium", "high"],
            index=2,
            format_func=lambda p: PRIORITY_BADGE[p],
        )

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
            st.session_state.plan = None
            st.success(f"Added '{task_title}' to {selected_pet_name}.")
        except ValueError as e:
            st.error(str(e))

    # Show all tasks sorted by start time via Scheduler.sort_by_time()
    all_task_rows = []
    if st.session_state.owner and st.session_state.pets:
        _sched = Scheduler(st.session_state.owner)
        for p in st.session_state.pets:
            for t in _sched.sort_by_time(p.get_tasks()):
                all_task_rows.append({
                    "pet": p.name,
                    "time": t.time or "—",
                    "task": f"{task_emoji(t.title)} {t.title}",
                    "duration (min)": t.duration_minutes,
                    "priority": PRIORITY_BADGE.get(t.priority, t.priority),
                    "frequency": t.frequency,
                })
    if all_task_rows:
        st.write("**All tasks (sorted by start time):**")
        st.table(all_task_rows)

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate Schedule
# ---------------------------------------------------------------------------

st.subheader("4 · Today's Schedule")

if st.button("Generate Schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    elif not st.session_state.pets:
        st.warning("Please add at least one pet.")
    elif not any(p.get_tasks() for p in st.session_state.pets):
        st.warning("Please add at least one task.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        plan = (
            scheduler.build_plan_by_urgency() if urgency_mode else scheduler.build_plan()
        )
        st.session_state.plan = plan
        st.session_state.scheduler = scheduler
        # Auto-save whenever a fresh plan is generated.
        st.session_state.owner.save_to_json(DATA_FILE)

if st.session_state.plan is not None:
    plan = st.session_state.plan
    scheduler = st.session_state.scheduler
    scheduled = plan["scheduled"]
    skipped = plan["skipped"]

    # --- Budget progress bar ---
    if scheduled:
        used = scheduled[-1]["cumulative_minutes"]
        budget = st.session_state.owner.available_minutes
        pct = min(used / budget, 1.0)
        st.caption(f"⏱ Time budget: **{used} / {budget} min used**")
        st.progress(pct)

    # --- Conflict detection ---
    conflicts = scheduler.detect_conflicts(scheduled)
    if conflicts:
        st.write("**⚠️ Scheduling conflicts detected:**")
        for warning in conflicts:
            st.warning(warning)

    # --- Filters ---
    pet_options = ["All Pets"] + [p.name for p in st.session_state.pets]
    col_a, col_b = st.columns(2)
    with col_a:
        pet_filter = st.selectbox("Filter by pet", pet_options)
    with col_b:
        status_filter = st.radio(
            "Filter by status", ["All", "Pending", "Completed"], horizontal=True
        )

    pet_name_arg = None if pet_filter == "All Pets" else pet_filter
    status_arg = None if status_filter == "All" else status_filter.lower()
    filtered = scheduler.filter_tasks(scheduled, pet_name=pet_name_arg, status=status_arg)

    # --- Scheduled task cards ---
    if filtered:
        for i, item in enumerate(filtered, start=1):
            render_task_card(i, item)
    else:
        st.info("No tasks match the current filters.")

    # --- Skipped tasks ---
    if skipped:
        with st.expander(f"Skipped tasks ({len(skipped)})"):
            for item in skipped:
                badge = PRIORITY_BADGE.get(item["task"].priority, item["task"].priority)
                icon = task_emoji(item["task"].title)
                st.write(
                    f"- {icon} **{item['task'].title}** ({item['pet']}) · {badge} · "
                    f"_{item['reason']}_"
                )
