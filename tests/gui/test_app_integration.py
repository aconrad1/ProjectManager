"""Tests for App integration — orchestrator, sidebar, navigation, keybindings."""
from __future__ import annotations

import customtkinter as ctk
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from gui_test_helpers import find_widget, find_all_widgets


@pytest.fixture
def app_instance(tk_root, pump):
    """Create a real App instance with mocked data loading.

    The App class creates its own CTk root via super().__init__, so we
    patch the heavy I/O parts (workbook loading, profile sync) to avoid
    file system dependency while still testing real widget behaviour.
    """
    # Patch all I/O-heavy calls that App.__init__ triggers
    with patch("gui.app.load_workbook") as m_load_wb, \
         patch("gui.app.sync_profile") as m_sync, \
         patch("gui.app.save_profile_dual"), \
         patch("gui.app.detect_external_edits", return_value=False), \
         patch("gui.app.workbook_path") as m_wb_path, \
         patch("gui.app.ensure_profile_dirs"), \
         patch("gui.app.get_active_config") as m_cfg:

        # Configure profile config mock
        from helpers.profile.profile import ProfileConfig
        m_cfg.return_value = ProfileConfig(
            name="Test User",
            role="Engineer",
            company="TestCo",
            email="test@test.com",
            phone="555-0000",
            recipient_name="Boss",
            recipient_email="boss@test.com",
            workbook_filename="test.xlsx",
            daily_hours_budget=8.0,
        )

        # Mock workbook path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda self: "C:/fake/test.xlsx"
        m_wb_path.return_value = mock_path

        # Mock workbook load
        m_load_wb.return_value = MagicMock()

        # Mock profile sync to return a real profile
        from tests.gui.conftest import build_sample_profile
        m_sync.return_value = build_sample_profile()

        from gui.app import App
        app = App()
        app.withdraw()  # hide for tests
        pump()
        yield app
        try:
            app.destroy()
        except Exception:
            pass
        pump()


class TestAppPages:
    """Verify page instantiation."""

    def test_pages_dict_populated(self, app_instance):
        assert len(app_instance.pages) > 0

    def test_tasks_page_exists(self, app_instance):
        assert "tasks" in app_instance.pages

    def test_add_task_page_exists(self, app_instance):
        assert "add_task" in app_instance.pages

    def test_generate_page_exists(self, app_instance):
        assert "generate" in app_instance.pages

    def test_dashboard_page_exists(self, app_instance):
        assert "dashboard" in app_instance.pages


class TestAppNavigation:
    """Verify show_page navigation."""

    def test_show_page_tasks(self, app_instance, pump):
        with patch.object(app_instance, "_check_external_edits"):
            app_instance.show_page("tasks")
            pump()
            assert app_instance._active_page_key == "tasks"

    def test_show_page_dashboard(self, app_instance, pump):
        with patch.object(app_instance, "_check_external_edits"):
            app_instance.show_page("dashboard")
            pump()
            assert app_instance._active_page_key == "dashboard"

    def test_show_page_refreshes_target(self, app_instance, pump):
        with patch.object(app_instance, "_check_external_edits"):
            tasks_page = app_instance.pages["tasks"]
            with patch.object(tasks_page, "refresh") as m_refresh:
                app_instance.show_page("tasks")
                m_refresh.assert_called_once()


class TestAppSidebar:
    """Verify sidebar construction."""

    def test_sidebar_frame_exists(self, app_instance):
        assert app_instance._sidebar_frame is not None

    def test_nav_buttons_created(self, app_instance):
        assert len(app_instance._nav_btns) > 0
        assert "tasks" in app_instance._nav_btns


class TestAppDirtyState:
    """Verify autosave/dirty flag mechanism."""

    def test_mark_dirty_schedules_autosave(self, app_instance, pump):
        app_instance.mark_dirty()
        # After mark_dirty, autosave should be pending (after_id set)
        assert app_instance._autosave_id is not None
        # Cancel the scheduled autosave to avoid side effects
        app_instance.after_cancel(app_instance._autosave_id)
        app_instance._autosave_id = None
