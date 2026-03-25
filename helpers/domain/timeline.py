"""Timeline value object — represents a date range with helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Timeline:
    """Immutable date range used by any domain node."""

    start: date | None = None
    end: date | None = None

    @property
    def duration_days(self) -> int | None:
        if self.start and self.end:
            return (self.end - self.start).days
        return None

    @property
    def is_active(self) -> bool:
        today = date.today()
        started = self.start is None or self.start <= today
        not_ended = self.end is None or today <= self.end
        return started and not_ended

    def contains(self, d: date) -> bool:
        if self.start and d < self.start:
            return False
        if self.end and d > self.end:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Timeline":
        start = date.fromisoformat(data["start"]) if data.get("start") else None
        end = date.fromisoformat(data["end"]) if data.get("end") else None
        return cls(start=start, end=end)
