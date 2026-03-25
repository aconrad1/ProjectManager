"""Centralised path definitions for the project.

All directory constants are derived from the project root (two levels above
``scripts/``).  Import paths from here instead of re-deriving them.

Profile folder schema
---------------------
Each profile lives under ``profiles/<company>/`` and has a fixed layout::

    profiles/
        user_profile.yaml
        _template.xlsx
        <company>/
            <workbook_filename>
            attachments/
            data/
                task_notes.json
                task_links.json
            reports/          ← xlsx snapshots
            exports/
                markdown/
                pdf/
"""

from __future__ import annotations

from pathlib import Path

# ── Profile folder sub-directories (the "schema") ─────────────────────────────
PROFILE_SUBDIRS: tuple[str, ...] = (
    "attachments",
    "data",
    "reports",
    "exports",
    "exports/markdown",
    "exports/pdf",
)


def _safe_dir_name(name: str) -> str:
    """Return a filesystem-safe directory name."""
    cleaned = "".join(c if c not in '<>:"/\\|?*' else "_" for c in name).strip()
    return cleaned or "Default"


# Resolved once at import time.
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

PROFILES_DIR: Path = BASE_DIR / "profiles"

PROFILE_PATH: Path = PROFILES_DIR / "user_profile.yaml"

TEMPLATE_WORKBOOK: Path = PROFILES_DIR / "_template.xlsx"


# ── Per-profile path helpers ──────────────────────────────────────────────────

def profile_dir(company: str) -> Path:
    """Return ``profiles/<safe-company-name>/``."""
    return PROFILES_DIR / _safe_dir_name(company)


def workbook_path(company: str, filename: str) -> Path:
    return profile_dir(company) / filename


def data_dir(company: str) -> Path:
    return profile_dir(company) / "data"


def attachments_dir(company: str) -> Path:
    return profile_dir(company) / "attachments"


def notes_file(company: str) -> Path:
    return data_dir(company) / "task_notes.json"


def links_file(company: str) -> Path:
    return data_dir(company) / "task_links.json"


def reports_dir(company: str) -> Path:
    return profile_dir(company) / "reports"


def exports_dir(company: str) -> Path:
    return profile_dir(company) / "exports"


def markdown_dir(company: str) -> Path:
    return exports_dir(company) / "markdown"


def pdf_dir(company: str) -> Path:
    return exports_dir(company) / "pdf"
