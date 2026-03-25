"""Daily task scheduler — partial allocation, weekly budgets, multi-task slots.

Assigns each active task to one or more calendar days, splitting work
hours across days when a task cannot fit entirely into a single day's
remaining budget.

Features
--------
- **Partial allocation** — a task's hours can span multiple days.
- **Multi-task slots** — each ``(day, priority)`` can hold up to
  ``max_tasks_per_priority_slot`` tasks (configurable).
- **Daily budget** — ``profile.daily_hours_budget`` caps hours per day.
- **Weekly budget** — optional ``profile.weekly_hours_budget`` cap
  when ``enforce_weekly_budget`` is enabled.
- **Custom week start** — ``week_start_day`` in config (monday/sunday/
  saturday).

Return type
-----------
``Schedule = dict[date, dict[int, list[tuple[Task, float]]]]``

    schedule[day][priority] = [(task, hours_assigned), ...]

The helper :func:`flatten_schedule` converts this to the legacy flat
format ``dict[date, list[tuple[int, Task]]]`` for callers that don't
need per-slot detail.

Algorithm
---------
1.  Gather active tasks (Weekly + Ongoing, status not Completed/On Hold).
2.  Group by priority (1-5).
3.  Sort each group by rollover → deadline → start → title.
4.  For each priority, iterate tasks and allocate hours day-by-day:
    a) Find the next day with daily capacity, weekly capacity (if
       enforced), and slot room for this priority.
    b) Assign ``min(remaining_task_hours, remaining_day_capacity)``
       hours to that day.
    c) Repeat until the task's hours are fully allocated.
5.  Set ``task.scheduled_date`` to the **first** day it appears on.
6.  Return the nested schedule mapping.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import TypeAlias

from helpers.domain.profile import Profile
from helpers.domain.task import Task
from helpers.config.loader import load as load_config

# ── Public type aliases ────────────────────────────────────────────────────────
ScheduleEntry: TypeAlias = tuple[Task, float]            # (task, hours_assigned)
Schedule: TypeAlias = dict[date, dict[int, list[ScheduleEntry]]]

# ── Internal constants ─────────────────────────────────────────────────────────
_EXCLUDED_STATUSES = frozenset({"completed", "on hold"})
_MAX_SCHEDULE_DAYS = 365  # safety limit to prevent infinite loops

_WEEK_START_MAP: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_active(task: Task) -> bool:
    """Return True if the task should be scheduled."""
    return task.status.strip().lower() not in _EXCLUDED_STATUSES


def _sort_key(task: Task, ref: date):
    """Sort key: rollover first → deadline → start → title."""
    is_rollover = (
        task.scheduled_date is not None
        and task.scheduled_date < ref
    )
    rollover_rank = 0 if is_rollover else 1
    _far = date(2999, 12, 31)
    deadline_val = task.deadline if task.deadline else _far
    start_val = task.start if task.start else _far
    return (rollover_rank, deadline_val, start_val, task.title)


def _task_hours(task: Task) -> float:
    """Total allocated hours for a task (sum of deliverable allocations).

    Falls back to ``default_time_allocated_hours`` from config.
    """
    total = sum(d.time_allocated for d in task.deliverables if d.time_allocated)
    if total > 0:
        return total
    defaults = load_config("defaults")
    return defaults.get("default_time_allocated_hours", 1.0)


def _get_week_start_day() -> int:
    """Return the weekday int (0=monday) for the configured week start."""
    defaults = load_config("defaults")
    name = defaults.get("week_start_day", "monday").strip().lower()
    return _WEEK_START_MAP.get(name, 0)


def week_start_date(d: date, start_day: int | None = None) -> date:
    """Return the start of the week containing *d*.

    *start_day* is a weekday int (0=Monday .. 6=Sunday).  If ``None``,
    reads from config.
    """
    if start_day is None:
        start_day = _get_week_start_day()
    offset = (d.weekday() - start_day) % 7
    return d - timedelta(days=offset)


# ── Core scheduler ─────────────────────────────────────────────────────────────

def compute_schedule(
    profile: Profile,
    reference_date: date | None = None,
) -> Schedule:
    """Assign every active task to one or more days with partial allocation.

    Parameters
    ----------
    profile : Profile
        The loaded domain hierarchy.
    reference_date : date, optional
        The scheduling anchor (defaults to today).

    Returns
    -------
    Schedule
        ``{date: {priority: [(task, hours_assigned), ...]}}``.
    """
    if reference_date is None:
        reference_date = date.today()

    cfg = load_config("defaults")
    daily_cap: float = profile.daily_hours_budget or 8.0
    weekly_cap: float = profile.weekly_hours_budget or 40.0
    enforce_weekly: bool = cfg.get("enforce_weekly_budget", False)
    max_per_slot: int = cfg.get("max_tasks_per_priority_slot", 3)
    wk_start_day: int = _WEEK_START_MAP.get(
        cfg.get("week_start_day", "monday").strip().lower(), 0
    )

    # 1. Gather active tasks from Weekly + Ongoing projects
    active_tasks: list[Task] = []
    for project in profile.projects:
        cat = project.category.strip().lower()
        if cat in ("weekly", "ongoing"):
            for task in project.tasks:
                if _is_active(task):
                    active_tasks.append(task)

    # 2. Group by priority
    by_priority: dict[int, list[Task]] = defaultdict(list)
    for task in active_tasks:
        by_priority[task.priority].append(task)

    # 3. Sort each group
    for pri in by_priority:
        by_priority[pri].sort(key=lambda t: _sort_key(t, reference_date))

    # 4. Allocate with partial-day splitting
    schedule: Schedule = defaultdict(lambda: defaultdict(list))
    day_hours: dict[date, float] = defaultdict(float)
    week_hours: dict[date, float] = defaultdict(float)  # keyed by week-start date
    # Track slot counts: (day, priority) → number of distinct tasks
    slot_count: dict[tuple[date, int], int] = defaultdict(int)

    for pri in sorted(by_priority.keys()):
        tasks = by_priority[pri]
        # Track where to start looking for each task in this priority
        global_offset = 0

        for task in tasks:
            remaining = _task_hours(task)
            if remaining <= 0:
                remaining = cfg.get("default_time_allocated_hours", 1.0)

            first_day: date | None = None
            offset = global_offset
            safety = 0

            while remaining > 1e-9 and safety < _MAX_SCHEDULE_DAYS:
                safety += 1
                day = reference_date + timedelta(days=offset)
                wk_key = week_start_date(day, wk_start_day)

                # Check slot capacity for this (day, priority)
                if slot_count[(day, pri)] >= max_per_slot:
                    offset += 1
                    continue

                # Check daily capacity
                avail_day = daily_cap - day_hours[day]
                if avail_day <= 1e-9:
                    offset += 1
                    continue

                # Check weekly capacity (if enforced)
                if enforce_weekly:
                    avail_week = weekly_cap - week_hours[wk_key]
                    if avail_week <= 1e-9:
                        # Skip to next week
                        days_to_next_week = 7 - (day - wk_key).days
                        offset += max(days_to_next_week, 1)
                        continue
                    avail_day = min(avail_day, avail_week)

                # Allocate hours
                assign = min(remaining, avail_day)
                schedule[day][pri].append((task, assign))
                day_hours[day] += assign
                week_hours[wk_key] += assign
                remaining -= assign

                if first_day is None:
                    first_day = day
                    slot_count[(day, pri)] += 1
                elif day != first_day:
                    slot_count[(day, pri)] += 1

                # If we fully consumed this day, move to next
                if daily_cap - day_hours[day] <= 1e-9:
                    offset += 1
                else:
                    # Try to fit more of this task on the same day
                    # (only if there's still remaining hours)
                    if remaining > 1e-9:
                        offset += 1

            task.scheduled_date = first_day
            # Next task in this priority starts at least at the same offset
            # (allows multiple tasks per slot)
            if first_day is not None:
                global_offset = (first_day - reference_date).days

    # Convert nested defaultdicts to plain dicts
    return {day: dict(pri_map) for day, pri_map in schedule.items()}


# ── Schedule conversion & analysis ─────────────────────────────────────────────

def flatten_schedule(
    schedule: Schedule,
) -> dict[date, list[tuple[int, Task]]]:
    """Convert the nested schedule to the legacy flat format.

    Each task appears once per day (the first entry wins).
    Useful for callers that expect ``{date: [(priority, task), ...]}``.
    """
    flat: dict[date, list[tuple[int, Task]]] = {}
    for day, pri_map in schedule.items():
        entries: list[tuple[int, Task]] = []
        seen: set[str] = set()
        for pri in sorted(pri_map.keys()):
            for task, _hrs in pri_map[pri]:
                if task.id not in seen:
                    entries.append((pri, task))
                    seen.add(task.id)
        flat[day] = entries
    return flat


def daily_hours(schedule: Schedule) -> dict[date, float]:
    """Return total allocated hours per day from a schedule."""
    result: dict[date, float] = {}
    for day, pri_map in schedule.items():
        total = 0.0
        for entries in pri_map.values():
            total += sum(hrs for _, hrs in entries)
        result[day] = total
    return result


def over_capacity_days(
    schedule: Schedule,
    daily_cap: float,
) -> dict[date, float]:
    """Return days where allocated hours exceed *daily_cap*.

    Returns ``{date: total_hours}`` only for over-capacity days.
    """
    return {
        day: hours
        for day, hours in daily_hours(schedule).items()
        if hours > daily_cap
    }


def weekly_hours_totals(
    schedule: Schedule,
    week_start_day: int | None = None,
) -> dict[date, float]:
    """Return total hours per week (keyed by week-start date)."""
    result: dict[date, float] = defaultdict(float)
    for day, hours in daily_hours(schedule).items():
        wk = week_start_date(day, week_start_day)
        result[wk] += hours
    return dict(result)
