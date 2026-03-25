"""Prefixed sequential ID generation — P-001, T-001, D-001.

Each generator scans the ID column of the relevant sheet to find the
current maximum, then returns the next value.  All IDs are zero-padded
to three digits.
"""

from __future__ import annotations

import re

from openpyxl.worksheet.worksheet import Worksheet

# ── Prefix constants ───────────────────────────────────────────────────────────

PREFIX_PROJECT      = "P"
PREFIX_TASK         = "T"
PREFIX_DELIVERABLE  = "D"

_ID_PATTERN = re.compile(r"^([A-Z])-(\d{3,})$")


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_id(value: str) -> tuple[str, int]:
    """Parse 'P-003' → ('P', 3).  Raises ValueError on bad format."""
    m = _ID_PATTERN.match(str(value).strip())
    if not m:
        raise ValueError(f"Invalid ID format: {value!r}")
    return m.group(1), int(m.group(2))


def format_id(prefix: str, number: int) -> str:
    """Format ('P', 3) → 'P-003'."""
    return f"{prefix}-{number:03d}"


def _max_id_in_column(ws: Worksheet, col: int = 1, prefix: str = "") -> int:
    """Return the highest numeric part of IDs in column *col* (1-based).

    Skips the header row (row 1).  Returns 0 if no matching IDs are found.
    """
    max_num = 0
    for row in ws.iter_rows(min_row=2, max_col=col, min_col=col, values_only=True):
        cell_value = row[0]
        if cell_value is None:
            continue
        try:
            pfx, num = parse_id(str(cell_value))
        except ValueError:
            continue
        if prefix and pfx != prefix:
            continue
        max_num = max(max_num, num)
    return max_num


# ── Public generators ──────────────────────────────────────────────────────────

def next_project_id(ws: Worksheet) -> str:
    """Return the next available project ID (e.g. 'P-004')."""
    return format_id(PREFIX_PROJECT, _max_id_in_column(ws, col=1, prefix=PREFIX_PROJECT) + 1)


def next_task_id(ws: Worksheet) -> str:
    """Return the next available task ID (e.g. 'T-012')."""
    return format_id(PREFIX_TASK, _max_id_in_column(ws, col=1, prefix=PREFIX_TASK) + 1)


def next_deliverable_id(ws: Worksheet) -> str:
    """Return the next available deliverable ID (e.g. 'D-007')."""
    return format_id(PREFIX_DELIVERABLE, _max_id_in_column(ws, col=1, prefix=PREFIX_DELIVERABLE) + 1)


def id_exists(ws: Worksheet, target_id: str, col: int = 1) -> bool:
    """Return True if *target_id* already exists in column *col*."""
    target = str(target_id).strip()
    for row in ws.iter_rows(min_row=2, max_col=col, min_col=col, values_only=True):
        if row[0] is not None and str(row[0]).strip() == target:
            return True
    return False


# ── Domain-layer ID allocation (scan Profile tree, no worksheet needed) ────────

def _max_id_in_list(ids: list[str], prefix: str) -> int:
    """Return the highest numeric part from a list of ID strings."""
    max_num = 0
    for raw_id in ids:
        try:
            pfx, num = parse_id(str(raw_id))
        except ValueError:
            continue
        if pfx == prefix:
            max_num = max(max_num, num)
    return max_num


def next_project_id_from_profile(profile) -> str:
    """Return the next available project ID by scanning the Profile tree.

    Accepts a ``helpers.domain.profile.Profile`` instance.
    """
    ids = [p.id for p in profile.projects]
    return format_id(PREFIX_PROJECT, _max_id_in_list(ids, PREFIX_PROJECT) + 1)


def next_task_id_from_profile(profile) -> str:
    """Return the next available task ID by scanning the Profile tree."""
    ids = [t.id for t in profile.all_tasks]
    return format_id(PREFIX_TASK, _max_id_in_list(ids, PREFIX_TASK) + 1)


def next_deliverable_id_from_profile(profile) -> str:
    """Return the next available deliverable ID by scanning the Profile tree."""
    ids = [
        d.id
        for p in profile.projects
        for t in p.tasks
        for d in t.deliverables
    ]
    return format_id(PREFIX_DELIVERABLE, _max_id_in_list(ids, PREFIX_DELIVERABLE) + 1)
