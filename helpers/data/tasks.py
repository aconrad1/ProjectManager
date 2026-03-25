"""Cell-parsing helpers for workbook data.

The canonical domain model lives in ``helpers.domain.Task``.
This module provides shared parsing utilities used by readers and writers.
"""

from __future__ import annotations

from datetime import date, datetime


# ── Cell-parsing utilities ─────────────────────────────────────────────────────

def clean(value: object) -> str:
    """Convert a cell value to a stripped string."""
    if value is None:
        return ""
    return str(value).strip()


def parse_priority(value: object) -> int:
    """Safely parse a priority value to int (default 5)."""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 5


def parse_date(value: object) -> date | None:
    """Parse a date cell value to ``date | None``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def parse_percent(value: object) -> int:
    """Parse a percentage cell value to int 0-100 (default 0)."""
    if value is None:
        return 0
    try:
        v = float(value)
        # openpyxl may return 0.75 for 75%
        if 0 < v <= 1:
            return int(round(v * 100))
        return int(round(v))
    except (TypeError, ValueError):
        return 0


def parse_float(value: object) -> float | None:
    """Parse a numeric cell value to float, returning None if empty/invalid."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
