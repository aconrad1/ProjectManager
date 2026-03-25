"""Tests for ProjectDialog — modal dialog for adding/editing projects."""
from __future__ import annotations

from datetime import date

import customtkinter as ctk
from unittest.mock import MagicMock, patch

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def project_dialog_add(tk_root, pump):
    """ProjectDialog in add mode."""
    from gui.dialogs.project_dialog import ProjectDialog
    callback = MagicMock()
    dlg = ProjectDialog(tk_root, title="Add Project", on_save=callback)
    pump()
    yield dlg, callback
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


@pytest.fixture
def project_dialog_edit(tk_root, pump):
    """ProjectDialog in edit mode with a pre-filled project."""
    from gui.dialogs.project_dialog import ProjectDialog
    from helpers.domain.project import Project

    project = Project(
        id="P-099", title="Existing Project", category="Ongoing",
        status="In Progress", description="Project desc",
        supervisor="Kurt", site="Taylor", priority=2,
        notes="Some notes", start=date(2026, 1, 1),
    )
    callback = MagicMock()
    dlg = ProjectDialog(tk_root, title="Edit Project", project=project, on_save=callback)
    pump()
    yield dlg, callback, project
    try:
        dlg.destroy()
    except Exception:
        pass
    pump()


class TestProjectDialogWidgets:
    """Verify dialog creates all expected fields."""

    def test_has_12_fields(self, project_dialog_add):
        dlg, _ = project_dialog_add
        assert len(dlg.entries) == 12

    def test_title_field_exists(self, project_dialog_add):
        dlg, _ = project_dialog_add
        assert isinstance(dlg.entries["Title"], ctk.CTkEntry)

    def test_category_field_exists(self, project_dialog_add):
        dlg, _ = project_dialog_add
        assert isinstance(dlg.entries["Category"], ctk.CTkOptionMenu)

    def test_priority_allows_none(self, project_dialog_add):
        dlg, _ = project_dialog_add
        prio_var = dlg.entries["Priority"]._variable
        assert prio_var.get() == "None"

    def test_save_button_present(self, project_dialog_add):
        dlg, _ = project_dialog_add
        btn = find_widget(dlg, ctk.CTkButton, text="Save")
        assert btn is not None

    def test_cancel_button_present(self, project_dialog_add):
        dlg, _ = project_dialog_add
        btn = find_widget(dlg, ctk.CTkButton, text="Cancel")
        assert btn is not None


class TestProjectDialogEditMode:
    """Verify edit mode pre-fills fields."""

    def test_title_prefilled(self, project_dialog_edit):
        dlg, _, project = project_dialog_edit
        assert dlg.entries["Title"].get() == "Existing Project"

    def test_category_prefilled(self, project_dialog_edit):
        dlg, _, project = project_dialog_edit
        assert dlg.entries["Category"]._variable.get() == "Ongoing"

    def test_supervisor_prefilled(self, project_dialog_edit):
        dlg, _, project = project_dialog_edit
        assert dlg.entries["Supervisor"].get() == "Kurt"


class TestProjectDialogSave:
    """Verify save logic."""

    def test_save_validates_empty_title(self, project_dialog_add, pump):
        dlg, callback = project_dialog_add
        with patch("tkinter.messagebox.showwarning") as m_warn:
            dlg._save()
            m_warn.assert_called_once()
        callback.assert_not_called()

    def test_save_returns_correct_data(self, project_dialog_add, pump):
        dlg, callback = project_dialog_add
        dlg.entries["Title"].insert(0, "New Project")
        dlg._save()
        pump()
        callback.assert_called_once()
        data = callback.call_args[0][0]
        assert data["title"] == "New Project"
        assert "category" in data
        assert "priority" in data
        assert "status" in data

    def test_category_options(self, project_dialog_add):
        dlg, _ = project_dialog_add
        cat_var = dlg.entries["Category"]._variable
        # Default is "Ongoing"
        assert cat_var.get() in ("Weekly", "Ongoing", "Completed")
