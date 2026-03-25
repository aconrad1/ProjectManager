"""Tests for BatchOperationDialog — batch status/priority/date changes."""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk
from unittest.mock import MagicMock, patch

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def batch_dialog(tk_root, mock_app, pump):
    """BatchOperationDialog with 2 task IDs."""
    from gui.dialogs.batch_dialog import BatchOperationDialog
    callback = MagicMock()
    dlg = BatchOperationDialog(
        tk_root,
        task_ids=["T-001", "T-002"],
        service=mock_app.service,
        on_complete=callback,
    )
    pump()
    yield dlg, callback, mock_app
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


class TestBatchDialogWidgets:
    """Verify dialog creates all expected widgets."""

    def test_header_shows_task_count(self, batch_dialog):
        dlg, _, _ = batch_dialog
        header = find_widget(dlg, ctk.CTkLabel, text="Batch Edit — 2 task(s)")
        assert header is not None

    def test_status_dropdown_present(self, batch_dialog):
        dlg, _, _ = batch_dialog
        assert isinstance(dlg._status_var, ctk.StringVar)

    def test_priority_dropdown_present(self, batch_dialog):
        dlg, _, _ = batch_dialog
        assert isinstance(dlg._prio_var, ctk.StringVar)
        assert dlg._prio_var.get() == "(no change)"

    def test_shift_checkboxes_present(self, batch_dialog):
        dlg, _, _ = batch_dialog
        assert isinstance(dlg._shift_start_var, ctk.BooleanVar)
        assert isinstance(dlg._shift_end_var, ctk.BooleanVar)
        assert isinstance(dlg._shift_deadline_var, ctk.BooleanVar)

    def test_days_entry_present(self, batch_dialog):
        dlg, _, _ = batch_dialog
        assert isinstance(dlg._shift_days_entry, ctk.CTkEntry)

    def test_apply_button(self, batch_dialog):
        dlg, _, _ = batch_dialog
        btn = find_widget(dlg, ctk.CTkButton, text="Apply")
        assert btn is not None

    def test_cancel_button(self, batch_dialog):
        dlg, _, _ = batch_dialog
        btn = find_widget(dlg, ctk.CTkButton, text="Cancel")
        assert btn is not None


class TestBatchDialogApply:
    """Verify apply logic."""

    def test_apply_status_changes(self, batch_dialog, pump):
        dlg, callback, mock_app = batch_dialog
        dlg._status_var.set("On Hold")
        dlg._apply()
        pump()
        # Both tasks should have status set
        t1 = mock_app.profile.find_task_global("T-001")
        t2 = mock_app.profile.find_task_global("T-002")
        assert t1.status == "On Hold"
        assert t2.status == "On Hold"
        callback.assert_called_once()

    def test_apply_priority_changes(self, batch_dialog, pump):
        dlg, callback, mock_app = batch_dialog
        dlg._prio_var.set("P1 - Urgent")
        dlg._apply()
        pump()
        t1 = mock_app.profile.find_task_global("T-001")
        t2 = mock_app.profile.find_task_global("T-002")
        assert t1.priority == 1
        assert t2.priority == 1
        callback.assert_called_once()

    def test_no_changes_shows_info(self, batch_dialog, pump):
        dlg, callback, _ = batch_dialog
        dlg._status_var.set("(no change)")
        dlg._prio_var.set("(no change)")
        with patch("tkinter.messagebox.showinfo") as m_info:
            dlg._apply()
            m_info.assert_called_once()
        callback.assert_not_called()

    def test_invalid_days_shows_warning(self, batch_dialog, pump):
        dlg, callback, _ = batch_dialog
        dlg._shift_start_var.set(True)
        dlg._shift_days_entry.insert(0, "abc")
        with patch("tkinter.messagebox.showwarning") as m_warn:
            dlg._apply()
            m_warn.assert_called_once()

    def test_date_shift_applies_delta(self, batch_dialog, pump):
        dlg, callback, mock_app = batch_dialog
        dlg._shift_start_var.set(True)
        dlg._shift_days_entry.insert(0, "7")
        # Task T-001 has start=2026-03-20
        t1 = mock_app.profile.find_task_global("T-001")
        original_start = t1.start
        dlg._apply()
        pump()
        assert t1.start == original_start + timedelta(days=7)
        callback.assert_called_once()
