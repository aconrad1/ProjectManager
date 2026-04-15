# Task 8: Extract Category Filtering into Shared Query Helper

**Audit ID**: N-08  
**Effort**: Small  
**Phase**: 2 — Separation of Concerns

---

## Objective

Extract the duplicated category filtering pattern (`if cat_filter != "All" and project.category != cat_filter: continue`) into a shared helper function in `helpers/data/queries.py`. Replace the inline filtering in all affected pages.

---

## Audit Reference

> **N-08: Category Filtering Logic Duplicated Across 3 Pages**
>
> ```python
> # Appears in tasks_page.py, dashboard_page.py, gantt_page.py
> if cat_filter != "All" and project.category != cat_filter:
>     continue
> ```

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/data/queries.py` | **CREATE** — shared filtering function |
| `scripts/gui/pages/tasks_page.py` | **MODIFY** — use shared filter |
| `scripts/gui/pages/gantt_page.py` | **MODIFY** — use shared filter |

---

## Current Code

### tasks_page.py (line ~369 in `_populate_tree()`)

```python
for project in profile.projects:
    if cat_filter != "All" and project.category != cat_filter:
        continue
    # ... process project tasks ...
```

### gantt_page.py (line ~87 in `_render()`)

```python
for project in profile.projects:
    if cat_filter != "All" and project.category != cat_filter:
        continue
    # ... build gantt rows ...
```

### dashboard_page.py (line ~72 — uses a different pattern)

```python
weekly = profile.tasks_for_category("Weekly")
ongoing = profile.tasks_for_category("Ongoing")
completed = profile.tasks_for_category("Completed")
```

Note: dashboard_page uses `tasks_for_category()` (already centralized in Profile). Only tasks_page and gantt_page have the inline filter at the project level.

---

## Required Changes

### Step 1: Create `helpers/data/queries.py`

```python
"""Shared query helpers for filtering domain data."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from helpers.domain.project import Project


def filter_projects_by_category(
    projects: list[Project], category: str
) -> list[Project]:
    """Return projects matching *category*, or all if category is 'All'."""
    if category == "All":
        return list(projects)
    return [p for p in projects if p.category == category]
```

### Step 2: Update `scripts/gui/pages/tasks_page.py`

In `_populate_tree()`, replace the inline filter:

```python
from helpers.data.queries import filter_projects_by_category

# Before:
for project in profile.projects:
    if cat_filter != "All" and project.category != cat_filter:
        continue
    # ...

# After:
for project in filter_projects_by_category(profile.projects, cat_filter):
    # ...
```

### Step 3: Update `scripts/gui/pages/gantt_page.py`

In `_render()`, replace the inline filter:

```python
from helpers.data.queries import filter_projects_by_category

# Before:
for project in profile.projects:
    if cat_filter != "All" and project.category != cat_filter:
        continue
    # ...

# After:
for project in filter_projects_by_category(profile.projects, cat_filter):
    # ...
```

---

## Acceptance Criteria

1. `helpers/data/queries.py` exists with `filter_projects_by_category()`
2. No inline `if cat_filter != "All" and project.category != cat_filter` checks remain in tasks_page or gantt_page
3. Both pages import and use the shared function
4. Filtering behavior is identical (category == "All" returns everything; otherwise exact match)
5. `pytest tests/` passes
6. `helpers/data/queries.py` has no UI/tkinter imports

---

## Constraints

- Do NOT change dashboard_page.py — it already uses `profile.tasks_for_category()` which is a different pattern
- Do NOT add search filtering to this helper — that's page-specific (Task 12)
- Keep the function simple — one responsibility: filter projects by category
- The module lives in `helpers/data/` alongside `tasks.py`, `overview.py`, etc.
