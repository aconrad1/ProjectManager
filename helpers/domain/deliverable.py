"""Deliverable domain node — leaf of the hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from helpers.domain.base import Node


@dataclass
class Deliverable(Node):
    """A concrete deliverable item owned by a Task."""

    deliverable_id: str = ""   # D-NNN (workbook primary key)
    task_id: str = ""          # FK → Tasks.Task ID
    percent_complete: int = 0
    time_allocated: float | None = None   # hours
    time_spent: float | None = None       # hours

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "type": "deliverable",
            "deliverable_id": self.deliverable_id,
            "task_id": self.task_id,
            "percent_complete": self.percent_complete,
            "time_allocated": self.time_allocated,
            "time_spent": self.time_spent,
        })
        return d

    @classmethod
    def from_dict(cls, data: dict, parent=None) -> "Deliverable":
        return cls(
            id=data["id"],
            title=data["title"],
            parent=parent,
            description=data.get("description", ""),
            deadline=date.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            start=date.fromisoformat(data["start"]) if data.get("start") else None,
            end=date.fromisoformat(data["end"]) if data.get("end") else None,
            status=data.get("status", "Not Started"),
            deliverable_id=data.get("deliverable_id", ""),
            task_id=data.get("task_id", ""),
            percent_complete=data.get("percent_complete", 0),
            time_allocated=data.get("time_allocated"),
            time_spent=data.get("time_spent"),
        )
