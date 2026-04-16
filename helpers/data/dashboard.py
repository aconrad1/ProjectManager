"""Dashboard statistics computation helpers (no UI dependencies)."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import TYPE_CHECKING

from helpers.config.loader import active_categories, terminal_categories, valid_categories

if TYPE_CHECKING:
    from helpers.domain.profile import Profile
    from helpers.domain.task import Task


def compute_stat_cards(profile: Profile) -> list[tuple[str, int]]:
    """Return (label, count) entries for dashboard stat cards."""
    _active = active_categories()
    _terminal = terminal_categories()
    active_tasks: list = []
    terminal_tasks: list = []
    cards: list[tuple[str, int]] = []
    for cat in valid_categories():
        tasks = profile.tasks_for_category(cat)
        cards.append((f"{cat} Tasks" if cat not in _terminal else cat, len(tasks)))
        if cat in _active:
            active_tasks.extend(tasks)
        elif cat in _terminal:
            terminal_tasks.extend(tasks)
    cards.append(("Total Active", len(active_tasks)))
    return cards


def compute_priority_breakdown(tasks: list[Task]) -> dict[int, int]:
    """Return counts by priority for the provided task list."""
    return dict(Counter(task.priority for task in tasks))


def compute_recently_completed(tasks: list[Task], since: date | None = None) -> list[Task]:
    """Return completed tasks since *since* (default: 7 days), newest first."""
    if since is None:
        since = date.today() - timedelta(days=7)
    return sorted(
        [task for task in tasks if task.date_completed and task.date_completed >= since],
        key=lambda task: task.date_completed,
        reverse=True,
    )


def compute_site_distribution(tasks: list[Task], top_n: int = 8) -> list[tuple[str, int]]:
    """Return (site, count) sorted by frequency."""
    site_counts: Counter[str] = Counter()
    for task in tasks:
        sites = [site.strip() for site in task.site.replace("&", ",").split(",") if site.strip()]
        if not sites or sites == ["N/A"]:
            sites = ["Unassigned"]
        for site in sites:
            site_counts[site] += 1
    return site_counts.most_common(top_n)


def compute_spotlight_tasks(tasks: list[Task], max_priority: int = 2, limit: int = 6) -> list[Task]:
    """Return highest-priority tasks sorted by priority."""
    return sorted(
        [task for task in tasks if task.priority <= max_priority],
        key=lambda task: task.priority,
    )[:limit]
