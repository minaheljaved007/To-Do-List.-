"""
test_app_integration.py
Integration tests that run the real app.py through Streamlit's AppTest
framework, using a mocked Supabase client (no real network calls) so
the full UI + database-backed logic path is verified together.

Run with: pytest test_app_integration.py -v
"""

import os
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    """
    Ensures every test runs with fake credentials and a fresh fake
    in-memory Supabase client, so no real network call is ever made
    and no data leaks between tests via Streamlit's resource cache.
    """
    monkeypatch.setenv("SUPABASE_URL", "https://fake-project.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "fake-anon-key")

    import task_manager as tm_module
    from test_task_manager import FakeClient

    monkeypatch.setattr(tm_module, "create_client", lambda url, key: FakeClient())

    # st.cache_resource persists across AppTest runs within the same
    # process (it's a process-wide cache), so without clearing it here,
    # the TaskManager (and its in-memory fake data) from a previous test
    # would leak into this one.
    import streamlit as st
    st.cache_resource.clear()

    yield


def test_app_runs_without_exceptions():
    at = AppTest.from_file("app.py")
    at.run(timeout=15)
    assert not at.exception, f"App raised exception on startup: {at.exception}"


def test_app_shows_title():
    at = AppTest.from_file("app.py")
    at.run(timeout=15)
    titles = [t.value for t in at.title]
    assert any("To-Do List" in t for t in titles)


def test_add_task_via_form():
    at = AppTest.from_file("app.py")
    at.run(timeout=15)

    task_inputs = [ti for ti in at.text_input if ti.label == "Task description"]
    assert len(task_inputs) == 1
    task_inputs[0].set_value("Test integration task")

    submit_buttons = [b for b in at.button if "Add Task" in (b.label or "")]
    assert len(submit_buttons) == 1
    submit_buttons[0].click().run(timeout=15)

    assert not at.exception, f"Exception after adding task: {at.exception}"

    markdowns = [m.value for m in at.markdown if "Test integration task" in m.value]
    assert len(markdowns) == 1

    metrics = {m.label: m.value for m in at.metric}
    assert metrics.get("Total") == "1"


def test_empty_task_shows_error():
    at = AppTest.from_file("app.py")
    at.run(timeout=15)

    submit_buttons = [b for b in at.button if "Add Task" in (b.label or "")]
    submit_buttons[0].click().run(timeout=15)

    assert not at.exception
    errors = at.error
    assert len(errors) >= 1


def test_no_tasks_shows_info_message():
    at = AppTest.from_file("app.py")
    at.run(timeout=15)
    infos = [i.value for i in at.info]
    assert any("No tasks found" in i for i in infos)


def test_toggle_and_delete_flow():
    at = AppTest.from_file("app.py")
    at.run(timeout=15)

    task_inputs = [ti for ti in at.text_input if ti.label == "Task description"]
    task_inputs[0].set_value("Toggle and delete me")
    submit_buttons = [b for b in at.button if "Add Task" in (b.label or "")]
    submit_buttons[0].click().run(timeout=15)
    assert not at.exception

    cb = at.checkbox[0]
    cb.set_value(True).run(timeout=15)
    assert not at.exception

    metrics = {m.label: m.value for m in at.metric}
    assert metrics.get("Completed") == "1"

    del_buttons = [b for b in at.button if b.label == "🗑️"]
    del_buttons[0].click().run(timeout=15)
    assert not at.exception

    infos = [i.value for i in at.info]
    assert any("No tasks found" in i for i in infos)


def test_missing_credentials_shows_friendly_message(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    at = AppTest.from_file("app.py")
    at.run(timeout=15)

    assert not at.exception, "Missing credentials should show a friendly error, not crash"
    errors = [e.value for e in at.error]
    assert any("Setup required" in e for e in errors)
