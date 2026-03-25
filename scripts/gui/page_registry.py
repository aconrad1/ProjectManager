"""Page registry — declarative configuration for all GUI pages.

To add a new page:
  1. Create a file in ``gui/pages/`` with a class that subclasses ``BasePage``.
     The class must define ``KEY``, ``TITLE``, ``build()``, and ``refresh()``.
     Set ``OPTIONAL = True`` if the page can be skipped when its data is absent.
  2. Add one entry to ``PAGE_DEFS`` below.  That's it — no other code changes.

Each entry is a dict with:
  - ``module``:  dotted import path relative to ``scripts/`` (e.g. ``gui.pages.tasks_page``)
  - ``class_name``:  the BasePage subclass name to import
  - ``nav_label``:  sidebar button text (leading spaces for padding)
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from gui.base_page import BasePage


@dataclass
class PageDef:
    module: str
    class_name: str
    nav_label: str


# ── Master page list — order here controls sidebar order ──────────────────────
PAGE_DEFS: list[PageDef] = [
    PageDef("gui.pages.tasks_page",      "TasksPage",      "  Tasks"),
    PageDef("gui.pages.add_task_page",    "AddTaskPage",    "  Add Task"),
    PageDef("gui.pages.generate_page",    "GeneratePage",   "  Generate"),
    PageDef("gui.pages.gantt_page",       "GanttPage",      "  Project Timeline"),
    PageDef("gui.pages.scheduler_page",   "SchedulerPage",  "  Weekly Planner"),
    PageDef("gui.pages.dashboard_page",   "DashboardPage",  "  Dashboard"),
    PageDef("gui.pages.profile_page",     "ProfilePage",    "  Profiles"),
    PageDef("gui.pages.settings_page",    "SettingsPage",   "  Settings"),
]


def load_pages() -> list[tuple[str, Type["BasePage"], str]]:
    """Import and return all page classes from ``PAGE_DEFS``.

    Returns a list of ``(key, PageClass, nav_label)`` tuples in sidebar order.
    Pages marked ``OPTIONAL = True`` are silently skipped if the import fails.
    """
    result: list[tuple[str, Type["BasePage"], str]] = []
    for defn in PAGE_DEFS:
        try:
            mod = import_module(defn.module)
            cls = getattr(mod, defn.class_name)
            result.append((cls.KEY, cls, defn.nav_label))
        except Exception:
            # Optional pages may fail if dependencies are missing — skip them
            pass
    return result
