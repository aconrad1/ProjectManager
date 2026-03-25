"""Tests for TasksPage — the primary task management treeview."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from unittest.mock import patch, MagicMock

import pytest
import customtkinter as ctk

from gui_test_helpers import (
    find_widget, find_all_widgets, get_treeview_items,
    get_treeview_column_names,
)


@pytest.fixture
def tasks_page(tk_root, mock_app, pump):
    """Instantiate a real TasksPage with real widgets."""
    from gui.pages.tasks_page import TasksPage

    page = TasksPage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


# ═══════════════════════════════════════════════════════════════════════════════
#  Widget existence
# ═══════════════════════════════════════════════════════════════════════════════


class TestTasksPageWidgets:
    """Verify that build() creates all expected widgets."""

    def test_treeview_exists(self, tasks_page):
        assert isinstance(tasks_page.tree, ttk.Treeview)

    def test_treeview_has_correct_columns(self, tasks_page):
        cols = get_treeview_column_names(tasks_page.tree)
        expected = ["title", "supervisor", "site", "status",
                    "priority", "scheduled", "time", "category"]
        assert cols == expected

    def test_treeview_selectmode_extended(self, tasks_page):
        assert str(tasks_page.tree.cget("selectmode")) == "extended"

    def test_filter_var_initialized(self, tasks_page):
        assert isinstance(tasks_page._filter_var, (tk.StringVar, ctk.StringVar))
        assert tasks_page._filter_var.get() in ("All", "Weekly", "Ongoing", "Completed")

    def test_search_entry_present(self, tasks_page):
        assert hasattr(tasks_page, "_search_entry")
        assert isinstance(tasks_page._search_entry, ctk.CTkEntry)

    def test_status_bar_present(self, tasks_page):
        assert hasattr(tasks_page, "_status_label")
        assert isinstance(tasks_page._status_label, ctk.CTkLabel)

    def test_context_menu_created(self, tasks_page):
        assert isinstance(tasks_page._ctx_menu, tk.Menu)
        # Context menu should have many items
        assert tasks_page._ctx_menu.index("end") >= 10

    def test_dnd_available_flag_exists(self, tasks_page):
        assert isinstance(tasks_page._dnd_available, bool)

    def test_button_bar_has_edit_button(self, tasks_page):
        btn = find_widget(tasks_page, ctk.CTkButton, text="Edit Selected")
        assert btn is not None

    def test_button_bar_has_delete_button(self, tasks_page):
        btn = find_widget(tasks_page, ctk.CTkButton, text="Delete Selected")
        assert btn is not None

    def test_button_bar_has_duplicate_button(self, tasks_page):
        btn = find_widget(tasks_page, ctk.CTkButton, text="Duplicate")
        assert btn is not None

    def test_button_bar_has_add_project_button(self, tasks_page):
        btn = find_widget(tasks_page, ctk.CTkButton, text="Add Project")
        assert btn is not None

    def test_button_bar_has_batch_edit_button(self, tasks_page):
        btn = find_widget(tasks_page, ctk.CTkButton, text="Batch Edit…")
        assert btn is not None

    def test_button_bar_has_refresh_button(self, tasks_page):
        btn = find_widget(tasks_page, ctk.CTkButton, text="Refresh")
        assert btn is not None

    def test_attachment_buttons_present(self, tasks_page):
        for label in ("Attach File", "View Attachments", "Link Folder", "Open Folder", "Task Notes"):
            btn = find_widget(tasks_page, ctk.CTkButton, text=label)
            assert btn is not None, f"Missing button: {label}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Treeview population
# ═══════════════════════════════════════════════════════════════════════════════


class TestTasksPageTreeview:
    """Verify that refresh() populates the tree correctly."""

    def test_refresh_populates_projects(self, tasks_page, pump):
        tasks_page.refresh()
        pump()
        items = get_treeview_items(tasks_page.tree)
        project_items = [i for i in items if "project" in (i["tags"] or ())]
        assert len(project_items) == 2  # Ongoing Project + Weekly Project

    def test_refresh_populates_tasks(self, tasks_page, pump):
        tasks_page.refresh()
        pump()
        items = get_treeview_items(tasks_page.tree)
        # Should find tasks as children of projects
        task_iids = [i["iid"] for i in items if i["iid"].startswith("task_")]
        assert len(task_iids) == 3  # T-001, T-002, T-003

    def test_refresh_populates_deliverables(self, tasks_page, pump):
        tasks_page.refresh()
        pump()
        items = get_treeview_items(tasks_page.tree)
        deliv_iids = [i["iid"] for i in items if i["iid"].startswith("deliv_")]
        assert len(deliv_iids) == 2  # D-001, D-002

    def test_filter_by_category(self, tasks_page, pump):
        tasks_page._filter_var.set("Weekly")
        tasks_page._populate_tree()
        pump()
        items = get_treeview_items(tasks_page.tree)
        project_items = [i for i in items if "project" in (i["tags"] or ())]
        assert len(project_items) == 1
        assert "Weekly" in str(project_items[0]["values"])

    def test_search_filters_tasks(self, tasks_page, pump):
        tasks_page._filter_var.set("All")
        tasks_page._search_var.set("Task A")
        tasks_page._populate_tree()
        pump()
        items = get_treeview_items(tasks_page.tree)
        task_iids = [i for i in items if i["iid"].startswith("task_")]
        assert len(task_iids) == 1
        assert "Task A" in str(task_iids[0]["values"])

    def test_status_bar_shows_counts(self, tasks_page, pump):
        tasks_page.refresh()
        pump()
        text = tasks_page._status_label.cget("text")
        assert "Weekly:" in text
        assert "Ongoing:" in text

    def test_dnd_warning_in_status_bar(self, tasks_page, pump):
        tasks_page._dnd_available = False
        tasks_page.update_status_bar()
        pump()
        text = tasks_page._status_label.cget("text")
        assert "Drag-and-drop unavailable" in text

    def test_no_dnd_warning_when_available(self, tasks_page, pump):
        tasks_page._dnd_available = True
        tasks_page.update_status_bar()
        pump()
        text = tasks_page._status_label.cget("text")
        assert "Drag-and-drop unavailable" not in text


# ═══════════════════════════════════════════════════════════════════════════════
#  Callback logic
# ═══════════════════════════════════════════════════════════════════════════════


class TestTasksPageCallbacks:
    """Verify that widget interactions trigger correct service calls."""

    def _select_first_task(self, page, pump):
        """Populate tree and select the first task row."""
        page.refresh()
        pump()
        items = get_treeview_items(page.tree)
        for item in items:
            if item["iid"].startswith("task_"):
                page.tree.selection_set(item["iid"])
                pump()
                return item["iid"]
        return None

    def test_quick_set_status(self, tasks_page, pump):
        self._select_first_task(tasks_page, pump)
        tasks_page._quick_set_status("On Hold")
        task = tasks_page.app.profile.find_task_global("T-001")
        assert task.status == "On Hold"

    def test_quick_set_priority(self, tasks_page, pump):
        self._select_first_task(tasks_page, pump)
        tasks_page._quick_set_priority(5)
        task = tasks_page.app.profile.find_task_global("T-001")
        assert task.priority == 5

    def test_delete_selected_task_calls_service(self, tasks_page, pump):
        iid = self._select_first_task(tasks_page, pump)
        assert iid is not None
        with patch("tkinter.messagebox.askyesno", return_value=True):
            tasks_page._delete_selected_task()
        tasks_page.app.service._persist.assert_called()

    def test_add_project_opens_dialog(self, tasks_page, pump):
        with patch("gui.pages.tasks_page.ProjectDialog") as MockDialog:
            tasks_page._add_project()
            MockDialog.assert_called_once()

    def test_edit_selected_no_selection_shows_info(self, tasks_page, pump):
        tasks_page.tree.selection_set([])
        pump()
        with patch("tkinter.messagebox.showinfo") as m:
            tasks_page._edit_selected_task()
            m.assert_called_once()

    def test_batch_edit_no_selection_shows_info(self, tasks_page, pump):
        tasks_page.tree.selection_set([])
        pump()
        with patch("tkinter.messagebox.showinfo") as m:
            tasks_page._batch_edit()
            m.assert_called_once()

    def test_batch_edit_with_tasks_opens_dialog(self, tasks_page, pump):
        # Select two task rows
        tasks_page.refresh()
        pump()
        items = get_treeview_items(tasks_page.tree)
        task_iids = [i["iid"] for i in items if i["iid"].startswith("task_")][:2]
        tasks_page.tree.selection_set(task_iids)
        pump()

        with patch("gui.pages.tasks_page.BatchOperationDialog") as MockDialog:
            tasks_page._batch_edit()
            MockDialog.assert_called_once()
            call_kw = MockDialog.call_args
            # task_ids may be passed positionally or as kwarg
            task_ids = call_kw.kwargs.get("task_ids") or call_kw.args[1] if len(call_kw.args) > 1 else call_kw.kwargs.get("task_ids", [])
            assert len(task_ids) >= 1

    def test_duplicate_task_opens_dialog(self, tasks_page, pump):
        self._select_first_task(tasks_page, pump)
        with patch("gui.pages.tasks_page.TaskDialog") as MockDialog:
            tasks_page._duplicate_selected_task()
            MockDialog.assert_called_once()

    def test_edit_selected_task_opens_dialog(self, tasks_page, pump):
        self._select_first_task(tasks_page, pump)
        with patch("gui.pages.tasks_page.TaskDialog") as MockDialog:
            tasks_page._edit_selected_task()
            MockDialog.assert_called_once()

    def test_ui_state_persisted_on_filter_change(self, tasks_page, pump):
        with patch("gui.pages.tasks_page.save_ui_state") as m_save:
            tasks_page._filter_var.set("Weekly")
            tasks_page._on_filter_change()
            pump()
            m_save.assert_called_once()
            state = m_save.call_args[0][0]
            assert state["tasks_filter"] == "Weekly"
