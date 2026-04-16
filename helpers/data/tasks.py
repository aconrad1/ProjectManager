"""Cell-parsing helpers for workbook data.

The canonical domain model lives in ``helpers.domain.Task``.
This module provides shared parsing utilities used by readers and writers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

from helpers.data.queries import filter_projects_by_category
from helpers.config.loader import priority_range

if TYPE_CHECKING:
    from helpers.domain.profile import Profile


# ── Cell-parsing utilities ─────────────────────────────────────────────────────

def clean(value: object) -> str:
    """Convert a cell value to a stripped string."""
    if value is None:
        return ""
    return str(value).strip()


def parse_priority(value: object) -> int:
    """Safely parse a priority value to int (default max priority)."""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return priority_range()[1]


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


@dataclass
class TreeDeliverable:
    """Pre-computed deliverable row data for tree insertion."""

    id: str
    title: str
    status: str
    pct_str: str
    time_str: str
    task_id: str
    task_title: str


@dataclass
class TreeTask:
    """Pre-computed task row data for tree insertion."""

    id: str
    title: str
    supervisor: str
    site: str
    status: str
    priority: int
    scheduled: str
    time_str: str
    category: str
    project_id: str
    deliverables: list[TreeDeliverable]


@dataclass
class TreeProject:
    """Pre-computed project row data for tree insertion."""

    id: str
    title: str
    status: str
    category: str
    time_str: str
    tasks: list[TreeTask]


def build_tree_data(
    profile: Profile,
    category: str = "All",
    search: str = "",
) -> list[TreeProject]:
    """Build filtered, formatted tree data for the tasks treeview."""
    result: list[TreeProject] = []
    search_lower = search.lower().strip()

    for project in filter_projects_by_category(profile.projects, category):
        matching_tasks: list[TreeTask] = []

        for task in project.tasks:
            if search_lower:
                haystack = (
                    f"{task.title} {task.supervisor} {task.site} {task.status}"
                ).lower()
                if search_lower not in haystack:
                    continue

            deliverables: list[TreeDeliverable] = []
            for deliv in task.deliverables:
                d_alloc = f"{deliv.time_allocated:.1f}" if deliv.time_allocated else ""
                d_spent = f"{deliv.time_spent:.1f}" if deliv.time_spent else ""
                deliverables.append(
                    TreeDeliverable(
                        id=deliv.id,
                        title=deliv.title,
                        status=deliv.status,
                        pct_str=f"{deliv.percent_complete}%",
                        time_str=f"{d_alloc}/{d_spent}" if d_alloc or d_spent else "",
                        task_id=task.id,
                        task_title=task.title,
                    )
                )

            t_alloc = task.time_allocated_total
            t_spent = task.time_spent_total
            sched = task.scheduled_date.strftime("%m/%d") if task.scheduled_date else ""

            matching_tasks.append(
                TreeTask(
                    id=task.id,
                    title=task.title,
                    supervisor=task.supervisor,
                    site=task.site,
                    status=task.status,
                    priority=task.priority,
                    scheduled=sched,
                    time_str=f"{t_alloc:.1f}/{t_spent:.1f}" if t_alloc or t_spent else "",
                    category=project.category,
                    project_id=project.id,
                    deliverables=deliverables,
                )
            )

        if not matching_tasks and search_lower:
            continue

        alloc = project.time_allocated_total
        spent = project.time_spent_total
        result.append(
            TreeProject(
                id=project.id,
                title=project.title,
                status=project.status,
                category=project.category,
                time_str=f"{alloc:.1f}/{spent:.1f}" if alloc or spent else "",
                tasks=matching_tasks,
            )
        )

    return result
