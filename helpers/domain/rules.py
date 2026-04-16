"""Pure business rules for the domain model.

These functions encode decisions that apply regardless of whether the caller
is operating on domain objects or workbook cells.
"""

from __future__ import annotations

from helpers.config.loader import completion_aliases, terminal_categories, default_category


def should_auto_complete_project(task_statuses: list[str]) -> bool:
    """Return True if all task statuses indicate completion."""
    if not task_statuses:
        return False
    _aliases = completion_aliases()
    return all(s.strip().lower() in _aliases for s in task_statuses)


def should_reopen_project(project_category: str) -> bool:
    """Return True if a project should be reverted from Completed to Ongoing."""
    return project_category.strip() in terminal_categories()


def reopen_category() -> str:
    """The category to revert a completed project to when reopened."""
    return default_category()
