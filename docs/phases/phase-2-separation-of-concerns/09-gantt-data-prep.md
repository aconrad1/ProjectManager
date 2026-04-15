# Task 9: Extract Gantt Data Preparation

**Audit ID**: C-04  
**Effort**: Medium  
**Phase**: 2 — Separation of Concerns

---

## Objective

Extract the data preparation portion of the Gantt page's `_render()` method (row building, date range computation, layout sizing) into helper functions. The page should call helpers for data, then handle only canvas drawing.

---

## Audit Reference

> **C-04: Gantt Page _render() Is 425 Lines**
>
> A single method that: computes date ranges, builds row data (filtering by category), configures canvas, draws month labels/week ticks/today line, draws row backgrounds/labels, draws bars with progress overlays, draws deadline markers and grid dividers. Bound to `<Configure>`, runs on every window resize.
>
> Fix: Extract data preparation into `helpers/reporting/gantt.py`.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/reporting/gantt.py` | **CREATE** — data preparation functions |
| `scripts/gui/pages/gantt_page.py` | **MODIFY** — call helpers for data prep, keep drawing code |

---

## Current Code

### gantt_page.py `_render()` — Data prep section (lines ~68–179)

**Row building (lines ~81–138):**
```python
rows: list[dict] = []
unscheduled_rows: list[dict] = []

for project in profile.projects:
    if cat_filter != "All" and project.category != cat_filter:
        continue

    dated_tasks = [t for t in project.tasks if t.start]
    undated_tasks = [t for t in project.tasks if not t.start]

    if dated_tasks:
        rows.append({
            "type": "project", "label": project.title,
            "category": project.category,
        })
        for task in dated_tasks:
            rows.append({
                "type": "task", "label": task.title, "item_id": task.id,
                "start": task.start, "end": task.end or task.start,
                "deadline": task.deadline, "status": task.status,
                "priority": task.priority,
            })
            for deliv in task.deliverables:
                if deliv.start:
                    rows.append({
                        "type": "deliverable", "label": deliv.title,
                        "item_id": deliv.id, "start": deliv.start,
                        "end": deliv.end or deliv.start,
                        "status": deliv.status, "pct": deliv.percent_complete,
                    })

    for task in undated_tasks:
        unscheduled_rows.append({
            "type": "task", "label": task.title, "item_id": task.id,
            "status": task.status, "priority": task.priority,
        })
        for deliv in task.deliverables:
            unscheduled_rows.append({
                "type": "deliverable", "label": deliv.title,
                "item_id": deliv.id, "status": deliv.status,
                "pct": getattr(deliv, "percent_complete", 0),
            })
```

**Date range computation (lines ~147–162):**
```python
all_dates: list[date] = []
for r in rows:
    if "start" in r:
        all_dates.append(r["start"])
        all_dates.append(r["end"])
        if r.get("deadline"):
            all_dates.append(r["deadline"])

if all_dates:
    range_start = min(all_dates) - timedelta(days=3)
    range_end = max(all_dates) + timedelta(days=10)
else:
    range_start = date.today() - timedelta(days=3)
    range_end = date.today() + timedelta(days=30)

total_days = (range_end - range_start).days + 1
```

**Unscheduled section merge (lines ~165–169):**
```python
if unscheduled_rows:
    rows.append({"type": "section", "label": "No Scheduled Start"})
    rows.extend(unscheduled_rows)
```

**Canvas drawing starts at line ~180** — month headers, row backgrounds, bars, markers.

---

## Required Changes

### Step 1: Create `helpers/reporting/gantt.py`

```python
"""Gantt chart data preparation — pure computation, no UI dependencies."""

from __future__ import annotations

from datetime import date, timedelta
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from helpers.domain.profile import Profile
    from helpers.domain.project import Project


@dataclass
class GanttRow:
    """A single row in the Gantt chart."""
    type: str           # "project", "task", "deliverable", "section"
    label: str
    item_id: str = ""
    category: str = ""
    start: date | None = None
    end: date | None = None
    deadline: date | None = None
    status: str = ""
    priority: int = 0
    pct: int = 0


@dataclass
class GanttData:
    """Complete data needed to render a Gantt chart."""
    rows: list[GanttRow]
    range_start: date
    range_end: date
    total_days: int


def build_gantt_rows(
    projects: list[Project], category: str = "All"
) -> tuple[list[GanttRow], list[GanttRow]]:
    """Build scheduled and unscheduled row lists from projects.
    
    Returns (scheduled_rows, unscheduled_rows).
    """
    from helpers.data.queries import filter_projects_by_category
    
    rows: list[GanttRow] = []
    unscheduled: list[GanttRow] = []

    for project in filter_projects_by_category(projects, category):
        dated_tasks = [t for t in project.tasks if t.start]
        undated_tasks = [t for t in project.tasks if not t.start]

        if dated_tasks:
            rows.append(GanttRow(
                type="project", label=project.title,
                category=project.category,
            ))
            for task in dated_tasks:
                rows.append(GanttRow(
                    type="task", label=task.title, item_id=task.id,
                    start=task.start, end=task.end or task.start,
                    deadline=task.deadline, status=task.status,
                    priority=task.priority,
                ))
                for deliv in task.deliverables:
                    if deliv.start:
                        rows.append(GanttRow(
                            type="deliverable", label=deliv.title,
                            item_id=deliv.id, start=deliv.start,
                            end=deliv.end or deliv.start,
                            status=deliv.status,
                            pct=deliv.percent_complete,
                        ))

        for task in undated_tasks:
            unscheduled.append(GanttRow(
                type="task", label=task.title, item_id=task.id,
                status=task.status, priority=task.priority,
            ))
            for deliv in task.deliverables:
                unscheduled.append(GanttRow(
                    type="deliverable", label=deliv.title,
                    item_id=deliv.id, status=deliv.status,
                    pct=getattr(deliv, "percent_complete", 0),
                ))

    return rows, unscheduled


def compute_date_range(
    rows: list[GanttRow], padding_before: int = 3, padding_after: int = 10
) -> tuple[date, date, int]:
    """Compute the date range from scheduled rows.
    
    Returns (range_start, range_end, total_days).
    """
    all_dates: list[date] = []
    for r in rows:
        if r.start:
            all_dates.append(r.start)
        if r.end:
            all_dates.append(r.end)
        if r.deadline:
            all_dates.append(r.deadline)

    if all_dates:
        range_start = min(all_dates) - timedelta(days=padding_before)
        range_end = max(all_dates) + timedelta(days=padding_after)
    else:
        range_start = date.today() - timedelta(days=padding_before)
        range_end = date.today() + timedelta(days=30)

    total_days = (range_end - range_start).days + 1
    return range_start, range_end, total_days


def prepare_gantt_data(
    projects: list[Project], category: str = "All"
) -> GanttData:
    """Full data preparation for Gantt rendering."""
    scheduled, unscheduled = build_gantt_rows(projects, category)
    range_start, range_end, total_days = compute_date_range(scheduled)

    # Merge unscheduled section
    all_rows = list(scheduled)
    if unscheduled:
        all_rows.append(GanttRow(type="section", label="No Scheduled Start"))
        all_rows.extend(unscheduled)

    return GanttData(
        rows=all_rows,
        range_start=range_start,
        range_end=range_end,
        total_days=total_days,
    )
```

### Step 2: Modify `scripts/gui/pages/gantt_page.py`

Replace the data prep section in `_render()` with a single call:

```python
from helpers.reporting.gantt import prepare_gantt_data, GanttData

def _render(self):
    c = self._canvas
    c.delete("all")

    profile = self.app.profile
    if not profile:
        # ... error render ...
        return

    cat_filter = self._filter_var.get()
    day_w = max(4, self._day_width_var.get())

    data = prepare_gantt_data(profile.projects, cat_filter)

    if not data.rows:
        c.create_text(200, 60, text="No tasks found.", ...)
        return

    self._rows = data.rows  # Store for context menu lookups

    # ... canvas drawing code continues using data.rows, data.range_start,
    #     data.range_end, data.total_days ...
```

Update row access from dict-style (`r["type"]`, `r["start"]`) to attribute-style (`r.type`, `r.start`) throughout the drawing code.

---

## Acceptance Criteria

1. `helpers/reporting/gantt.py` exists with `GanttRow`, `GanttData`, and `prepare_gantt_data()`
2. No row building, date range computation, or category filtering logic remains in `gantt_page.py`'s `_render()`
3. The Gantt chart renders identically (same rows, same date ranges, same layout)
4. `GanttRow` and `GanttData` are dataclasses — no UI dependencies
5. `prepare_gantt_data()` can be unit tested without a GUI
6. `pytest tests/gui/test_gantt_page.py` passes
7. Context menu and `_shift_date()` still work (they reference `self._rows`)

---

## Constraints

- Do NOT extract the canvas drawing code in this task — only data preparation
- The `_render()` method will still be long after this change — breaking up drawing is a separate effort
- Row dicts become `GanttRow` dataclasses — update all dict key access to attribute access in the drawing code
- Do NOT add new features (e.g., milestone rows) — strictly extract existing logic
- The `prepare_gantt_data()` function depends on `filter_projects_by_category()` from Task 8 — if Task 8 hasn't been done yet, inline the filter
