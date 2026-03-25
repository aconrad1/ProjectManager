"""Tests for ProfilePage — profile CRUD and switching."""
from __future__ import annotations

import customtkinter as ctk
from unittest.mock import patch, MagicMock

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def profile_page(tk_root, mock_app, pump):
    from gui.pages.profile_page import ProfilePage
    page = ProfilePage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestProfilePageWidgets:
    """Verify that build() creates all expected widgets."""

    def test_list_frame_exists(self, profile_page):
        assert profile_page._list_frame is not None

    def test_detail_title_exists(self, profile_page):
        assert isinstance(profile_page._detail_title, ctk.CTkLabel)

    def test_entry_fields_created(self, profile_page):
        expected_keys = [
            "name", "role", "company", "email", "phone",
            "recipient_name", "recipient_email",
            "workbook_filename", "daily_hours_budget",
        ]
        for key in expected_keys:
            assert key in profile_page._entries, f"Missing entry: {key}"
            assert isinstance(profile_page._entries[key], ctk.CTkEntry)

    def test_new_profile_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="+ New Profile")
        assert btn is not None

    def test_delete_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="Delete")
        assert btn is not None

    def test_save_changes_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="Save Changes")
        assert btn is not None

    def test_switch_to_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="Switch To")
        assert btn is not None

    def test_import_workbook_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="Import Workbook…")
        assert btn is not None

    def test_export_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="Export Profile…")
        assert btn is not None

    def test_import_bundle_button(self, profile_page):
        btn = find_widget(profile_page, ctk.CTkButton, text="Import Profile…")
        assert btn is not None

    def test_status_label(self, profile_page):
        assert isinstance(profile_page._status_label, ctk.CTkLabel)


class TestProfilePageActions:
    """Verify profile actions."""

    def test_select_profile_populates_fields(self, profile_page, pump):
        with patch("gui.pages.profile_page.get_profiles", return_value=[
            {"name": "John Doe", "company": "TestCo", "role": "Eng",
             "email": "john@test.com", "phone": "555-1234",
             "recipient_name": "Boss", "recipient_email": "boss@test.com",
             "workbook_filename": "projects.xlsx", "daily_hours_budget": 8.0},
        ]), patch("gui.pages.profile_page.get_active_index", return_value=0):
            profile_page._select_profile(0)
            pump()
            assert profile_page._entries["name"].get() == "John Doe"
            assert profile_page._entries["company"].get() == "TestCo"

    def test_save_validates_name(self, profile_page, pump):
        profile_page._selected_idx = 0
        profile_page._entries["name"].delete(0, "end")
        profile_page._entries["company"].insert(0, "Co")
        with patch("gui.pages.profile_page.get_profiles", return_value=[{}]), \
             patch("tkinter.messagebox.showwarning") as m_warn:
            profile_page._save_profile()
            m_warn.assert_called_once()

    def test_save_validates_company(self, profile_page, pump):
        profile_page._selected_idx = 0
        profile_page._entries["name"].delete(0, "end")
        profile_page._entries["name"].insert(0, "Test")
        profile_page._entries["company"].delete(0, "end")
        with patch("gui.pages.profile_page.get_profiles", return_value=[{}]), \
             patch("tkinter.messagebox.showwarning") as m_warn:
            profile_page._save_profile()
            m_warn.assert_called_once()

    def test_set_status_updates_label(self, profile_page, pump):
        profile_page._set_status("All good!", ok=True)
        pump()
        assert profile_page._status_label.cget("text") == "All good!"

    def test_delete_no_selection_does_nothing(self, profile_page, pump):
        profile_page._selected_idx = None
        # Should not raise
        profile_page._delete_profile()

    def test_new_profile_opens_dialog(self, profile_page, pump):
        with patch("gui.pages.profile_page._NewProfileDialog") as MockDialog:
            profile_page._new_profile()
            MockDialog.assert_called_once()
