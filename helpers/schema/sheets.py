"""Sheet name constants and metadata for the 6-sheet workbook layout.

Every module that needs a sheet name imports from here — no more
duplicated string literals scattered across the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── Sheet name constants ───────────────────────────────────────────────────────

SHEET_OVERVIEW      = "Overview"
SHEET_PROJECTS      = "Projects"
SHEET_TASKS         = "Tasks"
SHEET_DELIVERABLES  = "Deliverables"
SHEET_TIMELINES     = "Timelines"
SHEET_GANTT         = "Gantt Chart"

# Ordered list — the order sheets appear in the workbook
ALL_SHEETS: tuple[str, ...] = (
    SHEET_OVERVIEW,
    SHEET_PROJECTS,
    SHEET_TASKS,
    SHEET_DELIVERABLES,
    SHEET_TIMELINES,
    SHEET_GANTT,
)

# Sheets that hold editable data rows (used by readers / writers)
DATA_SHEETS: tuple[str, ...] = (
    SHEET_PROJECTS,
    SHEET_TASKS,
    SHEET_DELIVERABLES,
)


# ── Sheet metadata ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SheetMeta:
    """Describes a single workbook sheet."""
    name: str
    frozen_pane: str | None = None   # e.g. "A2" freezes header row
    tab_color: str | None = None     # hex without '#'


SHEET_META: dict[str, SheetMeta] = {
    SHEET_OVERVIEW:     SheetMeta(SHEET_OVERVIEW,     frozen_pane=None, tab_color="003DA5"),
    SHEET_PROJECTS:     SheetMeta(SHEET_PROJECTS,     frozen_pane="A2", tab_color="336BBF"),
    SHEET_TASKS:        SheetMeta(SHEET_TASKS,        frozen_pane="A2", tab_color="336BBF"),
    SHEET_DELIVERABLES: SheetMeta(SHEET_DELIVERABLES, frozen_pane="A2", tab_color="336BBF"),
    SHEET_TIMELINES:    SheetMeta(SHEET_TIMELINES,    frozen_pane="A2", tab_color="B3CDE3"),
    SHEET_GANTT:        SheetMeta(SHEET_GANTT,        frozen_pane="F2", tab_color="E6EFF8"),
}


# ── Project category values ────────────────────────────────────────────────────

CATEGORY_WEEKLY    = "Weekly"
CATEGORY_ONGOING   = "Ongoing"
CATEGORY_COMPLETED = "Completed"

ALL_CATEGORIES: tuple[str, ...] = (
    CATEGORY_WEEKLY,
    CATEGORY_ONGOING,
    CATEGORY_COMPLETED,
)
