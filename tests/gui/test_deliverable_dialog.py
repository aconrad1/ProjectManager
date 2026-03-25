"""Tests for DeliverableDialog — modal dialog for adding/editing deliverables."""
from __future__ import annotations

from datetime import date

import customtkinter as ctk
from unittest.mock import MagicMock, patch

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def deliverable_dialog_add(tk_root, pump):
    """DeliverableDialog in add mode."""
    from gui.dialogs.deliverable_dialog import DeliverableDialog
    callback = MagicMock()
    dlg = DeliverableDialog(tk_root, title="Add Deliverable", task_id="T-001", on_save=callback)
    pump()
    yield dlg, callback
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


@pytest.fixture
def deliverable_dialog_edit(tk_root, pump):
    """DeliverableDialog in edit mode with a pre-filled deliverable."""
    from gui.dialogs.deliverable_dialog import DeliverableDialog
    from helpers.domain.deliverable import Deliverable

    deliv = Deliverable(
        id="D-099", title="Existing Deliverable", task_id="T-001",
        status="In Progress", description="Deliv desc",
        percent_complete=50, time_allocated=8.0, time_spent=3.5,
        start=date(2026, 3, 20), end=date(2026, 3, 25),
    )
    callback = MagicMock()
    dlg = DeliverableDialog(tk_root, title="Edit Deliverable", deliverable=deliv,
                            task_id="T-001", on_save=callback)
    pump()
    yield dlg, callback, deliv
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


class TestDeliverableDialogWidgets:
    """Verify dialog creates all expected fields."""

    def test_has_9_fields(self, deliverable_dialog_add):
        dlg, _ = deliverable_dialog_add
        assert len(dlg.entries) == 9

    def test_title_field(self, deliverable_dialog_add):
        dlg, _ = deliverable_dialog_add
        assert isinstance(dlg.entries["Title"], ctk.CTkEntry)

    def test_status_field(self, deliverable_dialog_add):
        dlg, _ = deliverable_dialog_add
        assert isinstance(dlg.entries["Status"], ctk.CTkOptionMenu)

    def test_percent_complete_field(self, deliverable_dialog_add):
        dlg, _ = deliverable_dialog_add
        assert isinstance(dlg.entries["% Complete"], ctk.CTkEntry)

    def test_time_allocated_field(self, deliverable_dialog_add):
        dlg, _ = deliverable_dialog_add
        assert isinstance(dlg.entries["Time Allocated"], ctk.CTkEntry)

    def test_save_button_present(self, deliverable_dialog_add):
        dlg, _ = deliverable_dialog_add
        btn = find_widget(dlg, ctk.CTkButton, text="Save")
        assert btn is not None


class TestDeliverableDialogEditMode:
    """Verify edit mode pre-fills fields."""

    def test_title_prefilled(self, deliverable_dialog_edit):
        dlg, _, deliv = deliverable_dialog_edit
        assert dlg.entries["Title"].get() == "Existing Deliverable"

    def test_percent_prefilled(self, deliverable_dialog_edit):
        dlg, _, deliv = deliverable_dialog_edit
        assert dlg.entries["% Complete"].get() == "50"

    def test_time_allocated_prefilled(self, deliverable_dialog_edit):
        dlg, _, deliv = deliverable_dialog_edit
        assert dlg.entries["Time Allocated"].get() == "8.0"

    def test_time_spent_prefilled(self, deliverable_dialog_edit):
        dlg, _, deliv = deliverable_dialog_edit
        assert dlg.entries["Time Spent"].get() == "3.5"

    def test_start_date_prefilled(self, deliverable_dialog_edit):
        dlg, _, deliv = deliverable_dialog_edit
        assert dlg.entries["Start Date"].get() == "2026-03-20"


class TestDeliverableDialogSave:
    """Verify save logic."""

    def test_save_validates_empty_title(self, deliverable_dialog_add, pump):
        dlg, callback = deliverable_dialog_add
        with patch("tkinter.messagebox.showwarning") as m_warn:
            dlg._save()
            m_warn.assert_called_once()
        callback.assert_not_called()

    def test_save_returns_correct_data(self, deliverable_dialog_add, pump):
        dlg, callback = deliverable_dialog_add
        dlg.entries["Title"].insert(0, "New Deliverable")
        dlg.entries["% Complete"].insert(0, "75")
        dlg.entries["Time Allocated"].insert(0, "4.5")
        dlg._save()
        pump()
        callback.assert_called_once()
        data = callback.call_args[0][0]
        assert data["title"] == "New Deliverable"
        assert data["percent_complete"] == 75
        assert data["time_allocated"] == 4.5

    def test_percent_clamped_to_100(self, deliverable_dialog_add, pump):
        dlg, callback = deliverable_dialog_add
        dlg.entries["Title"].insert(0, "Test")
        dlg.entries["% Complete"].insert(0, "150")
        dlg._save()
        pump()
        data = callback.call_args[0][0]
        assert data["percent_complete"] == 100

    def test_time_fields_accept_floats(self, deliverable_dialog_add, pump):
        dlg, callback = deliverable_dialog_add
        dlg.entries["Title"].insert(0, "Test")
        dlg.entries["Time Allocated"].insert(0, "4.5")
        dlg.entries["Time Spent"].insert(0, "2.25")
        dlg._save()
        pump()
        data = callback.call_args[0][0]
        assert data["time_allocated"] == 4.5
        assert data["time_spent"] == 2.25
