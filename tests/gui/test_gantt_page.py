"""Tests for GanttPage — canvas-based project timeline view."""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta

import customtkinter as ctk
import pytest

from gui_test_helpers import find_widget, find_all_widgets


@pytest.fixture
def gantt_page(tk_root, mock_app, pump):
    from gui.pages.gantt_page import GanttPage
    page = GanttPage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestGanttPageWidgets:
    """Verify that build() creates all expected widgets."""

    def test_canvas_exists(self, gantt_page):
        assert isinstance(gantt_page._canvas, tk.Canvas)

    def test_dark_mode_checkbox_present(self, gantt_page):
        assert isinstance(gantt_page._dark_var, ctk.BooleanVar)
        cb = find_widget(gantt_page, ctk.CTkCheckBox, text="Dark Mode")
        assert cb is not None

    def test_filter_dropdown_present(self, gantt_page):
        assert isinstance(gantt_page._filter_var, ctk.StringVar)
        assert gantt_page._filter_var.get() == "All"

    def test_zoom_slider_present(self, gantt_page):
        assert isinstance(gantt_page._day_width_var, tk.IntVar)
        slider = find_widget(gantt_page, ctk.CTkSlider)
        assert slider is not None

    def test_scrollbars_present(self, gantt_page):
        scrollbars = find_all_widgets(gantt_page, tk.Scrollbar)
        assert len(scrollbars) >= 2  # vertical + horizontal

    def test_canvas_frame_exists(self, gantt_page):
        assert gantt_page._canvas_frame is not None


class TestGanttPageRendering:
    """Verify that _render() populates the canvas."""

    def test_render_populates_rows(self, gantt_page, pump):
        gantt_page.refresh()
        pump()
        # With 2 dated tasks (T-001, T-002 have start dates), rows should include projects + tasks
        assert len(gantt_page._rows) > 0

    def test_render_has_project_rows(self, gantt_page, pump):
        gantt_page.refresh()
        pump()
        project_rows = [r for r in gantt_page._rows if r["type"] == "project"]
        assert len(project_rows) >= 1  # At least Ongoing Project has dated tasks

    def test_render_has_task_rows(self, gantt_page, pump):
        gantt_page.refresh()
        pump()
        task_rows = [r for r in gantt_page._rows if r["type"] == "task"]
        assert len(task_rows) >= 2  # T-001 and T-002 are dated; T-003 undated goes to unscheduled

    def test_render_unscheduled_section(self, gantt_page, pump):
        gantt_page.refresh()
        pump()
        section_rows = [r for r in gantt_page._rows if r["type"] == "section"]
        # T-003 has no start date → should appear in "No Scheduled Start" section
        assert len(section_rows) == 1
        assert section_rows[0]["label"] == "No Scheduled Start"

    def test_filter_by_category(self, gantt_page, pump):
        gantt_page._filter_var.set("Weekly")
        gantt_page._render()
        pump()
        project_rows = [r for r in gantt_page._rows if r["type"] == "project"]
        # Weekly project has no dated tasks → no project header in main section
        # but T-003 is undated → shows in unscheduled section
        task_rows = [r for r in gantt_page._rows if r["type"] == "task"]
        for t in task_rows:
            assert "Weekly" in t.get("label", "") or t.get("item_id") == "T-003"


class TestGanttPageDarkMode:
    """Verify dark mode toggle."""

    def test_dark_mode_default_off(self, gantt_page):
        assert gantt_page._dark_mode is False

    def test_toggle_dark_mode_changes_bg(self, gantt_page, pump):
        gantt_page._dark_var.set(True)
        gantt_page._toggle_dark_mode()
        pump()
        assert gantt_page._dark_mode is True
        bg = gantt_page._canvas.cget("bg")
        # Should be dark (not white)
        assert bg != "white"

    def test_bar_color_returns_correct_for_status(self, gantt_page):
        # Light mode
        gantt_page._dark_mode = False
        color_ip = gantt_page._bar_color("In Progress")
        color_c = gantt_page._bar_color("Completed")
        assert color_ip != color_c

    def test_toggle_back_to_light(self, gantt_page, pump):
        gantt_page._dark_var.set(True)
        gantt_page._toggle_dark_mode()
        pump()
        gantt_page._dark_var.set(False)
        gantt_page._toggle_dark_mode()
        pump()
        assert gantt_page._dark_mode is False
        assert gantt_page._canvas.cget("bg") == "white"


class TestGanttPageContextMenu:
    """Verify context menu actions."""

    def test_shift_date_modifies_task(self, gantt_page, pump):
        gantt_page.refresh()
        pump()
        task = gantt_page.app.profile.find_task_global("T-001")
        original_start = task.start
        gantt_page._shift_date("T-001", "start", 1)
        assert task.start == original_start + timedelta(days=1)

    def test_shift_date_end(self, gantt_page, pump):
        gantt_page.refresh()
        pump()
        task = gantt_page.app.profile.find_task_global("T-001")
        original_end = task.end
        gantt_page._shift_date("T-001", "end", -1)
        assert task.end == original_end - timedelta(days=1)
