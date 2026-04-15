"""Domain validation layer.

Provides lightweight validators for projects, tasks, and deliverables.
Each validator returns a list of error strings (empty = valid).

Usage::

    from helpers.validation import validate_task, ValidationError

    errors = validate_task(data)
    if errors:
        raise ValidationError(errors)
"""

from __future__ import annotations

from datetime import date
from typing import Any


class ValidationError(Exception):
    """Raised when domain validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(format_errors(errors))


def format_errors(errors: list[str]) -> str:
    """Format a list of validation errors into a user-friendly string."""
    if len(errors) == 1:
        return errors[0]
    return "Validation errors:\n" + "\n".join(f"  • {e}" for e in errors)


# ── Project ────────────────────────────────────────────────────────────────────

_VALID_CATEGORIES = {"Weekly", "Ongoing", "Completed"}

def validate_project(data: dict[str, Any]) -> list[str]:
    """Validate project creation/edit data. Returns list of error strings."""
    errors: list[str] = []
    title = data.get("title", "")
    if not title or not str(title).strip():
        errors.append("Project title is required.")
    category = data.get("category")
    if category and category not in _VALID_CATEGORIES:
        errors.append(f"Invalid category '{category}'. Must be one of: {', '.join(sorted(_VALID_CATEGORIES))}.")
    priority = data.get("priority")
    if priority is not None:
        if not isinstance(priority, int) or not (1 <= priority <= 5):
            errors.append("Priority must be an integer between 1 and 5.")
    _check_date_range(data, errors)
    return errors


# ── Task ───────────────────────────────────────────────────────────────────────

_VALID_STATUSES = {
    "Not Started", "In Progress", "On Track", "Ongoing",
    "Recurring", "On Hold", "Completed",
}

def validate_task(data: dict[str, Any]) -> list[str]:
    """Validate task creation/edit data. Returns list of error strings."""
    errors: list[str] = []
    title = data.get("title", "")
    if not title or not str(title).strip():
        errors.append("Task title is required.")
    status = data.get("status")
    if status and status not in _VALID_STATUSES:
        errors.append(f"Invalid status '{status}'. Must be one of: {', '.join(sorted(_VALID_STATUSES))}.")
    priority = data.get("priority")
    if priority is not None:
        if not isinstance(priority, int) or not (1 <= priority <= 5):
            errors.append("Priority must be an integer between 1 and 5.")
    _check_date_range(data, errors)
    return errors


# ── Deliverable ────────────────────────────────────────────────────────────────

def validate_deliverable(data: dict[str, Any]) -> list[str]:
    """Validate deliverable creation/edit data. Returns list of error strings."""
    errors: list[str] = []
    title = data.get("title", "")
    if not title or not str(title).strip():
        errors.append("Deliverable title is required.")
    pct = data.get("percent_complete")
    if pct is not None:
        try:
            pct_val = float(pct)
            if not (0 <= pct_val <= 100):
                errors.append("Percent complete must be between 0 and 100.")
        except (TypeError, ValueError):
            errors.append("Percent complete must be a number.")
    for field in ("time_allocated", "time_spent"):
        val = data.get(field)
        if val is not None:
            try:
                if float(val) < 0:
                    errors.append(f"{field.replace('_', ' ').title()} cannot be negative.")
            except (TypeError, ValueError):
                errors.append(f"{field.replace('_', ' ').title()} must be a number.")
    _check_date_range(data, errors)
    return errors


# ── Helpers ────────────────────────────────────────────────────────────────────

def _check_date_range(data: dict[str, Any], errors: list[str]) -> None:
    """Append an error if start > end or start > deadline."""
    start = data.get("start")
    end = data.get("end")
    deadline = data.get("deadline")
    if isinstance(start, date) and isinstance(end, date) and start > end:
        errors.append("Start date cannot be after end date.")
    if isinstance(start, date) and isinstance(deadline, date) and start > deadline:
        errors.append("Start date cannot be after deadline.")


# ── Schedule config ────────────────────────────────────────────────────────────

_VALID_WEEK_STARTS = {"monday", "tuesday", "wednesday", "thursday",
                      "friday", "saturday", "sunday"}

def validate_schedule_config(config: dict[str, Any]) -> list[str]:
    """Validate scheduler configuration from ``defaults.json``.

    Checks ``default_time_allocated_hours``, ``max_tasks_per_priority_slot``,
    ``week_start_day``, and budget-related values.
    """
    errors: list[str] = []
    dta = config.get("default_time_allocated_hours")
    if dta is not None:
        try:
            if float(dta) <= 0:
                errors.append("default_time_allocated_hours must be > 0.")
        except (TypeError, ValueError):
            errors.append("default_time_allocated_hours must be a number.")

    mtps = config.get("max_tasks_per_priority_slot")
    if mtps is not None:
        if not isinstance(mtps, int) or mtps < 1:
            errors.append("max_tasks_per_priority_slot must be a positive integer.")

    wsd = config.get("week_start_day")
    if wsd is not None and str(wsd).strip().lower() not in _VALID_WEEK_STARTS:
        errors.append(f"week_start_day must be one of: {', '.join(sorted(_VALID_WEEK_STARTS))}.")

    return errors


def validate_budget(daily: float | None, weekly: float | None) -> list[str]:
    """Validate time budget values from the profile."""
    errors: list[str] = []
    if daily is not None and daily <= 0:
        errors.append("daily_hours_budget must be > 0.")
    if weekly is not None and weekly <= 0:
        errors.append("weekly_hours_budget must be > 0.")
    if daily and weekly and daily > weekly:
        errors.append("daily_hours_budget cannot exceed weekly_hours_budget.")
    return errors
