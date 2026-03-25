"""Bidirectional field name ↔ domain attribute translation.

Excel columns use human-readable names (``"Status Commentary"``).
The domain model uses Python attribute names (``"commentary"``).

This module provides translation between the two conventions so that
both CLI (field-name dicts) and GUI (attr-name dicts) can feed into
a single mutation path.
"""

from __future__ import annotations

from typing import Literal

# ── Mapping tables ─────────────────────────────────────────────────────────────
# field_name (Excel column) → attr_name (domain attribute)

_PROJECT_FIELD_TO_ATTR: dict[str, str] = {
    "Title":          "title",
    "Category":       "category",
    "Supervisor":     "supervisor",
    "Site":           "site",
    "Description":    "description",
    "Status":         "status",
    "Priority":       "priority",
    "Notes":          "notes",
    "Start Date":     "start",
    "End Date":       "end",
    "Deadline":       "deadline",
    "Date Completed": "date_completed",
}

_TASK_FIELD_TO_ATTR: dict[str, str] = {
    "Title":             "title",
    "Supervisor":        "supervisor",
    "Site":              "site",
    "Description":       "description",
    "Status Commentary": "commentary",
    "Status":            "status",
    "Priority":          "priority",
    "Start Date":        "start",
    "End Date":          "end",
    "Deadline":          "deadline",
    "Date Completed":    "date_completed",
    "Scheduled Date":    "scheduled_date",
    # Aliases used by some callers
    "Project Supervisor": "supervisor",
    "Project Description": "description",
}

_DELIVERABLE_FIELD_TO_ATTR: dict[str, str] = {
    "Title":          "title",
    "Description":    "description",
    "Status":         "status",
    "Start Date":     "start",
    "End Date":       "end",
    "Deadline":       "deadline",
    "% Complete":     "percent_complete",
    "Time Allocated": "time_allocated",
    "Time Spent":     "time_spent",
}

# Reverse maps: attr_name → field_name
_PROJECT_ATTR_TO_FIELD = {v: k for k, v in _PROJECT_FIELD_TO_ATTR.items()}
_TASK_ATTR_TO_FIELD = {v: k for k, v in _TASK_FIELD_TO_ATTR.items()
                       if k not in ("Project Supervisor", "Project Description")}
_DELIVERABLE_ATTR_TO_FIELD = {v: k for k, v in _DELIVERABLE_FIELD_TO_ATTR.items()}

_FIELD_TO_ATTR = {
    "project":     _PROJECT_FIELD_TO_ATTR,
    "task":        _TASK_FIELD_TO_ATTR,
    "deliverable": _DELIVERABLE_FIELD_TO_ATTR,
}

_ATTR_TO_FIELD = {
    "project":     _PROJECT_ATTR_TO_FIELD,
    "task":        _TASK_ATTR_TO_FIELD,
    "deliverable": _DELIVERABLE_ATTR_TO_FIELD,
}

EntityType = Literal["project", "task", "deliverable"]


# ── Public API ─────────────────────────────────────────────────────────────────

def fields_to_attrs(data: dict, entity: EntityType) -> dict:
    """Translate Excel field-name keys to domain attribute keys.

    Keys already in attr format are passed through unchanged.
    Unknown keys are dropped.
    """
    mapping = _FIELD_TO_ATTR[entity]
    attr_values = _ATTR_TO_FIELD[entity]  # for detecting already-attr keys
    result: dict = {}
    for key, value in data.items():
        if key in mapping:
            result[mapping[key]] = value
        elif key in attr_values:
            # Already an attr name — pass through
            result[key] = value
    return result


def attrs_to_fields(data: dict, entity: EntityType) -> dict:
    """Translate domain attribute keys to Excel field-name keys.

    Keys already in field format are passed through unchanged.
    Unknown keys are dropped.
    """
    mapping = _ATTR_TO_FIELD[entity]
    field_values = _FIELD_TO_ATTR[entity]  # for detecting already-field keys
    result: dict = {}
    for key, value in data.items():
        if key in mapping:
            result[mapping[key]] = value
        elif key in field_values:
            # Already a field name — pass through
            result[key] = value
    return result


def normalize_to_attrs(data: dict, entity: EntityType) -> dict:
    """Normalize a dict that may contain mixed field/attr keys to all attrs.

    Accepts either format and returns pure attr-name keys.
    """
    return fields_to_attrs(data, entity)
