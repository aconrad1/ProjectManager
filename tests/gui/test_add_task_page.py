"""Tests for AddTaskPage — form for creating new tasks."""
from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from unittest.mock import patch
import pytest

from gui_test_helpers import find_widget, find_all_widgets


@pytest.fixture
def add_task_page(tk_root, mock_app, pump):
    from gui.pages.add_task_page import AddTaskPage
    page = AddTaskPage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    page.refresh()
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestAddTaskPageWidgets:
    def test_form_has_10_field_entries(self, add_task_page):
        assert len(add_task_page._add_entries) == 10

    def test_project_dropdown_populated(self, add_task_page):
        # After refresh, project menu should list the 2 projects
        val = add_task_page._project_var.get()
        assert val != "(no projects)"

    def test_title_entry_is_ctk_entry(self, add_task_page):
        assert isinstance(add_task_page._add_entries["Title"], ctk.CTkEntry)

    def test_description_is_textbox(self, add_task_page):
        assert isinstance(add_task_page._add_entries["Description"], ctk.CTkTextbox)

    def test_status_is_option_menu(self, add_task_page):
        assert isinstance(add_task_page._add_entries["Status"], ctk.CTkOptionMenu)

    def test_priority_is_option_menu(self, add_task_page):
        assert isinstance(add_task_page._add_entries["Priority"], ctk.CTkOptionMenu)

    def test_add_task_button_present(self, add_task_page):
        btn = find_widget(add_task_page, ctk.CTkButton, text="Add Task")
        assert btn is not None

    def test_date_completed_hidden_by_default(self, add_task_page):
        # When a widget is pack_forget'd, pack_info() raises TclError
        try:
            add_task_page._date_completed_frame.pack_info()
            visible = True
        except tk.TclError:
            visible = False
        assert not visible


class TestAddTaskPageCallbacks:
    def test_add_task_validates_empty_title(self, add_task_page, pump):
        # Leave title empty
        with patch("tkinter.messagebox.showwarning") as m_warn:
            add_task_page._do_add_task()
            m_warn.assert_called_once()

    def test_add_task_calls_service(self, add_task_page, pump):
        add_task_page._add_entries["Title"].insert(0, "New Test Task")
        add_task_page._do_add_task()
        pump()
        add_task_page.app.service._persist.assert_called()

    def test_form_resets_after_add(self, add_task_page, pump):
        add_task_page._add_entries["Title"].insert(0, "New Test Task")
        add_task_page._do_add_task()
        pump()
        assert add_task_page._add_entries["Title"].get() == ""

    def test_refresh_rebuilds_project_list(self, add_task_page, mock_app, pump):
        from helpers.domain.project import Project
        new_proj = Project(id="P-003", title="New Project", category="Ongoing", status="In Progress")
        mock_app.profile.add_project(new_proj)
        add_task_page.refresh()
        pump()
        val = add_task_page._project_var.get()
        # Should still be valid (not no projects)
        assert val != "(no projects)"

    def test_date_completed_hidden_for_ongoing(self, add_task_page, pump):
        # Select ongoing project
        add_task_page._project_var.set("Ongoing Project (Ongoing)")
        add_task_page._on_project_changed()
        pump()
        try:
            add_task_page._date_completed_frame.pack_info()
            visible = True
        except tk.TclError:
            visible = False
        assert not visible

    def test_add_task_no_project_shows_warning(self, add_task_page, pump):
        add_task_page._add_entries["Title"].insert(0, "Test")
        add_task_page._project_var.set("(no projects)")
        with patch("tkinter.messagebox.showwarning") as m_warn:
            add_task_page._do_add_task()
            m_warn.assert_called_once()
