"""
task_manager.py
Core business logic for the To-Do List app, backed by Supabase (Postgres).

Same public interface as the local JSON version, so app.py does not need
to change. Requires SUPABASE_URL and SUPABASE_KEY to be set, either as
environment variables or in Streamlit secrets (st.secrets).
"""

import os
from datetime import date
from typing import List, Dict, Optional

from supabase import create_client, Client

VALID_PRIORITIES = ["Low", "Medium", "High"]
TABLE = "tasks"


def _get_credentials():
    """
    Reads Supabase credentials from Streamlit secrets first (for cloud
    deployment), falling back to environment variables (for local dev).
    """
    url = None
    key = None
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

    url = url or os.environ.get("SUPABASE_URL")
    key = key or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY "
            "as environment variables (local) or in .streamlit/secrets.toml (cloud)."
        )
    return url, key


class TaskManager:
    """Handles all CRUD operations against the Supabase 'tasks' table."""

    def __init__(self, client: Optional[Client] = None):
        if client is not None:
            self.client = client
        else:
            url, key = _get_credentials()
            self.client = create_client(url, key)

    # ---------- validation ----------
    @staticmethod
    def validate_task_text(text: str) -> Optional[str]:
        if text is None or not text.strip():
            return "Task description cannot be empty."
        if len(text.strip()) > 200:
            return "Task description must be under 200 characters."
        return None

    # ---------- CRUD ----------
    def add_task(
        self,
        text: str,
        priority: str = "Medium",
        due_date: Optional[str] = None,
        category: str = "General",
    ) -> Dict:
        error = self.validate_task_text(text)
        if error:
            raise ValueError(error)
        if priority not in VALID_PRIORITIES:
            priority = "Medium"

        payload = {
            "text": text.strip(),
            "completed": False,
            "priority": priority,
            "category": category.strip() if category else "General",
            "due_date": due_date,
        }
        result = self.client.table(TABLE).insert(payload).execute()
        return result.data[0]

    def get_all_tasks(self) -> List[Dict]:
        result = self.client.table(TABLE).select("*").order("created_at", desc=True).execute()
        return result.data

    def get_task(self, task_id: str) -> Optional[Dict]:
        result = self.client.table(TABLE).select("*").eq("id", task_id).execute()
        return result.data[0] if result.data else None

    def update_task(self, task_id: str, **fields) -> bool:
        update_payload = {}
        if "text" in fields:
            error = self.validate_task_text(fields["text"])
            if error:
                raise ValueError(error)
            update_payload["text"] = fields["text"].strip()
        if "priority" in fields and fields["priority"] in VALID_PRIORITIES:
            update_payload["priority"] = fields["priority"]
        if "category" in fields:
            update_payload["category"] = fields["category"].strip() or "General"
        if "due_date" in fields:
            update_payload["due_date"] = fields["due_date"]

        if not update_payload:
            return False

        result = self.client.table(TABLE).update(update_payload).eq("id", task_id).execute()
        return len(result.data) > 0

    def toggle_complete(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        new_completed = not task["completed"]
        payload = {
            "completed": new_completed,
            "completed_at": _now_iso() if new_completed else None,
        }
        result = self.client.table(TABLE).update(payload).eq("id", task_id).execute()
        return len(result.data) > 0

    def delete_task(self, task_id: str) -> bool:
        result = self.client.table(TABLE).delete().eq("id", task_id).execute()
        return len(result.data) > 0

    def delete_completed(self) -> int:
        result = self.client.table(TABLE).delete().eq("completed", True).execute()
        return len(result.data)

    def clear_all(self) -> int:
        all_tasks = self.get_all_tasks()
        count = len(all_tasks)
        if count:
            self.client.table(TABLE).delete().neq(
                "id", "00000000-0000-0000-0000-000000000000"
            ).execute()
        return count

    # ---------- filtering / stats ----------
    def filter_tasks(
        self,
        status: str = "All",
        priority: str = "All",
        category: str = "All",
        search: str = "",
    ) -> List[Dict]:
        query = self.client.table(TABLE).select("*")

        if status == "Active":
            query = query.eq("completed", False)
        elif status == "Completed":
            query = query.eq("completed", True)

        if priority != "All":
            query = query.eq("priority", priority)

        if category != "All":
            query = query.eq("category", category)

        if search:
            query = query.ilike("text", f"%{search}%")

        result = query.order("created_at", desc=True).execute()
        return result.data

    def get_categories(self) -> List[str]:
        result = self.client.table(TABLE).select("category").execute()
        cats = sorted(set(row["category"] for row in result.data))
        return cats

    def get_stats(self) -> Dict:
        tasks = self.get_all_tasks()
        total = len(tasks)
        completed = sum(1 for t in tasks if t["completed"])
        active = total - completed
        today = date.today().isoformat()
        overdue = sum(
            1 for t in tasks
            if not t["completed"] and t["due_date"] and t["due_date"] < today
        )
        return {
            "total": total,
            "completed": completed,
            "active": active,
            "overdue": overdue,
            "completion_rate": round((completed / total * 100), 1) if total else 0.0,
        }

    def is_overdue(self, task: Dict) -> bool:
        if task["completed"] or not task["due_date"]:
            return False
        return task["due_date"] < date.today().isoformat()


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
