"""Profile domain node — root of the hierarchy.

A Profile owns Projects and carries all metadata needed by the
configuration layer (company, role, paths, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from helpers.domain.base import Node
from helpers.domain.deliverable import Deliverable
from helpers.domain.project import Project
from helpers.domain.task import Task


@dataclass
class Profile(Node):
    """Root of the Profile → Project → Task → Deliverable hierarchy."""

    projects: list[Project] = field(default_factory=list)

    # Profile-level metadata (mirrors user_profile.yaml)
    company: str = ""
    role: str = ""
    email: str = ""
    phone: str = ""
    recipient_name: str = ""
    recipient_email: str = ""
    workbook_filename: str = ""

    # Time budget settings
    daily_hours_budget: float = 8.0
    weekly_hours_budget: float = 40.0

    # ── Children management ────────────────────────────────────────────────

    def add_project(self, project: Project) -> None:
        project.parent = self
        self.projects.append(project)

    def find_project(self, project_id: str) -> Project | None:
        for p in self.projects:
            if p.id == project_id:
                return p
        return None

    def find_project_by_category(self, category: str) -> Project | None:
        """Return the first project matching *category* (e.g. 'Weekly')."""
        cat = category.strip().lower()
        for p in self.projects:
            if p.category.strip().lower() == cat:
                return p
        return None

    def projects_for_category(self, category: str) -> list[Project]:
        """Return all projects matching *category*."""
        cat = category.strip().lower()
        return [p for p in self.projects if p.category.strip().lower() == cat]

    def remove_project(self, project_id: str) -> bool:
        for i, p in enumerate(self.projects):
            if p.id == project_id:
                self.projects.pop(i)
                return True
        return False

    # ── Cross-hierarchy queries ────────────────────────────────────────────

    @property
    def all_tasks(self) -> list[Task]:
        """Flat list of every task across all projects."""
        result: list[Task] = []
        for p in self.projects:
            result.extend(p.tasks)
        return result

    def find_task_global(self, task_id: str) -> Task | None:
        """Search all projects for a task by ID."""
        for p in self.projects:
            t = p.find_task(task_id)
            if t:
                return t
        return None

    def find_by_id(self, item_id: str) -> Project | Task | Deliverable | None:
        """Resolve any prefixed ID (P-/T-/D-) to its domain object."""
        if not item_id or "-" not in item_id:
            return None

        prefix = item_id.split("-")[0].upper()
        if prefix == "P":
            return self.find_project(item_id)
        if prefix == "T":
            return self.find_task_global(item_id)
        if prefix == "D":
            for task in self.all_tasks:
                deliverable = task.find_deliverable(item_id)
                if deliverable:
                    return deliverable
        return None

    def tasks_for_category(self, category: str) -> list[Task]:
        """Return all tasks that belong to projects in *category*."""
        tasks: list[Task] = []
        for p in self.projects_for_category(category):
            tasks.extend(p.tasks)
        return tasks

    # ── Fuzzy / title-based lookups ────────────────────────────────────────

    def search_projects(self, query: str) -> list[Project]:
        """Case-insensitive substring search across project titles."""
        q = query.strip().lower()
        return [p for p in self.projects if q in p.title.lower()]

    def find_project_by_title(self, query: str) -> Project | None:
        """Return the first project whose title contains *query* (case-insensitive).

        Returns an exact-title match first if one exists, otherwise the first
        substring match.
        """
        q = query.strip().lower()
        substring_match = None
        for p in self.projects:
            title = p.title.lower()
            if title == q:
                return p
            if substring_match is None and q in title:
                substring_match = p
        return substring_match

    def search_tasks(self, query: str) -> list[Task]:
        """Case-insensitive substring search across all task titles."""
        q = query.strip().lower()
        return [t for t in self.all_tasks if q in t.title.lower()]

    def find_task_by_title(self, query: str) -> Task | None:
        """Return the first task whose title contains *query* (case-insensitive).

        Returns an exact-title match first if one exists, otherwise the first
        substring match.
        """
        q = query.strip().lower()
        substring_match = None
        for t in self.all_tasks:
            title = t.title.lower()
            if title == q:
                return t
            if substring_match is None and q in title:
                substring_match = t
        return substring_match

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "type": "profile",
            "company": self.company,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "recipient_name": self.recipient_name,
            "recipient_email": self.recipient_email,
            "workbook_filename": self.workbook_filename,
            "daily_hours_budget": self.daily_hours_budget,
            "weekly_hours_budget": self.weekly_hours_budget,
            "projects": [p.to_dict() for p in self.projects],
        })
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        profile = cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            deadline=date.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            start=date.fromisoformat(data["start"]) if data.get("start") else None,
            end=date.fromisoformat(data["end"]) if data.get("end") else None,
            status=data.get("status", "Active"),
            company=data.get("company", ""),
            role=data.get("role", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            recipient_name=data.get("recipient_name", ""),
            recipient_email=data.get("recipient_email", ""),
            workbook_filename=data.get("workbook_filename", ""),
            daily_hours_budget=float(data.get("daily_hours_budget", 8.0)),
            weekly_hours_budget=float(data.get("weekly_hours_budget", 40.0)),
        )
        for pd in data.get("projects", []):
            profile.add_project(Project.from_dict(pd, parent=profile))
        return profile
