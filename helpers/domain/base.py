"""Common base class for all domain nodes in the hierarchy.

Every node carries identity, scheduling metadata, and a parent reference
so that any node can resolve upward to the profile root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Node:
    """Base class shared by Profile, Project, Task, and Deliverable."""

    id: str
    title: str
    parent: Any | None = field(default=None, repr=False, compare=False)
    description: str = ""
    deadline: date | None = None
    start: date | None = None
    end: date | None = None
    status: str = "Not Started"

    # ── Computed helpers ───────────────────────────────────────────────────

    @property
    def timeline(self) -> tuple[date | None, date | None]:
        """Return ``(start, end)`` date pair."""
        return (self.start, self.end)

    @property
    def is_overdue(self) -> bool:
        """True when a deadline exists and today is past it."""
        return self.deadline is not None and date.today() > self.deadline

    def resolve_root(self) -> "Node":
        """Walk up the parent chain and return the root node (Profile)."""
        node: Node = self
        while node.parent is not None:
            node = node.parent
        return node

    # ── Serialisation helpers ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a JSON-safe dict (excludes parent to avoid cycles)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "status": self.status,
        }
