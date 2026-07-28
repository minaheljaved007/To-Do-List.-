"""
test_task_manager.py
Tests for the Supabase-backed TaskManager, using a mock Supabase client
so the query-building logic can be verified without a real database.

Run with: pytest test_task_manager.py -v
"""

import pytest
from unittest.mock import MagicMock
from task_manager import TaskManager


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    """Mimics the Supabase query builder's chainable, fluent interface."""

    def __init__(self, table_data, table_name):
        self._table_data = table_data
        self._table_name = table_name
        self._filters = []
        self._op = "select"
        self._payload = None

    def select(self, *args, **kwargs):
        self._op = "select"
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def delete(self):
        self._op = "delete"
        return self

    def eq(self, field, value):
        self._filters.append(("eq", field, value))
        return self

    def neq(self, field, value):
        self._filters.append(("neq", field, value))
        return self

    def ilike(self, field, pattern):
        self._filters.append(("ilike", field, pattern))
        return self

    def order(self, field, desc=False):
        self._filters.append(("order", field, desc))
        return self

    def _apply_filters(self, rows):
        for op, field, value in self._filters:
            if op == "eq":
                rows = [r for r in rows if r.get(field) == value]
            elif op == "neq":
                rows = [r for r in rows if r.get(field) != value]
            elif op == "ilike":
                needle = value.strip("%").lower()
                rows = [r for r in rows if needle in str(r.get(field, "")).lower()]
        return rows

    def execute(self):
        import uuid as uuid_lib
        from datetime import datetime

        if self._op == "insert":
            new_row = dict(self._payload)
            new_row["id"] = str(uuid_lib.uuid4())
            new_row["created_at"] = datetime.now().isoformat()
            new_row.setdefault("completed_at", None)
            self._table_data.append(new_row)
            return FakeResult([new_row])

        elif self._op == "select":
            rows = self._apply_filters(list(self._table_data))
            return FakeResult(rows)

        elif self._op == "update":
            matched = self._apply_filters(list(self._table_data))
            for row in matched:
                row.update(self._payload)
            return FakeResult(matched)

        elif self._op == "delete":
            matched = self._apply_filters(list(self._table_data))
            matched_ids = {r["id"] for r in matched}
            self._table_data[:] = [r for r in self._table_data if r["id"] not in matched_ids]
            return FakeResult(matched)

        return FakeResult([])


class FakeClient:
    def __init__(self):
        self._data = []

    def table(self, name):
        return FakeQuery(self._data, name)


@pytest.fixture
def tm():
    fake_client = FakeClient()
    return TaskManager(client=fake_client)


def test_add_task_success(tm):
    task = tm.add_task("Buy groceries", priority="High", category="Home")
    assert task["text"] == "Buy groceries"
    assert task["priority"] == "High"
    assert task["completed"] is False
    assert len(tm.get_all_tasks()) == 1


def test_add_task_empty_text_raises(tm):
    with pytest.raises(ValueError):
        tm.add_task("   ")


def test_add_task_too_long_raises(tm):
    with pytest.raises(ValueError):
        tm.add_task("x" * 201)


def test_add_task_invalid_priority_defaults_medium(tm):
    task = tm.add_task("Test task", priority="Nonsense")
    assert task["priority"] == "Medium"


def test_toggle_complete(tm):
    task = tm.add_task("Wash car")
    ok = tm.toggle_complete(task["id"])
    assert ok is True
    updated = tm.get_task(task["id"])
    assert updated["completed"] is True
    assert updated["completed_at"] is not None

    tm.toggle_complete(task["id"])
    updated2 = tm.get_task(task["id"])
    assert updated2["completed"] is False
    assert updated2["completed_at"] is None


def test_toggle_nonexistent_task(tm):
    assert tm.toggle_complete("fake-id") is False


def test_delete_task(tm):
    task = tm.add_task("Delete me")
    assert tm.delete_task(task["id"]) is True
    assert tm.get_task(task["id"]) is None


def test_delete_nonexistent_task(tm):
    assert tm.delete_task("fake-id") is False


def test_update_task_text(tm):
    task = tm.add_task("Original")
    tm.update_task(task["id"], text="Updated")
    assert tm.get_task(task["id"])["text"] == "Updated"


def test_update_task_invalid_text_raises(tm):
    task = tm.add_task("Original")
    with pytest.raises(ValueError):
        tm.update_task(task["id"], text="")


def test_delete_completed(tm):
    t1 = tm.add_task("Task 1")
    t2 = tm.add_task("Task 2")
    tm.toggle_complete(t1["id"])
    deleted = tm.delete_completed()
    assert deleted == 1
    remaining = tm.get_all_tasks()
    assert len(remaining) == 1
    assert remaining[0]["id"] == t2["id"]


def test_clear_all(tm):
    tm.add_task("Task 1")
    tm.add_task("Task 2")
    count = tm.clear_all()
    assert count == 2
    assert len(tm.get_all_tasks()) == 0


def test_filter_by_status(tm):
    t1 = tm.add_task("Active task")
    t2 = tm.add_task("Completed task")
    tm.toggle_complete(t2["id"])

    active = tm.filter_tasks(status="Active")
    completed = tm.filter_tasks(status="Completed")
    assert len(active) == 1 and active[0]["id"] == t1["id"]
    assert len(completed) == 1 and completed[0]["id"] == t2["id"]


def test_filter_by_priority(tm):
    tm.add_task("Low priority", priority="Low")
    tm.add_task("High priority", priority="High")
    result = tm.filter_tasks(priority="High")
    assert len(result) == 1
    assert result[0]["priority"] == "High"


def test_filter_by_search(tm):
    tm.add_task("Buy milk")
    tm.add_task("Walk the dog")
    result = tm.filter_tasks(search="milk")
    assert len(result) == 1
    assert "milk" in result[0]["text"].lower()


def test_filter_by_category(tm):
    tm.add_task("Work task", category="Work")
    tm.add_task("Home task", category="Home")
    result = tm.filter_tasks(category="Work")
    assert len(result) == 1
    assert result[0]["category"] == "Work"


def test_get_categories(tm):
    tm.add_task("Task 1", category="Work")
    tm.add_task("Task 2", category="Home")
    tm.add_task("Task 3", category="Work")
    cats = tm.get_categories()
    assert cats == ["Home", "Work"]


def test_get_stats(tm):
    t1 = tm.add_task("Task 1")
    t2 = tm.add_task("Task 2")
    tm.add_task("Task 3")
    tm.toggle_complete(t1["id"])
    tm.toggle_complete(t2["id"])

    stats = tm.get_stats()
    assert stats["total"] == 3
    assert stats["completed"] == 2
    assert stats["active"] == 1
    assert stats["completion_rate"] == 66.7


def test_get_stats_empty(tm):
    stats = tm.get_stats()
    assert stats["total"] == 0
    assert stats["completion_rate"] == 0.0


def test_overdue_detection(tm):
    task = tm.add_task("Old task", due_date="2020-01-01")
    assert tm.is_overdue(task) is True

    tm.toggle_complete(task["id"])
    updated = tm.get_task(task["id"])
    assert tm.is_overdue(updated) is False


def test_validate_task_text_none(tm):
    assert TaskManager.validate_task_text(None) is not None


def test_validate_task_text_valid(tm):
    assert TaskManager.validate_task_text("Valid task") is None


def test_missing_credentials_raises(monkeypatch):
    """If no client is passed and no env vars/secrets exist, should raise clearly."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Supabase credentials not found"):
        TaskManager()
