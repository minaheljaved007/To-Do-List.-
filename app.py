"""
app.py
Streamlit UI for the To-Do List application.
Run locally with: streamlit run app.py
"""

import streamlit as st
from datetime import date, datetime
from task_manager import TaskManager, VALID_PRIORITIES

# ---------- Page config ----------
st.set_page_config(
    page_title="To-Do List",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------- Init ----------
@st.cache_resource
def get_task_manager():
    return TaskManager()

try:
    tm = get_task_manager()
except RuntimeError as e:
    st.title("✅ To-Do List")
    st.error(
        "**Setup required:** could not connect to the database.\n\n"
        f"{e}"
    )
    st.info(
        "**Local development:** create a `.env` file or export "
        "`SUPABASE_URL` and `SUPABASE_KEY` in your terminal before running "
        "`streamlit run app.py`.\n\n"
        "**Streamlit Community Cloud:** add these as secrets in your app's "
        "settings (⚙️ Settings → Secrets)."
    )
    st.stop()

try:
    _connection_check = tm.get_stats()
except Exception as e:
    st.title("✅ To-Do List")
    st.error(
        "**Could not reach the database.** This usually means the "
        "SUPABASE_URL or SUPABASE_KEY is incorrect, or the `tasks` table "
        "hasn't been created yet (run schema.sql in the Supabase SQL Editor)."
    )
    st.caption(f"Technical details: {e}")
    st.stop()

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

PRIORITY_COLORS = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
    .task-card {
        padding: 0.6rem 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.4rem;
        border: 1px solid rgba(128,128,128,0.25);
    }
    .overdue-badge {
        color: #d33;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .stButton>button {
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar: Add Task + Stats ----------
with st.sidebar:
    st.header("➕ Add New Task")

    with st.form("add_task_form", clear_on_submit=True):
        new_text = st.text_input("Task description", placeholder="e.g. Finish project report")
        col1, col2 = st.columns(2)
        with col1:
            new_priority = st.selectbox("Priority", VALID_PRIORITIES, index=1)
        with col2:
            new_category = st.text_input("Category", value="General")
        new_due = st.date_input("Due date (optional)", value=None)
        submitted = st.form_submit_button("Add Task", use_container_width=True, type="primary")

        if submitted:
            error = TaskManager.validate_task_text(new_text)
            if error:
                st.error(error)
            else:
                due_str = new_due.isoformat() if isinstance(new_due, date) else None
                tm.add_task(new_text, priority=new_priority, due_date=due_str, category=new_category)
                st.success(f"Added: {new_text}")
                st.rerun()

    st.divider()
    st.header("📊 Stats")
    stats = tm.get_stats()
    c1, c2 = st.columns(2)
    c1.metric("Total", stats["total"])
    c2.metric("Active", stats["active"])
    c3, c4 = st.columns(2)
    c3.metric("Completed", stats["completed"])
    c4.metric("Overdue", stats["overdue"], delta_color="inverse")
    st.progress(stats["completion_rate"] / 100 if stats["total"] else 0)
    st.caption(f"{stats['completion_rate']}% complete")

    st.divider()
    st.header("🗑️ Bulk Actions")
    if st.button("Delete completed tasks", use_container_width=True):
        n = tm.delete_completed()
        st.toast(f"Deleted {n} completed task(s).")
        st.rerun()

    if not st.session_state.confirm_clear:
        if st.button("Clear ALL tasks", use_container_width=True):
            st.session_state.confirm_clear = True
            st.rerun()
    else:
        st.warning("Are you sure? This cannot be undone.")
        cc1, cc2 = st.columns(2)
        if cc1.button("Yes, clear", use_container_width=True, type="primary"):
            n = tm.clear_all()
            st.session_state.confirm_clear = False
            st.toast(f"Cleared {n} task(s).")
            st.rerun()
        if cc2.button("Cancel", use_container_width=True):
            st.session_state.confirm_clear = False
            st.rerun()

# ---------- Main area ----------
st.title("✅ To-Do List")

# Filters
fcol1, fcol2, fcol3, fcol4 = st.columns([1, 1, 1, 1.4])
with fcol1:
    status_filter = st.selectbox("Status", ["All", "Active", "Completed"])
with fcol2:
    priority_filter = st.selectbox("Priority", ["All"] + VALID_PRIORITIES)
with fcol3:
    categories = ["All"] + tm.get_categories()
    category_filter = st.selectbox("Category", categories)
with fcol4:
    search_query = st.text_input("Search", placeholder="Search tasks...")

sort_option = st.radio(
    "Sort by", ["Created (newest)", "Priority", "Due date"], horizontal=True
)

tasks = tm.filter_tasks(
    status=status_filter, priority=priority_filter, category=category_filter, search=search_query
)

# Sorting
if sort_option == "Priority":
    tasks.sort(key=lambda t: PRIORITY_ORDER.get(t["priority"], 1))
elif sort_option == "Due date":
    tasks.sort(key=lambda t: (t["due_date"] is None, t["due_date"] or ""))
else:
    tasks.sort(key=lambda t: t["created_at"], reverse=True)

st.divider()

if not tasks:
    st.info("No tasks found. Add one from the sidebar, or adjust your filters. 🎉")
else:
    for task in tasks:
        is_editing = st.session_state.edit_task_id == task["id"]

        with st.container():
            if is_editing:
                with st.form(f"edit_form_{task['id']}"):
                    edit_text = st.text_input("Task", value=task["text"])
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        edit_priority = st.selectbox(
                            "Priority", VALID_PRIORITIES,
                            index=VALID_PRIORITIES.index(task["priority"]),
                        )
                    with ecol2:
                        edit_category = st.text_input("Category", value=task["category"])
                    existing_due = (
                        datetime.fromisoformat(task["due_date"]).date()
                        if task["due_date"] else None
                    )
                    edit_due = st.date_input("Due date", value=existing_due)

                    save_col, cancel_col = st.columns(2)
                    save = save_col.form_submit_button("💾 Save", use_container_width=True, type="primary")
                    cancel = cancel_col.form_submit_button("✖ Cancel", use_container_width=True)

                    if save:
                        error = TaskManager.validate_task_text(edit_text)
                        if error:
                            st.error(error)
                        else:
                            due_str = edit_due.isoformat() if isinstance(edit_due, date) else None
                            tm.update_task(
                                task["id"],
                                text=edit_text,
                                priority=edit_priority,
                                category=edit_category,
                                due_date=due_str,
                            )
                            st.session_state.edit_task_id = None
                            st.rerun()
                    if cancel:
                        st.session_state.edit_task_id = None
                        st.rerun()
            else:
                row = st.columns([0.5, 5, 1, 1, 1])
                checked = row[0].checkbox(
                    f"Mark '{task['text']}' as complete",
                    value=task["completed"],
                    key=f"chk_{task['id']}",
                    label_visibility="collapsed",
                )
                if checked != task["completed"]:
                    tm.toggle_complete(task["id"])
                    st.rerun()

                label = task["text"]
                if task["completed"]:
                    label = f"~~{label}~~"
                overdue = tm.is_overdue(task)
                meta = f"{PRIORITY_COLORS.get(task['priority'], '')} {task['priority']} · 🏷️ {task['category']}"
                if task["due_date"]:
                    meta += f" · 📅 {task['due_date']}"
                    if overdue:
                        meta += "  **OVERDUE**"
                row[1].markdown(f"**{label}**  \n<small>{meta}</small>", unsafe_allow_html=True)

                if row[2].button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                    st.session_state.edit_task_id = task["id"]
                    st.rerun()
                if row[3].button("🗑️", key=f"del_{task['id']}", help="Delete task"):
                    tm.delete_task(task["id"])
                    st.rerun()
                row[4].write("")

        st.divider()

st.caption("Built with Streamlit · Data persisted locally in data/tasks.json")
