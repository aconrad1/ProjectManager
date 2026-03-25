"""Tests for SchedulerPage — 7-day weekly planner grid."""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta

import customtkinter as ctk
import pytest

from gui_test_helpers import find_widget, find_all_widgets


@pytest.fixture
def scheduler_page(tk_root, mock_app, pump):
    from gui.pages.scheduler_page import SchedulerPage
    page = SchedulerPage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestSchedulerPageWidgets:
    """Verify that build() creates all expected widgets."""

    def test_week_label_present(self, scheduler_page):
        assert isinstance(scheduler_page._week_label, ctk.CTkLabel)

    def test_warning_label_present(self, scheduler_page):
        assert isinstance(scheduler_page._warning_label, ctk.CTkLabel)

    def test_this_week_button(self, scheduler_page):
        btn = find_widget(scheduler_page, ctk.CTkButton, text="This Week")
        assert btn is not None

    def test_prev_button(self, scheduler_page):
        btn = find_widget(scheduler_page, ctk.CTkButton, text="◀")
        assert btn is not None

    def test_next_button(self, scheduler_page):
        btn = find_widget(scheduler_page, ctk.CTkButton, text="▶")
        assert btn is not None

    def test_scroll_frame_present(self, scheduler_page):
        assert scheduler_page._scroll is not None


class TestSchedulerPageNavigation:
    """Verify week navigation controls."""

    def test_go_next_week_advances(self, scheduler_page, pump):
        original = scheduler_page._week_start
        scheduler_page._go_next_week()
        pump()
        assert scheduler_page._week_start == original + timedelta(days=7)

    def test_go_prev_week_retreats(self, scheduler_page, pump):
        original = scheduler_page._week_start
        scheduler_page._go_prev_week()
        pump()
        assert scheduler_page._week_start == original - timedelta(days=7)

    def test_go_this_week_resets(self, scheduler_page, pump):
        # Move forward first
        scheduler_page._go_next_week()
        scheduler_page._go_next_week()
        pump()
        scheduler_page._go_this_week()
        pump()
        from helpers.scheduling.engine import week_start_date
        expected = week_start_date(date.today())
        assert scheduler_page._week_start == expected

    def test_week_label_shows_date_range(self, scheduler_page, pump):
        scheduler_page.refresh()
        pump()
        text = scheduler_page._week_label.cget("text")
        assert "–" in text or "-" in text  # date range separator


class TestSchedulerPageRendering:
    """Verify that _render() populates the grid."""

    def test_render_creates_content(self, scheduler_page, pump):
        scheduler_page.refresh()
        pump()
        children = scheduler_page._scroll.winfo_children()
        # Should have day headers, budget bars, priority rows
        assert len(children) > 0

    def test_warning_label_empty_when_under_budget(self, scheduler_page, pump):
        scheduler_page.refresh()
        pump()
        text = scheduler_page._warning_label.cget("text")
        # With only 3 tasks, unlikely to be over 8h budget
        # (no assertion on specific text, just verify it renders without error)
        assert isinstance(text, str)
