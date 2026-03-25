"""Tests for TaskNotesDialog — viewing and adding timestamped task notes."""
from __future__ import annotations

import customtkinter as ctk
from unittest.mock import patch, MagicMock

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def notes_dialog(tk_root, pump):
    """TaskNotesDialog with mocked notes persistence."""
    from gui.dialogs.task_notes_dialog import TaskNotesDialog
    with patch("gui.dialogs.task_notes_dialog._load_notes", return_value={
        "T-001": [
            {"timestamp": "2026-03-20 10:00", "text": "First note"},
            {"timestamp": "2026-03-21 14:30", "text": "Second note"},
        ]
    }), patch("gui.dialogs.task_notes_dialog._save_notes") as m_save:
        dlg = TaskNotesDialog(tk_root, task_id="T-001", task_title="Task A")
        pump()
        yield dlg, m_save
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


@pytest.fixture
def empty_notes_dialog(tk_root, pump):
    """TaskNotesDialog with no existing notes."""
    from gui.dialogs.task_notes_dialog import TaskNotesDialog
    with patch("gui.dialogs.task_notes_dialog._load_notes", return_value={}), \
         patch("gui.dialogs.task_notes_dialog._save_notes") as m_save:
        dlg = TaskNotesDialog(tk_root, task_id="T-099", task_title="Empty Task")
        pump()
        yield dlg, m_save
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


class TestTaskNotesDialogWidgets:
    """Verify dialog creates all expected widgets."""

    def test_notes_display_present(self, notes_dialog):
        dlg, _ = notes_dialog
        assert isinstance(dlg._notes_display, ctk.CTkTextbox)

    def test_note_entry_present(self, notes_dialog):
        dlg, _ = notes_dialog
        assert isinstance(dlg._note_entry, ctk.CTkTextbox)

    def test_add_note_button(self, notes_dialog):
        dlg, _ = notes_dialog
        btn = find_widget(dlg, ctk.CTkButton, text="Add Note")
        assert btn is not None

    def test_close_button(self, notes_dialog):
        dlg, _ = notes_dialog
        btn = find_widget(dlg, ctk.CTkButton, text="Close")
        assert btn is not None


class TestTaskNotesDialogContent:
    """Verify notes display and interaction."""

    def test_existing_notes_displayed(self, notes_dialog, pump):
        dlg, _ = notes_dialog
        dlg._notes_display.configure(state="normal")
        content = dlg._notes_display.get("1.0", "end").strip()
        dlg._notes_display.configure(state="disabled")
        assert "First note" in content
        assert "Second note" in content

    def test_notes_displayed_newest_first(self, notes_dialog, pump):
        dlg, _ = notes_dialog
        dlg._notes_display.configure(state="normal")
        content = dlg._notes_display.get("1.0", "end").strip()
        dlg._notes_display.configure(state="disabled")
        # "Second note" should appear before "First note" (newest first = reversed)
        idx_second = content.index("Second note")
        idx_first = content.index("First note")
        assert idx_second < idx_first

    def test_empty_notes_shows_message(self, empty_notes_dialog, pump):
        dlg, _ = empty_notes_dialog
        dlg._notes_display.configure(state="normal")
        content = dlg._notes_display.get("1.0", "end").strip()
        dlg._notes_display.configure(state="disabled")
        assert "No notes yet" in content

    def test_add_note_calls_save(self, notes_dialog, pump):
        dlg, m_save = notes_dialog
        dlg._note_entry.insert("1.0", "New note text")
        with patch("gui.dialogs.task_notes_dialog._load_notes", return_value={
            "T-001": [
                {"timestamp": "2026-03-20 10:00", "text": "First note"},
                {"timestamp": "2026-03-21 14:30", "text": "Second note"},
            ]
        }):
            dlg._add_note()
            pump()
            m_save.assert_called_once()
            saved_data = m_save.call_args[0][0]
            assert len(saved_data["T-001"]) == 3
            assert saved_data["T-001"][-1]["text"] == "New note text"

    def test_empty_note_rejected(self, notes_dialog, pump):
        dlg, m_save = notes_dialog
        # Leave entry empty
        dlg._add_note()
        pump()
        m_save.assert_not_called()
