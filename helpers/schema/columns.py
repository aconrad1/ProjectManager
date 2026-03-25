"""Per-sheet column definitions — types, widths, foreign-key metadata.

All column schemas live here so that readers, writers, GUI, and CLI
can build headers, validate data, and auto-size columns from one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


# ── Column type enum ───────────────────────────────────────────────────────────

class ColumnType(Enum):
    STRING   = auto()
    INTEGER  = auto()
    FLOAT    = auto()
    DATE     = auto()
    FORMULA  = auto()
    PERCENT  = auto()


# ── Column descriptor ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Column:
    """Describes one column in a workbook sheet."""
    name: str
    col_type: ColumnType
    width: int = 18
    is_fk: bool = False
    fk_target: str | None = None        # "SheetName.ColumnName"
    nullable: bool = False
    choices: tuple[str, ...] | None = None   # data-validation list


# ── Projects columns ──────────────────────────────────────────────────────────

PROJECTS_COLUMNS: tuple[Column, ...] = (
    Column("Project ID",      ColumnType.STRING,  width=12),
    Column("Title",           ColumnType.STRING,  width=30),
    Column("Category",        ColumnType.STRING,  width=14, choices=("Weekly", "Ongoing", "Completed")),
    Column("Supervisor",      ColumnType.STRING,  width=20),
    Column("Site",            ColumnType.STRING,  width=18),
    Column("Description",     ColumnType.STRING,  width=40),
    Column("Status",          ColumnType.STRING,  width=14),
    Column("Priority",        ColumnType.INTEGER, width=10),
    Column("Start Date",      ColumnType.DATE,    width=14),
    Column("End Date",        ColumnType.DATE,    width=14, nullable=True),
    Column("Deadline",        ColumnType.DATE,    width=14, nullable=True),
    Column("Date Completed",  ColumnType.DATE,    width=16, nullable=True),
    Column("Notes",           ColumnType.STRING,  width=40, nullable=True),
)

# ── Tasks columns ─────────────────────────────────────────────────────────────

TASKS_COLUMNS: tuple[Column, ...] = (
    Column("Task ID",            ColumnType.STRING,  width=12),
    Column("Project ID",         ColumnType.STRING,  width=12, is_fk=True, fk_target="Projects.Project ID"),
    Column("Title",              ColumnType.STRING,  width=30),
    Column("Description",        ColumnType.STRING,  width=40),
    Column("Supervisor",         ColumnType.STRING,  width=20),
    Column("Site",               ColumnType.STRING,  width=18),
    Column("Status",             ColumnType.STRING,  width=14),
    Column("Priority",           ColumnType.INTEGER, width=10),
    Column("Start Date",         ColumnType.DATE,    width=14),
    Column("End Date",           ColumnType.DATE,    width=14, nullable=True),
    Column("Deadline",           ColumnType.DATE,    width=14, nullable=True),
    Column("Status Commentary",  ColumnType.STRING,  width=40, nullable=True),
    Column("Date Completed",     ColumnType.DATE,    width=16, nullable=True),
    Column("Scheduled Date",     ColumnType.DATE,    width=14, nullable=True),
)

# ── Deliverables columns ──────────────────────────────────────────────────────

DELIVERABLES_COLUMNS: tuple[Column, ...] = (
    Column("Deliverable ID",  ColumnType.STRING,  width=14),
    Column("Task ID",         ColumnType.STRING,  width=12, is_fk=True, fk_target="Tasks.Task ID"),
    Column("Title",           ColumnType.STRING,  width=30),
    Column("Description",     ColumnType.STRING,  width=40),
    Column("Status",          ColumnType.STRING,  width=14),
    Column("Start Date",      ColumnType.DATE,    width=14),
    Column("End Date",        ColumnType.DATE,    width=14, nullable=True),
    Column("Deadline",        ColumnType.DATE,    width=14, nullable=True),
    Column("% Complete",      ColumnType.PERCENT, width=12),
    Column("Time Allocated",  ColumnType.FLOAT,   width=14, nullable=True),
    Column("Time Spent",      ColumnType.FLOAT,   width=14, nullable=True),
)

# ── Timelines columns ─────────────────────────────────────────────────────────

TIMELINES_COLUMNS: tuple[Column, ...] = (
    Column("Item ID",         ColumnType.STRING,  width=14),
    Column("Item Type",       ColumnType.STRING,  width=14, choices=("Project", "Task", "Deliverable")),
    Column("Title",           ColumnType.FORMULA, width=30),
    Column("Parent ID",       ColumnType.STRING,  width=14, nullable=True),
    Column("Start Date",      ColumnType.FORMULA, width=14),
    Column("Duration (days)", ColumnType.FORMULA, width=14),
    Column("End Date",        ColumnType.FORMULA, width=14),
    Column("Deadline",        ColumnType.FORMULA, width=14),
    Column("Status",          ColumnType.FORMULA, width=14),
    Column("% Complete",      ColumnType.FORMULA, width=12),
    Column("Time Allocated",  ColumnType.FORMULA, width=14),
    Column("Time Spent",      ColumnType.FORMULA, width=14),
    Column("Scheduled Date",  ColumnType.FORMULA, width=14),
    Column("Milestones",      ColumnType.STRING,  width=30, nullable=True),
)

# ── Gantt chart columns ───────────────────────────────────────────────────────

GANTT_COLUMNS: tuple[Column, ...] = (
    Column("Item ID",  ColumnType.STRING,  width=14),
    Column("Title",    ColumnType.FORMULA, width=30),
    Column("Start",    ColumnType.FORMULA, width=14),
    Column("End",      ColumnType.FORMULA, width=14),
    Column("Status",   ColumnType.FORMULA, width=14),
    # Columns F+ are dynamic date columns — generated at runtime by gantt.py
)


# ── Lookup helpers ─────────────────────────────────────────────────────────────

from .sheets import (
    SHEET_PROJECTS, SHEET_TASKS, SHEET_DELIVERABLES,
    SHEET_TIMELINES, SHEET_GANTT, SHEET_OVERVIEW,
)

COLUMNS_BY_SHEET: dict[str, tuple[Column, ...]] = {
    SHEET_PROJECTS:     PROJECTS_COLUMNS,
    SHEET_TASKS:        TASKS_COLUMNS,
    SHEET_DELIVERABLES: DELIVERABLES_COLUMNS,
    SHEET_TIMELINES:    TIMELINES_COLUMNS,
    SHEET_GANTT:        GANTT_COLUMNS,
}


def headers_for(sheet_name: str) -> list[str]:
    """Return the ordered list of header strings for *sheet_name*."""
    cols = COLUMNS_BY_SHEET.get(sheet_name)
    if cols is None:
        raise KeyError(f"No column schema defined for sheet '{sheet_name}'")
    return [c.name for c in cols]


def column_index(sheet_name: str, column_name: str) -> int:
    """Return the 0-based column index for *column_name* in *sheet_name*."""
    cols = COLUMNS_BY_SHEET.get(sheet_name)
    if cols is None:
        raise KeyError(f"No column schema defined for sheet '{sheet_name}'")
    for i, c in enumerate(cols):
        if c.name == column_name:
            return i
    raise KeyError(f"Column '{column_name}' not found in sheet '{sheet_name}'")
