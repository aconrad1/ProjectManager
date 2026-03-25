"""Derived configuration values — paths and constants that depend on the active profile.

Instead of fixed module-level constants (which break on profile switch),
callers use the functions here to get the *current* value.
"""

from __future__ import annotations

from pathlib import Path

from helpers.io.paths import BASE_DIR, PROFILES_DIR, _safe_dir_name
from helpers.io import paths as _paths
import helpers.profile.profile as _prof


# ── Dynamic path helpers (depend on active profile at call time) ───────────────

def workbook_path() -> Path:
    """Full path to the active profile's workbook inside its profile dir."""
    return _paths.workbook_path(_prof.USER_COMPANY, _prof.WORKBOOK_FILENAME)


def profile_dir() -> Path:
    return _paths.profile_dir(_prof.USER_COMPANY)


def data_dir() -> Path:
    return _paths.data_dir(_prof.USER_COMPANY)


def attachments_dir() -> Path:
    return _paths.attachments_dir(_prof.USER_COMPANY)


def notes_file() -> Path:
    return _paths.notes_file(_prof.USER_COMPANY)


def links_file() -> Path:
    return _paths.links_file(_prof.USER_COMPANY)


def reports_dir() -> Path:
    return _paths.reports_dir(_prof.USER_COMPANY)


def exports_dir() -> Path:
    return _paths.exports_dir(_prof.USER_COMPANY)


def markdown_dir() -> Path:
    return _paths.markdown_dir(_prof.USER_COMPANY)


def pdf_dir() -> Path:
    return _paths.pdf_dir(_prof.USER_COMPANY)
