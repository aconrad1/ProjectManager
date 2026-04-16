"""Gantt chart data preparation (pure computation, no UI dependencies)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from helpers.data.queries import filter_projects_by_category

if TYPE_CHECKING:
    from helpers.domain.project import Project


@dataclass
class GanttRow:
    """A single render row in the Gantt chart."""

    type: str
    label: str
    item_id: str = ""
    category: str = ""
    start: date | None = None
    end: date | None = None
    deadline: date | None = None
    status: str = ""
    priority: int = 0
    pct: int = 0

    # Backward-compatible dict-like access for existing tests/callers.
    def __getitem__(self, key: str):
        return getattr(self, key)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return getattr(self, key, None) is not None


@dataclass
class GanttData:
    """Prepared rows plus time range metadata for rendering."""

    rows: list[GanttRow]
    range_start: date
    range_end: date
    total_days: int


def build_gantt_rows(
    projects: list[Project], category: str = "All"
) -> tuple[list[GanttRow], list[GanttRow]]:
    """Build scheduled and unscheduled rows from projects."""
    scheduled: list[GanttRow] = []
    unscheduled: list[GanttRow] = []

    for project in filter_projects_by_category(projects, category):
        dated_tasks = [task for task in project.tasks if task.start]
        undated_tasks = [task for task in project.tasks if not task.start]

        if dated_tasks:
            scheduled.append(
                GanttRow(type="project", label=project.title, category=project.category)
            )
            for task in dated_tasks:
                scheduled.append(
                    GanttRow(
                        type="task",
                        label=task.title,
                        item_id=task.id,
                        start=task.start,
                        end=task.end or task.start,
                        deadline=task.deadline,
                        status=task.status,
                        priority=task.priority,
                    )
                )
                for deliv in task.deliverables:
                    if deliv.start:
                        scheduled.append(
                            GanttRow(
                                type="deliverable",
                                label=deliv.title,
                                item_id=deliv.id,
                                start=deliv.start,
                                end=deliv.end or deliv.start,
                                status=deliv.status,
                                pct=deliv.percent_complete,
                            )
                        )

        for task in undated_tasks:
            unscheduled.append(
                GanttRow(
                    type="task",
                    label=task.title,
                    item_id=task.id,
                    status=task.status,
                    priority=task.priority,
                )
            )
            for deliv in task.deliverables:
                unscheduled.append(
                    GanttRow(
                        type="deliverable",
                        label=deliv.title,
                        item_id=deliv.id,
                        status=deliv.status,
                        pct=getattr(deliv, "percent_complete", 0),
                    )
                )

    return scheduled, unscheduled


def compute_date_range(
    rows: list[GanttRow], padding_before: int = 3, padding_after: int = 10
) -> tuple[date, date, int]:
    """Compute render date range and total day count from scheduled rows."""
    all_dates: list[date] = []
    for row in rows:
        if row.start:
            all_dates.append(row.start)
        if row.end:
            all_dates.append(row.end)
        if row.deadline:
            all_dates.append(row.deadline)

    if all_dates:
        range_start = min(all_dates) - timedelta(days=padding_before)
        range_end = max(all_dates) + timedelta(days=padding_after)
    else:
        range_start = date.today() - timedelta(days=padding_before)
        range_end = date.today() + timedelta(days=30)

    total_days = (range_end - range_start).days + 1
    return range_start, range_end, total_days


def prepare_gantt_data(projects: list[Project], category: str = "All") -> GanttData:
    """Build all Gantt render data from profile projects."""
    scheduled, unscheduled = build_gantt_rows(projects, category)
    range_start, range_end, total_days = compute_date_range(scheduled)

    rows = list(scheduled)
    if unscheduled:
        rows.append(GanttRow(type="section", label="No Scheduled Start"))
        rows.extend(unscheduled)

    return GanttData(
        rows=rows,
        range_start=range_start,
        range_end=range_end,
        total_days=total_days,
    )
