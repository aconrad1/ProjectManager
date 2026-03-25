"""Tests for GeneratePage — report generation buttons and output log."""
from __future__ import annotations

import customtkinter as ctk
from unittest.mock import patch, MagicMock

import pytest

from gui_test_helpers import find_widget


@pytest.fixture
def generate_page(tk_root, mock_app, pump):
    from gui.pages.generate_page import GeneratePage
    page = GeneratePage(tk_root, app=mock_app)
    page.pack(fill="both", expand=True)
    pump()
    yield page
    page.pack_forget()
    page.destroy()
    pump()


class TestGeneratePageWidgets:
    """Verify that build() creates all expected widgets."""

    def test_save_workbook_button(self, generate_page):
        btn = find_widget(generate_page, ctk.CTkButton, text="Save Workbook")
        assert btn is not None

    def test_generate_reports_button(self, generate_page):
        btn = find_widget(generate_page, ctk.CTkButton, text="Generate Reports")
        assert btn is not None

    def test_save_and_close_button(self, generate_page):
        btn = find_widget(generate_page, ctk.CTkButton, text="Save & Close")
        assert btn is not None

    def test_open_latest_button(self, generate_page):
        btn = find_widget(generate_page, ctk.CTkButton, text="Open Latest Report")
        assert btn is not None

    def test_email_report_button(self, generate_page):
        btn = find_widget(generate_page, ctk.CTkButton, text="Email Report")
        assert btn is not None

    def test_log_textbox_present(self, generate_page):
        assert isinstance(generate_page._log, ctk.CTkTextbox)


class TestGeneratePageCallbacks:
    """Verify callback logic."""

    def test_log_write_appends_text(self, generate_page, pump):
        generate_page.log_write("hello world")
        pump()
        generate_page._log.configure(state="normal")
        content = generate_page._log.get("1.0", "end").strip()
        generate_page._log.configure(state="disabled")
        assert "hello world" in content

    def test_log_clear_empties_log(self, generate_page, pump):
        generate_page.log_write("some text")
        pump()
        generate_page._log_clear()
        pump()
        generate_page._log.configure(state="normal")
        content = generate_page._log.get("1.0", "end").strip()
        generate_page._log.configure(state="disabled")
        assert content == ""

    def test_save_workbook_calls_save_state(self, generate_page, pump):
        with patch("helpers.commands.utilities.save_workbook_cmd"):
            generate_page._save_workbook()
            generate_page.app.save_state.assert_called_once()

    def test_generate_reports_sets_flag(self, generate_page, pump):
        with patch("gui.pages.generate_page.threading.Thread") as MockThread:
            mock_thread = MagicMock()
            MockThread.return_value = mock_thread
            generate_page._generate_reports()
            assert generate_page._generating is True
            MockThread.assert_called_once()
            mock_thread.start.assert_called_once()

    def test_open_latest_no_reports_shows_info(self, generate_page, pump):
        with patch("gui.pages.generate_page.find_latest", return_value=None), \
             patch("tkinter.messagebox.showinfo") as m_info:
            generate_page._open_latest()
            m_info.assert_called_once()

    def test_open_latest_with_report_opens(self, generate_page, pump):
        fake_path = "C:/fake/report.pdf"
        with patch("gui.pages.generate_page.find_latest", return_value=fake_path), \
             patch("gui.pages.generate_page.open_path") as m_open:
            generate_page._open_latest()
            m_open.assert_called_once_with(fake_path)
