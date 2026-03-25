"""helpers.schema — Workbook schema, column contracts, and cross-sheet relationships.

This is the single source of truth for:
  • Sheet names and metadata
  • Column definitions (headers, types, widths, foreign keys)
  • ID generation (P-001, T-001, D-001)
  • Relationship contracts and validation
"""

from __future__ import annotations

from helpers.schema.sheets import (                              # noqa: F401
    SHEET_OVERVIEW, SHEET_PROJECTS, SHEET_TASKS,
    SHEET_DELIVERABLES, SHEET_TIMELINES, SHEET_GANTT,
    ALL_SHEETS, DATA_SHEETS, SHEET_META,
    CATEGORY_WEEKLY, CATEGORY_ONGOING, CATEGORY_COMPLETED, ALL_CATEGORIES,
)
from helpers.schema.columns import (                             # noqa: F401
    PROJECTS_COLUMNS, TASKS_COLUMNS, DELIVERABLES_COLUMNS,
    TIMELINES_COLUMNS, GANTT_COLUMNS,
    COLUMNS_BY_SHEET,
    Column, ColumnType,
    headers_for, column_index,
)
from helpers.schema.ids import (                                 # noqa: F401
    next_project_id, next_task_id, next_deliverable_id,
    parse_id, format_id, id_exists,
    PREFIX_PROJECT, PREFIX_TASK, PREFIX_DELIVERABLE,
)
from helpers.schema.contracts import (                           # noqa: F401
    validate_foreign_keys, validate_ids,
    RELATIONSHIPS, Relationship,
)
