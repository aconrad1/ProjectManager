"""Tests for SettingsPage — application info, paths, appearance."""
from __future__ import annotations

import customtkinter as ctk
from unittest.mock import patch

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def settings_page(tk_root, mock_app, pump):
    from gui.pages.settings_page import SettingsPage
    page = SettingsPage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestSettingsPageWidgets:
    """Verify that build() creates all expected widgets."""

    def test_profile_summary_label(self, settings_page):
        assert isinstance(settings_page._profile_summary, ctk.CTkLabel)

    def test_manage_profiles_button(self, settings_page):
        btn = find_widget(settings_page, ctk.CTkButton, text="Manage Profiles")
        assert btn is not None

    def test_open_yaml_button(self, settings_page):
        btn = find_widget(settings_page, ctk.CTkButton, text="Open YAML File")
        assert btn is not None

    def test_path_labels_created(self, settings_page):
        expected = ["Profile Dir", "Workbook", "Reports", "Exports", "Data", "Attachments"]
        labels = [label for label, _ in settings_page._path_labels]
        assert labels == expected

    def test_appearance_dropdown(self, settings_page):
        assert isinstance(settings_page._appearance_var, ctk.StringVar)
        assert settings_page._appearance_var.get() in ("Light", "Dark", "System")


class TestSettingsPageCallbacks:
    """Verify callback logic."""

    def test_manage_profiles_navigates(self, settings_page, pump):
        btn = find_widget(settings_page, ctk.CTkButton, text="Manage Profiles")
        btn.invoke()
        pump()
        settings_page.app.show_page.assert_called_with("profiles")

    def test_refresh_updates_summary(self, settings_page, pump):
        settings_page.refresh()
        pump()
        text = settings_page._profile_summary.cget("text")
        # Should contain something from profile module globals
        assert isinstance(text, str) and len(text) > 0

    def test_path_labels_populated_after_refresh(self, settings_page, pump):
        settings_page.refresh()
        pump()
        for label, lbl_widget in settings_page._path_labels:
            text = lbl_widget.cget("text")
            assert isinstance(text, str)
