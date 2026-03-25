"""Date helpers and filename generation utilities."""

from __future__ import annotations

from datetime import date, timedelta


def report_date() -> date:
    """Return today's date (used for stamping reports)."""
    return date.today()


def previous_monday(ref: date | None = None) -> date:
    """Return the Monday before (or equal to) the reference date."""
    if ref is None:
        ref = date.today()
    return ref - timedelta(days=ref.weekday())


def report_filename(prefix: str, ext: str) -> str:
    """Generate a date-stamped filename like 'Weekly_Report_2026-03-18.xlsx'."""
    return f"{prefix}_{report_date().isoformat()}.{ext}"


def file_prefix(name: str) -> str:
    """Return a filesystem-safe version of a name for file naming.

    Example: 'Liam Vanhooren' → 'Liam_Vanhooren'
    """
    return name.replace(" ", "_")
