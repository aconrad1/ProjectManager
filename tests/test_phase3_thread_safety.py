"""Tests for Phase 3 — Thread Safety & Error Handling changes.

Covers:
- Task 20: _cleanup_task_files error handling
- Task 21: PDF subprocess logging
- Task 22: Hours input validation helper
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure scripts/ is importable for GUI page imports
_PROJECT = Path(__file__).resolve().parent.parent
_SCRIPTS = _PROJECT / "scripts"
for _p in (_PROJECT, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


# ── Task 20: _cleanup_task_files isolates failures ────────────────────────────

class TestCleanupTaskFiles:
    """Verify that _cleanup_task_files handles individual failures gracefully."""

    def test_cleanup_continues_after_notes_failure(self):
        from helpers.commands.domain_service import DomainService

        with patch("helpers.commands.domain_service.delete_notes", side_effect=OSError("disk error")), \
             patch("helpers.commands.domain_service.delete_link") as mock_link, \
             patch("helpers.commands.domain_service.delete_attachments") as mock_attach:
            # Should not raise
            DomainService._cleanup_task_files("T-001")
            mock_link.assert_called_once_with("T-001")
            mock_attach.assert_called_once_with("T-001")

    def test_cleanup_continues_after_link_failure(self):
        from helpers.commands.domain_service import DomainService

        with patch("helpers.commands.domain_service.delete_notes") as mock_notes, \
             patch("helpers.commands.domain_service.delete_link", side_effect=OSError("no link")), \
             patch("helpers.commands.domain_service.delete_attachments") as mock_attach:
            DomainService._cleanup_task_files("T-002")
            mock_notes.assert_called_once_with("T-002")
            mock_attach.assert_called_once_with("T-002")

    def test_cleanup_logs_warning_on_failure(self, caplog):
        from helpers.commands.domain_service import DomainService

        with patch("helpers.commands.domain_service.delete_notes", side_effect=OSError("boom")), \
             patch("helpers.commands.domain_service.delete_link"), \
             patch("helpers.commands.domain_service.delete_attachments"):
            with caplog.at_level(logging.WARNING):
                DomainService._cleanup_task_files("T-003")
            assert "Failed to clean up notes for T-003" in caplog.text

    def test_cleanup_succeeds_when_all_pass(self):
        from helpers.commands.domain_service import DomainService

        with patch("helpers.commands.domain_service.delete_notes") as mock_notes, \
             patch("helpers.commands.domain_service.delete_link") as mock_link, \
             patch("helpers.commands.domain_service.delete_attachments") as mock_attach:
            DomainService._cleanup_task_files("T-004")
            mock_notes.assert_called_once_with("T-004")
            mock_link.assert_called_once_with("T-004")
            mock_attach.assert_called_once_with("T-004")


# ── Task 21: PDF subprocess error logging ─────────────────────────────────────

class TestPdfSubprocessLogging:
    """Verify that PDF generation logs and re-raises subprocess errors."""

    def test_called_process_error_includes_stderr(self):
        from helpers.reporting.pdf import generate_pdf

        fake_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["chrome"],
            stderr=b"GPU process crashed",
        )
        with patch("helpers.reporting.pdf._find_chrome", return_value="/usr/bin/chromium"), \
             patch("helpers.reporting.pdf.subprocess.run", side_effect=fake_error), \
             patch("helpers.reporting.pdf.Path.unlink"):
            from pathlib import Path
            import tempfile
            dest = Path(tempfile.mkdtemp()) / "test.pdf"
            with pytest.raises(RuntimeError, match="GPU process crashed"):
                generate_pdf("# Test", dest)

    def test_timeout_raises_runtime_error(self):
        from helpers.reporting.pdf import generate_pdf

        with patch("helpers.reporting.pdf._find_chrome", return_value="/usr/bin/chromium"), \
             patch("helpers.reporting.pdf.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)), \
             patch("helpers.reporting.pdf.Path.unlink"):
            from pathlib import Path
            import tempfile
            dest = Path(tempfile.mkdtemp()) / "test.pdf"
            with pytest.raises(RuntimeError, match="timed out"):
                generate_pdf("# Test", dest)


# ── Task 22: Hours input validation ───────────────────────────────────────────

class TestHoursInputValidation:
    """Verify _parse_hours_field warns on invalid input."""

    def test_valid_float_returns_value(self):
        from gui.pages.profile_page import _parse_hours_field
        assert _parse_hours_field("daily_hours_budget", "6.5") == 6.5

    def test_empty_returns_default(self):
        from gui.pages.profile_page import _parse_hours_field
        assert _parse_hours_field("daily_hours_budget", "") == 8.0

    def test_invalid_string_returns_default_with_warning(self):
        from gui.pages.profile_page import _parse_hours_field
        with patch("gui.pages.profile_page.messagebox.showwarning") as mock_warn:
            result = _parse_hours_field("daily_hours_budget", "abc")
            assert result == 8.0
            mock_warn.assert_called_once()
            assert "abc" in mock_warn.call_args[0][1]

    def test_zero_returns_default_with_warning(self):
        from gui.pages.profile_page import _parse_hours_field
        with patch("gui.pages.profile_page.messagebox.showwarning") as mock_warn:
            result = _parse_hours_field("daily_hours_budget", "0")
            assert result == 8.0
            mock_warn.assert_called_once()

    def test_negative_returns_default_with_warning(self):
        from gui.pages.profile_page import _parse_hours_field
        with patch("gui.pages.profile_page.messagebox.showwarning") as mock_warn:
            result = _parse_hours_field("daily_hours_budget", "-5")
            assert result == 8.0
            mock_warn.assert_called_once()

    def test_weekly_hours_default(self):
        from gui.pages.profile_page import _parse_hours_field
        assert _parse_hours_field("weekly_hours_budget", "") == 40.0

    def test_weekly_hours_invalid(self):
        from gui.pages.profile_page import _parse_hours_field
        with patch("gui.pages.profile_page.messagebox.showwarning"):
            result = _parse_hours_field("weekly_hours_budget", "nope")
            assert result == 40.0
