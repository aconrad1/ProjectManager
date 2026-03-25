"""Snapshot diff engine — compare two Profile snapshots to detect changes.

Compares the current domain state against the previous ``domain.json``
snapshot (or any two Profile trees) and returns structured change records.

Used by the report pipeline to build the **Change History** section in
Markdown, PDF, and Excel reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

from helpers.domain.profile import Profile
from helpers.persistence.serializer import load_profile_json


# ── Data structures ────────────────────────────────────────────────────────────

ChangeKind = Literal["added", "removed", "modified"]


@dataclass
class FieldChange:
    """A single field-level change on an entity."""
    field: str
    old: str
    new: str


@dataclass
class EntityChange:
    """One addition, removal, or modification of a project/task/deliverable."""
    kind: ChangeKind
    entity_type: str          # "project", "task", "deliverable"
    entity_id: str
    title: str
    fields: list[FieldChange] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """One-line description of the change."""
        if self.kind == "added":
            return f"Added {self.entity_type} '{self.title}'"
        if self.kind == "removed":
            return f"Removed {self.entity_type} '{self.title}'"
        parts = [f"{fc.field}: {fc.old!r} → {fc.new!r}" for fc in self.fields]
        return f"Modified {self.entity_type} '{self.title}': {'; '.join(parts)}"


@dataclass
class SnapshotDiff:
    """Complete diff between two profile snapshots."""
    changes: list[EntityChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def added(self) -> list[EntityChange]:
        return [c for c in self.changes if c.kind == "added"]

    @property
    def removed(self) -> list[EntityChange]:
        return [c for c in self.changes if c.kind == "removed"]

    @property
    def modified(self) -> list[EntityChange]:
        return [c for c in self.changes if c.kind == "modified"]


# ── Fields to compare ──────────────────────────────────────────────────────────

_PROJECT_FIELDS = ("title", "category", "status", "priority", "supervisor", "site")
_TASK_FIELDS = ("title", "status", "priority", "supervisor", "site", "commentary")
_DELIVERABLE_FIELDS = ("title", "status", "percent_complete", "time_allocated", "time_spent")


def _str(val) -> str:
    """Normalise a value to string for comparison."""
    if val is None:
        return ""
    if isinstance(val, date):
        return val.isoformat()
    return str(val).strip()


# ── Core diff logic ────────────────────────────────────────────────────────────

def _diff_fields(old_obj, new_obj, field_names: tuple[str, ...]) -> list[FieldChange]:
    """Compare named attributes on two objects, returning changes."""
    changes: list[FieldChange] = []
    for f in field_names:
        old_val = _str(getattr(old_obj, f, ""))
        new_val = _str(getattr(new_obj, f, ""))
        if old_val != new_val:
            changes.append(FieldChange(field=f, old=old_val, new=new_val))
    return changes


def diff_profiles(old: Profile, new: Profile) -> SnapshotDiff:
    """Compare two Profile trees and return all entity-level changes."""
    result = SnapshotDiff()

    # Index old entities by ID
    old_projects = {p.id: p for p in old.projects}
    new_projects = {p.id: p for p in new.projects}

    old_tasks = {t.id: t for t in old.all_tasks}
    new_tasks = {t.id: t for t in new.all_tasks}

    old_deliverables = {}
    for t in old.all_tasks:
        for d in t.deliverables:
            old_deliverables[d.id] = d

    new_deliverables = {}
    for t in new.all_tasks:
        for d in t.deliverables:
            new_deliverables[d.id] = d

    # --- Projects ---
    for pid in sorted(set(old_projects) | set(new_projects)):
        o = old_projects.get(pid)
        n = new_projects.get(pid)
        if o is None and n is not None:
            result.changes.append(EntityChange("added", "project", pid, n.title))
        elif o is not None and n is None:
            result.changes.append(EntityChange("removed", "project", pid, o.title))
        elif o is not None and n is not None:
            fc = _diff_fields(o, n, _PROJECT_FIELDS)
            if fc:
                result.changes.append(EntityChange("modified", "project", pid, n.title, fc))

    # --- Tasks ---
    for tid in sorted(set(old_tasks) | set(new_tasks)):
        o = old_tasks.get(tid)
        n = new_tasks.get(tid)
        if o is None and n is not None:
            result.changes.append(EntityChange("added", "task", tid, n.title))
        elif o is not None and n is None:
            result.changes.append(EntityChange("removed", "task", tid, o.title))
        elif o is not None and n is not None:
            fc = _diff_fields(o, n, _TASK_FIELDS)
            if fc:
                result.changes.append(EntityChange("modified", "task", tid, n.title, fc))

    # --- Deliverables ---
    for did in sorted(set(old_deliverables) | set(new_deliverables)):
        o = old_deliverables.get(did)
        n = new_deliverables.get(did)
        if o is None and n is not None:
            result.changes.append(EntityChange("added", "deliverable", did, n.title))
        elif o is not None and n is None:
            result.changes.append(EntityChange("removed", "deliverable", did, o.title))
        elif o is not None and n is not None:
            fc = _diff_fields(o, n, _DELIVERABLE_FIELDS)
            if fc:
                result.changes.append(EntityChange("modified", "deliverable", did, n.title, fc))

    return result


def load_previous_snapshot(company: str, reports_dir: Path, lookback_days: int = 7,
                           today: date | None = None) -> Profile | None:
    """Load the most recent prior ``domain.json`` snapshot from reports/.

    Falls back to the current ``domain.json`` if no snapshot is found.
    Actually, snapshots are .xlsx files — we need to look for domain.json
    in the data/ directory.  Instead, we compare against the saved
    domain.json from before the current pipeline run.

    This function looks for the *current* ``domain.json`` and returns it
    as the "previous" state.  The caller should invoke this **before** any
    mutations in the pipeline so it captures the pre-mutation state.
    """
    from helpers.io.paths import data_dir
    json_path = data_dir(company) / "domain.json"
    if json_path.exists():
        try:
            profile, _ = load_profile_json(json_path)
            return profile
        except Exception:
            return None
    return None
