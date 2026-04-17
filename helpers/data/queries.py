"""Shared query helpers for filtering domain data."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from helpers.domain.project import Project


def filter_projects_by_category(projects: list[Project], category: str) -> list[Project]:
    """Return projects matching *category*, or all if category is 'All'."""
    if category == "All":
        return list(projects)
    return [project for project in projects if project.category == category]
