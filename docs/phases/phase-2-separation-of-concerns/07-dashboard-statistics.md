# Task 7: Extract Dashboard Statistics into helpers/data/

**Audit ID**: C-05  
**Effort**: Medium  
**Phase**: 2 — Separation of Concerns

---

## Objective

Extract all statistics computation from `dashboard_page.py`'s `refresh()` method into a new `helpers/data/dashboard.py` module. The page should only call helper functions and build widgets — no `Counter`, no filtering, no sorting inline.

---

## Audit Reference

> **C-05: Dashboard refresh() Is 220 Lines of Stats + UI**
>
> Computes priority breakdowns (`Counter`), site distributions, recently completed items, and top-priority tasks — then immediately renders widgets for each. Business logic and UI creation are interleaved.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/data/dashboard.py` | **CREATE** — statistics computation functions |
| `scripts/gui/pages/dashboard_page.py` | **MODIFY** — call helpers, remove inline computation |

---

## Current Code

### dashboard_page.py `refresh()` — Interleaved business logic (lines ~68–210)

**Stat cards (line ~83):**
```python
stats = [
    ("Weekly Tasks", len(weekly), AG_DARK),
    ("Ongoing Projects", len(ongoing), AG_MID),
    ("Completed", len(completed), "#27ae60"),
    ("Total Active", len(all_active), "#2c3e50"),
]
```

**Priority breakdown (line ~99):**
```python
prio_counts = Counter(t.priority for t in all_active)
total_active = len(all_active) or 1
prio_colors = {1: "#c0392b", 2: "#e67e22", 3: "#f39c12", 4: "#7f8c8d", 5: "#bdc3c7"}
```

**Recently completed (line ~122):**
```python
recent_completed = [
    t for t in completed
    if t.date_completed and t.date_completed >= week_ago
]
```

**Site distribution (line ~157):**
```python
site_counts: Counter = Counter()
for t in all_active:
    sites = [s.strip() for s in t.site.replace("&", ",").split(",") if s.strip()]
    if not sites or sites == ["N/A"]:
        sites = ["Unassigned"]
    for s in sites:
        site_counts[s] += 1
```

**Top-priority spotlight (line ~194):**
```python
spotlight = sorted([t for t in all_active if t.priority <= 2],
                   key=lambda t: t.priority)[:6]
```

---

## Required Changes

### Step 1: Create `helpers/data/dashboard.py`

```python
"""Dashboard statistics — pure computation, no UI dependencies."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from helpers.domain.task import Task
    from helpers.domain.profile import Profile


def compute_stat_cards(profile: Profile) -> list[tuple[str, int]]:
    """Return [(label, count), ...] for the 4 dashboard stat cards."""
    weekly = profile.tasks_for_category("Weekly")
    ongoing = profile.tasks_for_category("Ongoing")
    completed = profile.tasks_for_category("Completed")
    active = weekly + ongoing
    return [
        ("Weekly Tasks", len(weekly)),
        ("Ongoing Projects", len(ongoing)),
        ("Completed", len(completed)),
        ("Total Active", len(active)),
    ]


def compute_priority_breakdown(tasks: list[Task]) -> dict[int, int]:
    """Return {priority: count} for active tasks."""
    return dict(Counter(t.priority for t in tasks))


def compute_recently_completed(
    tasks: list[Task], since: date | None = None
) -> list[Task]:
    """Return tasks completed since *since* (default: 7 days ago), newest first."""
    if since is None:
        since = date.today() - timedelta(days=7)
    return sorted(
        [t for t in tasks if t.date_completed and t.date_completed >= since],
        key=lambda t: t.date_completed,
        reverse=True,
    )


def compute_site_distribution(
    tasks: list[Task], top_n: int = 8
) -> list[tuple[str, int]]:
    """Return [(site_name, count), ...] sorted by frequency, capped at *top_n*."""
    site_counts: Counter[str] = Counter()
    for t in tasks:
        sites = [s.strip() for s in t.site.replace("&", ",").split(",") if s.strip()]
        if not sites or sites == ["N/A"]:
            sites = ["Unassigned"]
        for s in sites:
            site_counts[s] += 1
    return site_counts.most_common(top_n)


def compute_spotlight_tasks(
    tasks: list[Task], max_priority: int = 2, limit: int = 6
) -> list[Task]:
    """Return top-priority tasks (P1 & P2), sorted by priority, capped at *limit*."""
    return sorted(
        [t for t in tasks if t.priority <= max_priority],
        key=lambda t: t.priority,
    )[:limit]
```

### Step 2: Modify `scripts/gui/pages/dashboard_page.py`

Replace inline computation in `refresh()` with calls to the new helpers:

```python
from helpers.data.dashboard import (
    compute_stat_cards,
    compute_priority_breakdown,
    compute_recently_completed,
    compute_site_distribution,
    compute_spotlight_tasks,
)

def refresh(self) -> None:
    profile = self.app.profile
    if not profile:
        return

    # Data computation (no UI)
    stat_cards = compute_stat_cards(profile)
    active = profile.tasks_for_category("Weekly") + profile.tasks_for_category("Ongoing")
    prio_breakdown = compute_priority_breakdown(active)
    recent = compute_recently_completed(profile.tasks_for_category("Completed"))
    sites = compute_site_distribution(active)
    spotlight = compute_spotlight_tasks(active)

    # UI rendering (no computation)
    self._render_stat_cards(stat_cards)
    self._render_priority_breakdown(prio_breakdown, len(active))
    self._render_recently_completed(recent)
    self._render_site_distribution(sites)
    self._render_spotlight(spotlight)
```

Split the existing UI code into private render methods. Each method handles only widget creation using the pre-computed data passed as arguments.

---

## Acceptance Criteria

1. `helpers/data/dashboard.py` exists with 5 pure functions
2. None of the 5 functions import from `scripts/`, `tkinter`, or `customtkinter`
3. `dashboard_page.py`'s `refresh()` calls these functions and passes results to render methods
4. No `Counter` or business-logic filtering remains in `dashboard_page.py`
5. The dashboard looks and behaves identically
6. `pytest tests/gui/test_dashboard_page.py` passes
7. The new helpers can be unit tested independently (no GUI required)

---

## Constraints

- Color assignments for stat cards remain in the page (they are UI decisions, not business logic)
- Do NOT change the dashboard layout or add new features
- The helper functions take domain objects or primitive types — no tkinter widgets
- Keep the `helpers/data/dashboard.py` module focused — it computes data, nothing else
