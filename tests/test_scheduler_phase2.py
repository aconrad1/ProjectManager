"""Tests for Phase 2 scheduler — partial allocation, weekly budget, multi-task slots."""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from helpers.scheduling.engine import (
    compute_schedule,
    daily_hours,
    over_capacity_days,
    weekly_hours_totals,
    flatten_schedule,
    week_start_date,
    _task_hours,
    Schedule,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_deliverable(time_allocated):
    d = MagicMock()
    d.time_allocated = time_allocated
    return d


def _make_task(task_id: str, title: str, priority: int = 3,
               deliverables=None, status="In Progress",
               scheduled_date=None, deadline=None, start=None):
    t = MagicMock()
    t.id = task_id
    t.title = title
    t.priority = priority
    t.status = status
    t.deliverables = deliverables or []
    t.scheduled_date = scheduled_date
    t.deadline = deadline
    t.start = start
    return t


def _make_project(tasks, category="Weekly"):
    p = MagicMock()
    p.category = category
    p.tasks = tasks
    return p


def _make_profile(projects, daily_budget=8.0, weekly_budget=40.0):
    p = MagicMock()
    p.projects = projects
    p.daily_hours_budget = daily_budget
    p.weekly_hours_budget = weekly_budget
    return p


_DEFAULT_CFG = {
    "default_time_allocated_hours": 1.0,
    "max_tasks_per_priority_slot": 3,
    "week_start_day": "monday",
    "enforce_weekly_budget": False,
}


def _cfg(**overrides):
    return {**_DEFAULT_CFG, **overrides}


# ── Test classes ───────────────────────────────────────────────────────────────

class TestScheduleReturnType:
    """Verify the new nested schedule format."""

    def test_schedule_is_nested_dict(self):
        task = _make_task("T-001", "A", priority=1,
                          deliverables=[_make_deliverable(2.0)])
        proj = _make_project([task])
        profile = _make_profile([proj])
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        # Top level: date keys
        assert ref in sched
        # Second level: priority → list of (task, hours)
        assert 1 in sched[ref]
        entries = sched[ref][1]
        assert len(entries) == 1
        assert entries[0][0] is task
        assert entries[0][1] == 2.0

    def test_flatten_schedule(self):
        task = _make_task("T-001", "A", priority=2,
                          deliverables=[_make_deliverable(3.0)])
        proj = _make_project([task])
        profile = _make_profile([proj])
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
            flat = flatten_schedule(sched)
        assert ref in flat
        assert flat[ref][0] == (2, task)


class TestPartialAllocation:
    """Test that tasks exceeding daily budget are split across days."""

    def test_task_split_across_two_days(self):
        """A 6-hour task with a 4-hour daily cap should split 4+2."""
        task = _make_task("T-001", "Biggie", priority=1,
                          deliverables=[_make_deliverable(6.0)])
        proj = _make_project([task])
        profile = _make_profile([proj], daily_budget=4.0)
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        # Should span 2 days
        day1 = ref
        day2 = ref + timedelta(days=1)
        assert day1 in sched and 1 in sched[day1]
        assert day2 in sched and 1 in sched[day2]
        hrs_day1 = sched[day1][1][0][1]
        hrs_day2 = sched[day2][1][0][1]
        assert abs(hrs_day1 - 4.0) < 0.01
        assert abs(hrs_day2 - 2.0) < 0.01

    def test_task_fits_in_one_day(self):
        """A 3-hour task with an 8-hour cap fits in one day."""
        task = _make_task("T-001", "Small", priority=1,
                          deliverables=[_make_deliverable(3.0)])
        proj = _make_project([task])
        profile = _make_profile([proj], daily_budget=8.0)
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        assert len(sched) == 1
        assert sched[ref][1][0][1] == 3.0

    def test_scheduled_date_is_first_day(self):
        """task.scheduled_date should be set to the first day of allocation."""
        task = _make_task("T-001", "X", priority=1,
                          deliverables=[_make_deliverable(10.0)])
        proj = _make_project([task])
        profile = _make_profile([proj], daily_budget=4.0)
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            compute_schedule(profile, ref)
        assert task.scheduled_date == ref


class TestMultiTaskSlots:
    """Test that multiple tasks can share (day, priority)."""

    def test_two_tasks_same_priority_same_day(self):
        t1 = _make_task("T-001", "A", priority=2,
                        deliverables=[_make_deliverable(2.0)])
        t2 = _make_task("T-002", "B", priority=2,
                        deliverables=[_make_deliverable(2.0)])
        proj = _make_project([t1, t2])
        profile = _make_profile([proj], daily_budget=8.0)
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        # Both should be on the same day, same priority
        assert ref in sched and 2 in sched[ref]
        tasks_on_day = [t for t, _ in sched[ref][2]]
        assert t1 in tasks_on_day
        assert t2 in tasks_on_day

    def test_max_slot_limit_respected(self):
        """When max_tasks_per_priority_slot=1, only 1 task per slot."""
        t1 = _make_task("T-001", "A", priority=2,
                        deliverables=[_make_deliverable(1.0)])
        t2 = _make_task("T-002", "B", priority=2,
                        deliverables=[_make_deliverable(1.0)])
        proj = _make_project([t1, t2])
        profile = _make_profile([proj], daily_budget=8.0)
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config",
                   return_value=_cfg(max_tasks_per_priority_slot=1)):
            sched = compute_schedule(profile, ref)
        # Each day/priority should have at most 1 task
        for day, pri_map in sched.items():
            for pri, entries in pri_map.items():
                task_ids = {t.id for t, _ in entries}
                assert len(task_ids) <= 1


class TestWeeklyBudget:
    """Test weekly_hours_budget enforcement."""

    def test_weekly_budget_not_enforced_by_default(self):
        """With enforce_weekly_budget=False, tasks are not capped by weekly budget."""
        tasks = [
            _make_task(f"T-{i:03d}", f"Task {i}", priority=3,
                       deliverables=[_make_deliverable(8.0)])
            for i in range(1, 7)  # 6 tasks × 8h = 48h
        ]
        proj = _make_project(tasks)
        profile = _make_profile([proj], daily_budget=8.0, weekly_budget=40.0)
        ref = date(2026, 3, 23)  # Monday
        with patch("helpers.scheduling.engine.load_config",
                   return_value=_cfg(enforce_weekly_budget=False)):
            sched = compute_schedule(profile, ref)
        total = sum(sum(h for _, h in e) for pm in sched.values() for e in pm.values())
        # All 48 hours should be scheduled (no weekly cap)
        assert abs(total - 48.0) < 0.01

    def test_weekly_budget_enforced(self):
        """With enforce_weekly_budget=True, total hours per week ≤ weekly_budget."""
        tasks = [
            _make_task(f"T-{i:03d}", f"Task {i}", priority=3,
                       deliverables=[_make_deliverable(8.0)])
            for i in range(1, 7)  # 6 tasks × 8h = 48h
        ]
        proj = _make_project(tasks)
        profile = _make_profile([proj], daily_budget=8.0, weekly_budget=24.0)
        ref = date(2026, 3, 23)  # Monday
        with patch("helpers.scheduling.engine.load_config",
                   return_value=_cfg(enforce_weekly_budget=True)):
            sched = compute_schedule(profile, ref)
        # Check first week totals
        wk = weekly_hours_totals(sched, week_start_day=0)
        week_1_key = date(2026, 3, 23)
        if week_1_key in wk:
            assert wk[week_1_key] <= 24.0 + 0.01


class TestCustomWeekStart:
    """Test configurable week start day."""

    def test_monday_default(self):
        d = date(2026, 3, 25)  # Wednesday
        assert week_start_date(d, 0) == date(2026, 3, 23)  # Monday

    def test_sunday_start(self):
        d = date(2026, 3, 25)  # Wednesday
        assert week_start_date(d, 6) == date(2026, 3, 22)  # Sunday

    def test_saturday_start(self):
        d = date(2026, 3, 25)  # Wednesday
        assert week_start_date(d, 5) == date(2026, 3, 21)  # Saturday

    def test_on_start_day(self):
        """When d is the start day, should return d itself."""
        d = date(2026, 3, 23)  # Monday
        assert week_start_date(d, 0) == d


class TestDailyHours:
    """Test analysis helpers with new schedule format."""

    def test_sums_all_entries(self):
        task1 = MagicMock()
        task2 = MagicMock()
        day = date(2026, 3, 25)
        sched: Schedule = {
            day: {
                1: [(task1, 2.0)],
                3: [(task2, 3.5)],
            }
        }
        result = daily_hours(sched)
        assert abs(result[day] - 5.5) < 0.01

    def test_over_capacity(self):
        task = MagicMock()
        day = date(2026, 3, 25)
        sched: Schedule = {day: {1: [(task, 10.0)]}}
        result = over_capacity_days(sched, 8.0)
        assert day in result
        assert result[day] == 10.0


class TestExcludedStatuses:
    """Verify completed and on-hold tasks are excluded."""

    def test_completed_excluded(self):
        task = _make_task("T-001", "Done", status="Completed",
                          deliverables=[_make_deliverable(2.0)])
        proj = _make_project([task])
        profile = _make_profile([proj])
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        assert len(sched) == 0

    def test_on_hold_excluded(self):
        task = _make_task("T-001", "Held", status="On Hold",
                          deliverables=[_make_deliverable(2.0)])
        proj = _make_project([task])
        profile = _make_profile([proj])
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        assert len(sched) == 0


class TestSafetyLimit:
    """Verify the scheduler doesn't infinite-loop on edge cases."""

    def test_empty_profile(self):
        profile = _make_profile([])
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        assert sched == {}

    def test_no_active_tasks(self):
        task = _make_task("T-001", "X", status="Completed",
                          deliverables=[_make_deliverable(1.0)])
        proj = _make_project([task])
        profile = _make_profile([proj])
        ref = date(2026, 3, 25)
        with patch("helpers.scheduling.engine.load_config", return_value=_cfg()):
            sched = compute_schedule(profile, ref)
        assert sched == {}


class TestWeeklyHoursTotals:
    """Test the weekly_hours_totals helper."""

    def test_groups_by_week(self):
        task = MagicMock()
        mon = date(2026, 3, 23)
        wed = date(2026, 3, 25)
        next_mon = date(2026, 3, 30)
        sched: Schedule = {
            mon: {1: [(task, 3.0)]},
            wed: {1: [(task, 2.0)]},
            next_mon: {1: [(task, 4.0)]},
        }
        result = weekly_hours_totals(sched, week_start_day=0)
        assert abs(result[mon] - 5.0) < 0.01
        assert abs(result[next_mon] - 4.0) < 0.01
