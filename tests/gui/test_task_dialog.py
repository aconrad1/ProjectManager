"""Tests for TaskDialog — modal dialog for adding/editing tasks."""
from __future__ import annotations

from datetime import date

import customtkinter as ctk
from unittest.mock import MagicMock, patch

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def task_dialog_add(tk_root, pump):
    """TaskDialog in add mode (no task passed)."""
    from gui.dialogs.task_dialog import TaskDialog
    callback = MagicMock()
    dlg = TaskDialog(tk_root, title="Add Task", project_id="P-001", on_save=callback)
    pump()
    yield dlg, callback
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


@pytest.fixture
def task_dialog_edit(tk_root, pump):
    """TaskDialog in edit mode with a pre-filled task."""
    from gui.dialogs.task_dialog import TaskDialog
    from helpers.domain.task import Task

    task = Task(
        id="T-099", title="Existing Task", project_id="P-001",
        status="In Progress", priority=2, supervisor="Jane",
        site="Harmattan", description="Some desc", commentary="Notes here",
        start=date(2026, 3, 20), end=date(2026, 3, 27), deadline=date(2026, 4, 1),
    )
    callback = MagicMock()
    dlg = TaskDialog(tk_root, title="Edit Task", task=task, project_id="P-001", on_save=callback)
    pump()
    yield dlg, callback, task
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


class TestTaskDialogWidgets:
    """Verify dialog creates all expected fields."""

    def test_has_10_fields(self, task_dialog_add):
        dlg, _ = task_dialog_add
        assert len(dlg.entries) == 10

    def test_title_field_exists(self, task_dialog_add):
        dlg, _ = task_dialog_add
        assert isinstance(dlg.entries["Title"], ctk.CTkEntry)

    def test_status_field_exists(self, task_dialog_add):
        dlg, _ = task_dialog_add
        assert isinstance(dlg.entries["Status"], ctk.CTkOptionMenu)

    def test_priority_field_exists(self, task_dialog_add):
        dlg, _ = task_dialog_add
        assert isinstance(dlg.entries["Priority"], ctk.CTkOptionMenu)

    def test_save_button_present(self, task_dialog_add):
        dlg, _ = task_dialog_add
        btn = find_widget(dlg, ctk.CTkButton, text="Save")
        assert btn is not None

    def test_cancel_button_present(self, task_dialog_add):
        dlg, _ = task_dialog_add
        btn = find_widget(dlg, ctk.CTkButton, text="Cancel")
        assert btn is not None


class TestTaskDialogEditMode:
    """Verify edit mode pre-fills fields correctly."""

    def test_title_prefilled(self, task_dialog_edit):
        dlg, _, task = task_dialog_edit
        assert dlg.entries["Title"].get() == "Existing Task"

    def test_supervisor_prefilled(self, task_dialog_edit):
        dlg, _, task = task_dialog_edit
        assert dlg.entries["Supervisor"].get() == "Jane"

    def test_status_prefilled(self, task_dialog_edit):
        dlg, _, task = task_dialog_edit
        # Re-read the variable directly — it was set in __init__
        val = dlg._get("Status")
        assert val == "In Progress"

    def test_start_date_prefilled(self, task_dialog_edit):
        dlg, _, task = task_dialog_edit
        assert dlg.entries["Start Date"].get() == "2026-03-20"


class TestTaskDialogSave:
    """Verify save logic."""

    def test_save_validates_empty_title(self, task_dialog_add, pump):
        dlg, callback = task_dialog_add
        with patch("tkinter.messagebox.showwarning") as m_warn:
            dlg._save()
            m_warn.assert_called_once()
        callback.assert_not_called()

    def test_save_calls_callback(self, task_dialog_add, pump):
        dlg, callback = task_dialog_add
        dlg.entries["Title"].insert(0, "New Task")
        dlg._save()
        pump()
        callback.assert_called_once()
        data = callback.call_args[0][0]
        assert data["title"] == "New Task"
        assert data["project_id"] == "P-001"
        assert "priority" in data
        assert "status" in data

    def test_save_parses_date(self, task_dialog_add, pump):
        dlg, callback = task_dialog_add
        dlg.entries["Title"].insert(0, "Test")
        dlg.entries["Start Date"].insert(0, "2026-05-15")
        dlg._save()
        pump()
        data = callback.call_args[0][0]
        assert data["start"] == date(2026, 5, 15)

    def test_invalid_date_returns_none(self, task_dialog_add, pump):
        dlg, callback = task_dialog_add
        dlg.entries["Title"].insert(0, "Test")
        dlg.entries["Deadline"].insert(0, "not-a-date")
        dlg._save()
        pump()
        data = callback.call_args[0][0]
        assert data["deadline"] is None
