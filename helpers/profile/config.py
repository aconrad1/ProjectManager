"""Derived configuration values — paths and constants that depend on the active profile.

Instead of fixed module-level constants (which break on profile switch),
callers use the functions here to get the *current* value.
"""

from __future__ import annotations

from pathlib import Path

from helpers.io.paths import BASE_DIR, PROFILES_DIR, _safe_dir_name
from helpers.io import paths as _paths
from helpers.profile.profile import get_active_config


# ── Dynamic path helpers (depend on active profile at call time) ───────────────

def workbook_path() -> Path:
    """Full path to the active profile's workbook inside its profile dir."""
    cfg = get_active_config()
    return _paths.workbook_path(cfg.company, cfg.workbook_filename)


def profile_dir() -> Path:
    cfg = get_active_config()
    return _paths.profile_dir(cfg.company)


def data_dir() -> Path:
    cfg = get_active_config()
    return _paths.data_dir(cfg.company)


def attachments_dir() -> Path:
    cfg = get_active_config()
    return _paths.attachments_dir(cfg.company)


def notes_file() -> Path:
    cfg = get_active_config()
    return _paths.notes_file(cfg.company)


def links_file() -> Path:
    cfg = get_active_config()
    return _paths.links_file(cfg.company)


def reports_dir() -> Path:
    cfg = get_active_config()
    return _paths.reports_dir(cfg.company)


def exports_dir() -> Path:
    cfg = get_active_config()
    return _paths.exports_dir(cfg.company)


def markdown_dir() -> Path:
    cfg = get_active_config()
    return _paths.markdown_dir(cfg.company)


def pdf_dir() -> Path:
    cfg = get_active_config()
    return _paths.pdf_dir(cfg.company)
