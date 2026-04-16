"""Project domain node — contains Tasks, owned by a Profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from helpers.domain.base import Node
from helpers.domain.task import Task
from helpers.config.loader import default_priority, default_status


@dataclass
class Project(Node):
    """A project within a profile.  Maps to an Excel sheet category."""

    tasks: list[Task] = field(default_factory=list)
    project_id: str = ""   # P-NNN (workbook primary key)
    category: str = ""     # Weekly / Ongoing / Completed
    supervisor: str = ""
    site: str = ""
    priority: int = 3
    notes: str = ""
    date_completed: date | None = None

    # ── Children management ────────────────────────────────────────────────

    def add_task(self, task: Task) -> None:
        task.parent = self
        self.tasks.append(task)

    def find_task(self, task_id: str) -> Task | None:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def remove_task(self, task_id: str) -> bool:
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self.tasks.pop(i)
                return True
        return False

    # ── Queries ────────────────────────────────────────────────────────────

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    def tasks_by_priority(self) -> list[Task]:
        return sorted(self.tasks, key=lambda t: t.priority)

    def tasks_by_status(self, status: str) -> list[Task]:
        return [t for t in self.tasks if t.status.lower().strip() == status.lower().strip()]

    # ── Time aggregation ───────────────────────────────────────────────────

    @property
    def time_allocated_total(self) -> float:
        """Sum of time_allocated_total across all tasks (hours)."""
        return sum(t.time_allocated_total for t in self.tasks)

    @property
    def time_spent_total(self) -> float:
        """Sum of time_spent_total across all tasks (hours)."""
        return sum(t.time_spent_total for t in self.tasks)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "type": "project",
            "project_id": self.project_id,
            "category": self.category,
            "supervisor": self.supervisor,
            "site": self.site,
            "priority": self.priority,
            "notes": self.notes,
            "date_completed": self.date_completed.isoformat() if self.date_completed else None,
            "tasks": [t.to_dict() for t in self.tasks],
        })
        return d

    @classmethod
    def from_dict(cls, data: dict, parent=None) -> "Project":
        project = cls(
            id=data["id"],
            title=data["title"],
            parent=parent,
            description=data.get("description", ""),
            deadline=date.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            start=date.fromisoformat(data["start"]) if data.get("start") else None,
            end=date.fromisoformat(data["end"]) if data.get("end") else None,
            status=data.get("status", default_status()),
            project_id=data.get("project_id", ""),
            category=data.get("category", ""),
            supervisor=data.get("supervisor", ""),
            site=data.get("site", ""),
            priority=data.get("priority", default_priority()),
            notes=data.get("notes", ""),
            date_completed=(
                date.fromisoformat(data["date_completed"])
                if data.get("date_completed") else None
            ),
        )
        for td in data.get("tasks", []):
            project.add_task(Task.from_dict(td, parent=project))
        return project
