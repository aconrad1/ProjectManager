"""Task domain node — contains Deliverables, owned by a Project."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from helpers.domain.base import Node
from helpers.domain.deliverable import Deliverable


@dataclass
class Task(Node):
    """A task within a project.  Carries priority and child deliverables.

    This replaces the flat ``helpers.data.tasks.Task`` for all domain logic.
    The legacy dataclass is kept for backward-compatible workbook I/O and
    report rendering (converted via persistence adapters).
    """

    deliverables: list[Deliverable] = field(default_factory=list)
    task_id: str = ""          # T-NNN (workbook primary key)
    project_id: str = ""       # FK → Projects.Project ID
    priority: int = 3
    supervisor: str = ""
    site: str = ""
    commentary: str = ""
    date_completed: date | None = None
    scheduled_date: date | None = None

    # ── Children management ────────────────────────────────────────────────

    def add_deliverable(self, d: Deliverable) -> None:
        d.parent = self
        self.deliverables.append(d)

    def find_deliverable(self, deliverable_id: str) -> Deliverable | None:
        for d in self.deliverables:
            if d.id == deliverable_id:
                return d
        return None

    def remove_deliverable(self, deliverable_id: str) -> bool:
        for i, d in enumerate(self.deliverables):
            if d.id == deliverable_id:
                self.deliverables.pop(i)
                return True
        return False

    # ── Priority helpers ───────────────────────────────────────────────────

    @property
    def priority_label(self) -> str:
        labels = {1: "Urgent", 2: "High", 3: "Medium", 4: "Low", 5: "Background"}
        return labels.get(self.priority, "Unknown")

    # ── Time aggregation ───────────────────────────────────────────────────

    @property
    def time_allocated_total(self) -> float:
        """Sum of time_allocated across all deliverables (hours)."""
        return sum(d.time_allocated for d in self.deliverables if d.time_allocated is not None)

    @property
    def time_spent_total(self) -> float:
        """Sum of time_spent across all deliverables (hours)."""
        return sum(d.time_spent for d in self.deliverables if d.time_spent is not None)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "type": "task",
            "task_id": self.task_id,
            "project_id": self.project_id,
            "priority": self.priority,
            "supervisor": self.supervisor,
            "site": self.site,
            "commentary": self.commentary,
            "date_completed": self.date_completed.isoformat() if self.date_completed else None,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "deliverables": [dl.to_dict() for dl in self.deliverables],
        })
        return d

    @classmethod
    def from_dict(cls, data: dict, parent=None) -> "Task":
        task = cls(
            id=data["id"],
            title=data["title"],
            parent=parent,
            description=data.get("description", ""),
            deadline=date.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            start=date.fromisoformat(data["start"]) if data.get("start") else None,
            end=date.fromisoformat(data["end"]) if data.get("end") else None,
            status=data.get("status", "Not Started"),
            task_id=data.get("task_id", ""),
            project_id=data.get("project_id", ""),
            priority=data.get("priority", 3),
            supervisor=data.get("supervisor", ""),
            site=data.get("site", ""),
            commentary=data.get("commentary", ""),
            date_completed=(
                date.fromisoformat(data["date_completed"])
                if data.get("date_completed") else None
            ),
            scheduled_date=(
                date.fromisoformat(data["scheduled_date"])
                if data.get("scheduled_date") else None
            ),
        )
        for dd in data.get("deliverables", []):
            task.add_deliverable(Deliverable.from_dict(dd, parent=task))
        return task
