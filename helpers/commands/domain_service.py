"""Domain-first mutation service for the GUI.

All GUI mutations route through this class.  It mutates the in-memory
Profile tree, then persists via ``contract.save()`` which dual-writes
to both ``domain.json`` and the Excel workbook.

Pages call ``app.service.<method>(...)`` — never touch the workbook directly.
"""

from __future__ import annotations

from datetime import date
from typing import Callable

from openpyxl.workbook import Workbook

from helpers.domain.profile import Profile
from helpers.domain.project import Project
from helpers.domain.task import Task
from helpers.domain.deliverable import Deliverable
from helpers.schema.ids import (
    next_project_id_from_profile,
    next_task_id_from_profile,
    next_deliverable_id_from_profile,
)
from helpers.persistence.contract import save as _dual_save
from helpers.attachments.notes import delete_notes
from helpers.attachments.links import delete_link
from helpers.attachments.service import delete_attachments
from helpers.scheduling.engine import compute_schedule
from helpers.validation import (
    validate_project,
    validate_task,
    validate_deliverable,
    ValidationError,
)
from helpers.domain.rules import should_auto_complete_project, should_reopen_project, reopen_category
from helpers.config.loader import default_category, default_priority, default_status, terminal_statuses, terminal_categories, reopen_status


class DomainService:
    """Mediates between GUI actions and the domain + persistence layers.

    After every mutation the service calls ``_persist()`` which writes
    the Profile to both domain.json and the workbook in a single pass.
    Timelines and Gantt sheets are rebuilt automatically during that save.
    """

    def __init__(
        self,
        profile: Profile,
        wb: Workbook,
        on_persist: Callable[[], None] | None = None,
    ):
        self._profile = profile
        self._wb = wb
        self._on_persist = on_persist  # optional callback (e.g. app.mark_dirty)

    # ── property access ────────────────────────────────────────────────────

    @property
    def profile(self) -> Profile:
        """The active profile."""
        return self._profile

    @profile.setter
    def profile(self, value: Profile) -> None:
        self._profile = value

    @property
    def wb(self) -> Workbook:
        """The active workbook."""
        return self._wb

    @wb.setter
    def wb(self, value: Workbook) -> None:
        self._wb = value

    # ── persistence ────────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Dual-write the profile to JSON and workbook."""
        _dual_save(self._profile, self._wb)
        if self._on_persist:
            self._on_persist()

    def reschedule(self, reference_date: date | None = None) -> None:
        """Recompute the daily task schedule and persist."""
        compute_schedule(self._profile, reference_date)
        self._persist()

    # ═══════════════════════════════════════════════════════════════════════
    #  PROJECT CRUD
    # ═══════════════════════════════════════════════════════════════════════

    def add_project(self, data: dict) -> Project:
        """Create a new project and add it to the profile.

        *data* uses domain attribute names::

            {"title": "...", "category": "Weekly", "description": "...", ...}

        Raises :class:`~helpers.validation.ValidationError` on invalid data.
        """
        self._validate_or_raise(validate_project, data)
        pid = next_project_id_from_profile(self._profile)
        project = Project(
            id=pid,
            project_id=pid,
            title=data.get("title", ""),
            category=data.get("category", default_category()),
            description=data.get("description", ""),
            status=data.get("status", default_status()),
            supervisor=data.get("supervisor", ""),
            site=data.get("site", ""),
            priority=data.get("priority", default_priority()),
            notes=data.get("notes", ""),
            start=data.get("start"),
            end=data.get("end"),
            deadline=data.get("deadline"),
            date_completed=data.get("date_completed"),
        )
        self._profile.add_project(project)
        self._persist()
        return project

    def edit_project(self, project_id: str, data: dict) -> Project | None:
        """Update fields on an existing project.

        Only keys present in *data* are changed.
        Raises :class:`~helpers.validation.ValidationError` on invalid data.
        """
        project = self._profile.find_project(project_id)
        if not project:
            return None
        self._validate_or_raise(validate_project, data, partial=True)
        _apply_attrs(project, data)
        self._persist()
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project and cascade-delete all its tasks + deliverables."""
        project = self._profile.find_project(project_id)
        if not project:
            return False
        # Cascade: clean up notes/links/attachments for each task
        for task in list(project.tasks):
            self._cleanup_task_files(task.id)
        self._profile.remove_project(project_id)
        self._persist()
        return True

    # ═══════════════════════════════════════════════════════════════════════
    #  TASK CRUD
    # ═══════════════════════════════════════════════════════════════════════

    def add_task(self, project_id: str, data: dict) -> Task | None:
        """Create a new task under *project_id*.

        *data* uses domain attribute names::

            {"title": "...", "supervisor": "...", "priority": 2, ...}

        Raises :class:`~helpers.validation.ValidationError` on invalid data.
        """
        self._validate_or_raise(validate_task, data)
        project = self._profile.find_project(project_id)
        if not project:
            return None

        tid = next_task_id_from_profile(self._profile)
        task = Task(
            id=tid,
            task_id=tid,
            project_id=project_id,
            title=data.get("title", ""),
            supervisor=data.get("supervisor", ""),
            site=data.get("site", ""),
            description=data.get("description", ""),
            commentary=data.get("commentary", ""),
            status=data.get("status", default_status()),
            priority=data.get("priority", default_priority()),
            start=data.get("start"),
            end=data.get("end"),
            deadline=data.get("deadline"),
            date_completed=data.get("date_completed"),
        )
        project.add_task(task)
        self._persist()
        return task

    def edit_task(self, task_id: str, data: dict) -> Task | None:
        """Update fields on an existing task.

        Raises :class:`~helpers.validation.ValidationError` on invalid data.
        """
        task = self._profile.find_task_global(task_id)
        if not task:
            return None

        self._validate_or_raise(validate_task, data, partial=True)
        _apply_attrs(task, data)
        # Stamp date_completed when status changed to terminal via edit
        if data.get("status") in terminal_statuses() and not task.date_completed:
            task.date_completed = date.today()
        # Auto-complete parent project if all sibling tasks are now done
        self._check_project_completion(task)
        self._persist()
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task and cascade-delete its deliverables + file associations."""
        task = self._profile.find_task_global(task_id)
        if not task:
            return False

        self._cleanup_task_files(task.id)

        # Remove from parent project
        parent = task.parent
        if parent and hasattr(parent, "remove_task"):
            parent.remove_task(task_id)

        self._persist()
        return True

    def move_task(self, task_id: str, new_project_id: str) -> bool:
        """Move a task from its current project to *new_project_id*."""
        task = self._profile.find_task_global(task_id)
        new_project = self._profile.find_project(new_project_id)
        if not task or not new_project:
            return False

        old_parent = task.parent
        if old_parent and hasattr(old_parent, "remove_task"):
            old_parent.remove_task(task_id)

        task.project_id = new_project_id
        new_project.add_task(task)
        self._persist()
        return True

    # ═══════════════════════════════════════════════════════════════════════
    #  DELIVERABLE CRUD
    # ═══════════════════════════════════════════════════════════════════════

    def add_deliverable(self, task_id: str, data: dict) -> Deliverable | None:
        """Create a new deliverable under *task_id*.

        Raises :class:`~helpers.validation.ValidationError` on invalid data.
        """
        self._validate_or_raise(validate_deliverable, data)
        task = self._profile.find_task_global(task_id)
        if not task:
            return None

        did = next_deliverable_id_from_profile(self._profile)
        deliverable = Deliverable(
            id=did,
            deliverable_id=did,
            task_id=task_id,
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", default_status()),
            start=data.get("start"),
            end=data.get("end"),
            deadline=data.get("deadline"),
            percent_complete=data.get("percent_complete", 0),
            time_allocated=data.get("time_allocated"),
            time_spent=data.get("time_spent"),
        )
        task.add_deliverable(deliverable)
        self._persist()
        return deliverable

    def edit_deliverable(self, deliverable_id: str, data: dict) -> Deliverable | None:
        """Update fields on an existing deliverable.

        Raises :class:`~helpers.validation.ValidationError` on invalid data.
        """
        deliv = self._find_deliverable(deliverable_id)
        if not deliv:
            return None
        self._validate_or_raise(validate_deliverable, data, partial=True)
        _apply_attrs(deliv, data)
        self._persist()
        return deliv

    def delete_deliverable(self, deliverable_id: str) -> bool:
        """Delete a deliverable."""
        deliv = self._find_deliverable(deliverable_id)
        if not deliv:
            return False
        parent_task = deliv.parent
        if parent_task and hasattr(parent_task, "remove_deliverable"):
            parent_task.remove_deliverable(deliverable_id)
        self._persist()
        return True

    # ═══════════════════════════════════════════════════════════════════════
    #  QUICK SETTERS
    # ═══════════════════════════════════════════════════════════════════════

    def set_status(self, item_id: str, status: str) -> bool:
        """Set status on any item (project, task, or deliverable) by ID prefix."""
        node = self._find_any(item_id)
        if not node:
            return False
        node.status = status
        # Stamp date_completed when completing a task or project
        if status in terminal_statuses() and not getattr(node, "date_completed", True):
            node.date_completed = date.today()
        # Auto-complete parent project if all sibling tasks are now done
        if isinstance(node, Task):
            self._check_project_completion(node)
        self._persist()
        return True

    def set_priority(self, item_id: str, priority: int) -> bool:
        """Set priority on a task by ID."""
        node = self._find_any(item_id)
        if not node:
            return False
        if hasattr(node, "priority"):
            node.priority = priority
            self._persist()
            return True
        return False

    # ═══════════════════════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _check_project_completion(self, task: Task) -> None:
        """Auto-complete or reopen the parent project based on task statuses.

        - If all sibling tasks are Completed → auto-complete the project.
        - If the project was Completed but a task is no longer Completed
          → reopen the project back to Ongoing.
        """
        parent = task.parent
        if not isinstance(parent, Project):
            return
        if not parent.tasks:
            return
        statuses = [t.status for t in parent.tasks]
        if should_auto_complete_project(statuses):
            if not parent.date_completed:
                parent.status = next(iter(terminal_statuses()))
                parent.category = next(iter(terminal_categories()))
                parent.date_completed = date.today()
        elif should_reopen_project(parent.category):
            # A task was reopened — revert the project
            parent.status = reopen_status()
            parent.category = reopen_category()
            parent.date_completed = None

    def _find_any(self, item_id: str):
        """Resolve any P-/T-/D- ID to the corresponding domain object."""
        prefix = item_id.split("-")[0] if "-" in item_id else ""
        if prefix == "P":
            return self._profile.find_project(item_id)
        elif prefix == "T":
            return self._profile.find_task_global(item_id)
        elif prefix == "D":
            return self._find_deliverable(item_id)
        return None

    def _find_deliverable(self, deliverable_id: str) -> Deliverable | None:
        """Search all tasks for a deliverable by ID."""
        for task in self._profile.all_tasks:
            d = task.find_deliverable(deliverable_id)
            if d:
                return d
        return None

    @staticmethod
    def _cleanup_task_files(task_id: str) -> None:
        """Remove notes, links, and attachments associated with a task ID."""
        delete_notes(task_id)
        delete_link(task_id)
        delete_attachments(task_id)

    @staticmethod
    def _validate_or_raise(validator, data: dict, *, partial: bool = False) -> None:
        """Run *validator(data)* and raise :class:`ValidationError` if errors.

        When *partial* is True, skip validation for keys not present in *data*
        (used for edit operations where only changed fields are supplied).
        """
        if partial and "title" not in data:
            # For partial edits, inject a placeholder title so the "title
            # required" check doesn't fire on fields-only edits.
            data_for_check = {"title": "(unchanged)", **data}
        else:
            data_for_check = data
        errors = validator(data_for_check)
        if errors:
            raise ValidationError(errors)


# ── Attribute application helper ───────────────────────────────────────────────

# Attributes that map directly from data dict keys to domain object attrs.
_TASK_ATTRS = frozenset({
    "title", "supervisor", "site", "description", "commentary",
    "status", "priority", "start", "end", "deadline", "date_completed",
    "scheduled_date",
})
_DELIVERABLE_ATTRS = frozenset({
    "title", "description", "status", "start", "end", "deadline",
    "percent_complete", "time_allocated", "time_spent",
})
_PROJECT_ATTRS = frozenset({
    "title", "category", "description", "status", "priority",
    "supervisor", "site", "notes", "date_completed",
    "start", "end", "deadline",
})


def _apply_attrs(obj, data: dict) -> None:
    """Set attributes on *obj* for keys present in *data*."""
    if isinstance(obj, Task):
        allowed = _TASK_ATTRS
    elif isinstance(obj, Deliverable):
        allowed = _DELIVERABLE_ATTRS
    elif isinstance(obj, Project):
        allowed = _PROJECT_ATTRS
    else:
        allowed = set(data.keys())

    for key, value in data.items():
        if key in allowed and hasattr(obj, key):
            setattr(obj, key, value)
