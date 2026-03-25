"""Tests for DashboardPage — stat cards, priority breakdown, recent completions."""
from __future__ import annotations

import customtkinter as ctk
from unittest.mock import patch

import pytest

from gui_test_helpers import find_widget, find_all_widgets


@pytest.fixture
def dashboard_page(tk_root, mock_app, pump):
    from gui.pages.dashboard_page import DashboardPage
    page = DashboardPage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestDashboardPageWidgets:
    """Verify that build() creates all expected sections."""

    def test_open_latest_button(self, dashboard_page):
        btn = find_widget(dashboard_page, ctk.CTkButton, text="Open Latest Report")
        assert btn is not None

    def test_refresh_button(self, dashboard_page):
        btn = find_widget(dashboard_page, ctk.CTkButton, text="Refresh")
        assert btn is not None

    def test_dashboard_scroll_frame(self, dashboard_page):
        assert dashboard_page._dash_scroll is not None

    def test_stat_cards_frame(self, dashboard_page):
        assert dashboard_page._dash_cards_frame is not None

    def test_priority_frame(self, dashboard_page):
        assert dashboard_page._dash_priority_frame is not None

    def test_recent_frame(self, dashboard_page):
        assert dashboard_page._dash_recent_frame is not None

    def test_site_frame(self, dashboard_page):
        assert dashboard_page._dash_site_frame is not None


class TestDashboardPageRefresh:
    """Verify that refresh() populates sections correctly."""

    def test_stat_cards_created(self, dashboard_page, pump):
        dashboard_page.refresh()
        pump()
        children = dashboard_page._dash_cards_frame.winfo_children()
        assert len(children) == 4  # Weekly, Ongoing, Completed, Total Active

    def test_priority_section_has_content(self, dashboard_page, pump):
        dashboard_page.refresh()
        pump()
        children = dashboard_page._dash_priority_frame.winfo_children()
        # Should have title label + 5 priority row frames
        assert len(children) >= 6

    def test_recent_section_has_content(self, dashboard_page, pump):
        dashboard_page.refresh()
        pump()
        children = dashboard_page._dash_recent_frame.winfo_children()
        # At least the title label + "No tasks completed" message
        assert len(children) >= 2

    def test_site_section_has_content(self, dashboard_page, pump):
        dashboard_page.refresh()
        pump()
        children = dashboard_page._dash_site_frame.winfo_children()
        # Title + at least one site row (Harmattan, Taylor)
        assert len(children) >= 2

    def test_refresh_updates_after_profile_change(self, dashboard_page, mock_app, pump):
        dashboard_page.refresh()
        pump()
        cards_before = len(dashboard_page._dash_cards_frame.winfo_children())
        # Add another task and refresh to verify data changes propagate
        from helpers.domain.task import Task
        p = mock_app.profile.find_project("P-001")
        t = Task(id="T-099", title="Extra", project_id="P-001",
                 status="In Progress", priority=1, supervisor="X", site="Y")
        p.add_task(t)
        dashboard_page.refresh()
        pump()
        cards_after = len(dashboard_page._dash_cards_frame.winfo_children())
        # Same 4 cards (count stays 4)
        assert cards_after == cards_before == 4

    def test_open_latest_no_reports(self, dashboard_page, pump):
        with patch("gui.pages.dashboard_page.find_latest", return_value=None), \
             patch("tkinter.messagebox.showinfo") as m_info:
            dashboard_page._open_latest()
            m_info.assert_called_once()
