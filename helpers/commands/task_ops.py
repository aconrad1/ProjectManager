"""Task / Project / Deliverable operations — add, edit, delete, set status/priority.

All commands operate via ID-based lookups on the new 6-sheet schema
(Projects / Tasks / Deliverables).

Key convention
--------------
Functions accept data dicts using **either** Excel column names (e.g.
``"Status Commentary"``, ``"% Complete"``) **or** Python attribute names
(e.g. ``"commentary"``, ``"percent_complete"``).  The ``_norm()`` helper
normalises both forms to Excel column names before writing to the workbook.
DomainService (GUI path) uses Python attribute names; agents / CLI can use
either.
"""

from __future__ import annotations

from datetime import date

from helpers.commands.registry import register
from helpers.data.completions import _is_completed
from helpers.attachments.notes import delete_notes
from helpers.attachments.links import delete_link
from helpers.attachments.service import delete_attachments
from helpers.domain.rules import should_auto_complete_project, should_reopen_project

from helpers.domain.task import Task
from helpers.domain.project import Project
from helpers.domain.deliverable import Deliverable
from helpers.schema.sheets import SHEET_PROJECTS, SHEET_TASKS, SHEET_DELIVERABLES
from helpers.schema.columns import (
    PROJECTS_COLUMNS, TASKS_COLUMNS, DELIVERABLES_COLUMNS,
)
from helpers.persistence.row_reader import SheetAccessor
from helpers.persistence.workbook_writer import (
    add_project_row,
    add_task_row,
    add_deliverable_row,
    update_project_row,
    update_task_row,
    update_deliverable_row,
    delete_row_by_id,
)


# ── Post-mutation hook ─────────────────────────────────────────────────────────
# When set, called after every workbook mutation so the caller (e.g. CLI)
# doesn't have to remember to resync JSON manually.
# Signature: _post_mutate(wb) -> None

_post_mutate = None


def set_post_mutate_hook(fn) -> None:
    """Register a callback that fires after every task_ops mutation.

    Typical usage (in CLI boot)::

        from helpers.commands.task_ops import set_post_mutate_hook
        set_post_mutate_hook(lambda wb: resync_and_save(wb))
    """
    global _post_mutate
    _post_mutate = fn


def _notify(wb) -> None:
    """Fire the post-mutation hook if one is registered."""
    if _post_mutate is not None:
        _post_mutate(wb)


# ── Key normalisation ──────────────────────────────────────────────────────────

# Maps Python attribute names → Excel column names.
# Allows callers to use either convention interchangeably.
_ATTR_TO_COLUMN: dict[str, str] = {
    # Projects
    "project_id":       "Project ID",
    "category":         "Category",
    "supervisor":       "Supervisor",
    "site":             "Site",
    "description":      "Description",
    "status":           "Status",
    "priority":         "Priority",
    "start":            "Start Date",
    "end":              "End Date",
    "deadline":         "Deadline",
    "date_completed":   "Date Completed",
    "notes":            "Notes",
    # Tasks
    "task_id":          "Task ID",
    "title":            "Title",
    "commentary":       "Status Commentary",
    "scheduled_date":   "Scheduled Date",
    # Deliverables
    "deliverable_id":   "Deliverable ID",
    "percent_complete": "% Complete",
    "time_allocated":   "Time Allocated",
    "time_spent":       "Time Spent",
}


def _norm(data: dict) -> dict:
    """Return *data* with attribute-name keys translated to Excel column names.

    Keys that are already Excel column names pass through unchanged.
    Unknown keys are preserved so callers can detect typos via KeyError.
    """
    return {_ATTR_TO_COLUMN.get(k, k): v for k, v in data.items()}


# ── Project / Task / Deliverable creation ──────────────────────────────────

@register("add_project")
def add_project(wb, data: dict) -> Project:
    """Create a new project from form *data* and write to Projects sheet."""
    d = _norm(data)
    project = Project(
        id="",
        title=d.get("Title", ""),
        category=d.get("Category", "Ongoing"),
        description=d.get("Description", ""),
        status=d.get("Status", "Not Started"),
        supervisor=d.get("Supervisor", ""),
        site=d.get("Site", ""),
        priority=d.get("Priority", 3),
        notes=d.get("Notes", ""),
        start=d.get("Start Date"),
        end=d.get("End Date"),
        deadline=d.get("Deadline"),
        date_completed=d.get("Date Completed"),
    )
    add_project_row(wb, project)
    _sync_derived_sheets(wb)
    _notify(wb)
    return project


@register("add_task")
def add_task(wb, project_id: str, data: dict, *, date_completed=None) -> Task:
    """Add a task under *project_id* (P-NNN) and write to the Tasks sheet."""
    d = _norm(data)
    task = Task(
        id="",
        title=d.get("Title", ""),
        project_id=project_id,
        supervisor=d.get("Supervisor", d.get("Project Supervisor", "")),
        site=d.get("Site", ""),
        description=d.get("Description", d.get("Project Description", "")),
        commentary=d.get("Status Commentary", ""),
        status=d.get("Status", "Not Started"),
        priority=d.get("Priority", 3),
        date_completed=date_completed,
    )
    add_task_row(wb, task)
    _sync_derived_sheets(wb)
    _notify(wb)
    return task


@register("add_deliverable")
def add_deliverable(wb, task_id: str, data: dict) -> Deliverable:
    """Create a new deliverable under *task_id* and write to Deliverables sheet."""
    d = _norm(data)
    deliv = Deliverable(
        id="",
        title=d.get("Title", ""),
        task_id=task_id,
        description=d.get("Description", ""),
        status=d.get("Status", "Not Started"),
        start=d.get("Start Date"),
        end=d.get("End Date"),
        deadline=d.get("Deadline"),
        percent_complete=d.get("% Complete", 0),
        time_allocated=d.get("Time Allocated"),
        time_spent=d.get("Time Spent"),
    )
    add_deliverable_row(wb, deliv)
    _sync_derived_sheets(wb)
    _notify(wb)
    return deliv


@register("edit_project")
def edit_project(wb, project_or_id, data: dict | None = None) -> bool:
    """Edit a project by domain Project object or by ID + data dict.

    Signatures:
        edit_project(wb, project: Project)
        edit_project(wb, project_id: str, data: dict)
    """
    if isinstance(project_or_id, Project):
        result = update_project_row(wb, project_or_id)
        if result:
            _sync_derived_sheets(wb)
            _notify(wb)
        return result

    # ID-based path: edit_project(wb, "P-001", {"Status": "In Progress", ...})
    project_id = project_or_id
    if data is None:
        return False
    _update_fields_by_id(wb, SHEET_PROJECTS, PROJECTS_COLUMNS, project_id, _norm(data))
    _sync_derived_sheets(wb)
    _notify(wb)
    return True


@register("edit_task")
def edit_task(wb, task_or_id, data: dict | None = None) -> bool:
    """Edit a task by domain Task object or by ID + data dict.

    Signatures:
        edit_task(wb, task: Task)
        edit_task(wb, task_id: str, data: dict)

    When the Title field changes, notes, links, and attachments are
    automatically re-keyed to the new title.
    """
    if isinstance(task_or_id, Task):
        result = update_task_row(wb, task_or_id)
        if result:
            _sync_derived_sheets(wb)
            _notify(wb)
        return result

    # ID-based path: edit_task(wb, "T-001", {"Status": "Completed", ...})
    task_id = task_or_id
    if data is None:
        return False

    data = _norm(data)

    _update_fields_by_id(wb, SHEET_TASKS, TASKS_COLUMNS, task_id, data)
    _sync_derived_sheets(wb)
    _notify(wb)
    return True


@register("edit_deliverable")
def edit_deliverable(wb, deliv_or_id, data: dict | None = None) -> bool:
    """Edit a deliverable by domain object or by ID + data dict.

    Signatures:
        edit_deliverable(wb, deliverable: Deliverable)
        edit_deliverable(wb, deliverable_id: str, data: dict)
    """
    if isinstance(deliv_or_id, Deliverable):
        result = update_deliverable_row(wb, deliv_or_id)
        if result:
            _sync_derived_sheets(wb)
            _notify(wb)
        return result

    deliverable_id = deliv_or_id
    if data is None:
        return False
    _update_fields_by_id(wb, SHEET_DELIVERABLES, DELIVERABLES_COLUMNS, deliverable_id, _norm(data))
    _sync_derived_sheets(wb)
    _notify(wb)
    return True


@register("delete_task")
def delete_task(wb, task_id: str) -> None:
    """Delete a task by ID (T-NNN), cascading to child deliverables."""
    # Find and delete child deliverables first
    if SHEET_DELIVERABLES in wb.sheetnames:
        deliverables = SheetAccessor(wb[SHEET_DELIVERABLES], SHEET_DELIVERABLES)
        to_delete = []
        for row in deliverables.iter_rows():
            if deliverables.get(row, "Task ID") == task_id:
                did = deliverables.get_id(row)
                if did:
                    to_delete.append(did)
        for did in to_delete:
            delete_row_by_id(wb, SHEET_DELIVERABLES, did)

    # Find task title for attachment cleanup
    if SHEET_TASKS in wb.sheetnames:
        tasks = SheetAccessor(wb[SHEET_TASKS], SHEET_TASKS)
        if tasks.find_row(task_id):
            delete_notes(task_id)
            delete_link(task_id)
            delete_attachments(task_id)

    delete_row_by_id(wb, SHEET_TASKS, task_id)
    _sync_derived_sheets(wb)
    _notify(wb)


@register("delete_project")
def delete_project(wb, project_id: str) -> None:
    """Delete a project and cascade-delete all its tasks + deliverables."""
    if SHEET_TASKS in wb.sheetnames:
        tasks = SheetAccessor(wb[SHEET_TASKS], SHEET_TASKS)
        task_ids = []
        for row in tasks.iter_rows():
            if tasks.get(row, "Project ID") == project_id:
                tid = tasks.get_id(row)
                if tid:
                    task_ids.append(tid)
        for tid in task_ids:
            delete_task(wb, tid)

    delete_row_by_id(wb, SHEET_PROJECTS, project_id)
    _sync_derived_sheets(wb)
    _notify(wb)


@register("delete_deliverable")
def delete_deliverable(wb, deliverable_id: str) -> None:
    """Delete a deliverable by ID."""
    delete_row_by_id(wb, SHEET_DELIVERABLES, deliverable_id)
    _sync_derived_sheets(wb)
    _notify(wb)


@register("set_status")
def set_status(wb, item_id: str, new_status: str) -> None:
    """Set the Status field on a project, task, or deliverable by ID."""
    _set_field_by_id(wb, item_id, "Status", new_status)
    if item_id.startswith("T-"):
        # Stamp Date Completed when completing a task
        if _is_completed(new_status):
            tasks = SheetAccessor(wb[SHEET_TASKS], SHEET_TASKS)
            row = tasks.find_row(item_id)
            if row and tasks.get_raw(row, "Date Completed") is None:
                tasks.set(row, "Date Completed", date.today())
        # Auto-complete or reopen parent project
        _check_project_completion_wb(wb, item_id)
    _notify(wb)


@register("set_priority")
def set_priority(wb, item_id: str, new_priority: int) -> None:
    """Set the Priority field on a project or task by ID."""
    _set_field_by_id(wb, item_id, "Priority", new_priority)
    _notify(wb)


def _set_field_by_id(wb, item_id: str, field_name: str, value) -> None:
    """Find a row by ID and set a specific field."""
    prefix = item_id.split("-")[0]
    sheet_map = {"P": SHEET_PROJECTS, "T": SHEET_TASKS, "D": SHEET_DELIVERABLES}
    sheet_name = sheet_map.get(prefix)
    if not sheet_name or sheet_name not in wb.sheetnames:
        return
    accessor = SheetAccessor(wb[sheet_name], sheet_name)
    row = accessor.find_row(item_id)
    if row:
        accessor.set(row, field_name, value)


def _check_project_completion_wb(wb, task_id: str) -> None:
    """Auto-complete or reopen the parent project based on task statuses.

    - If all tasks are completed and the project has no Date Completed,
      stamps it as Completed.
    - If not all tasks are completed but the project is in the Completed
      category, reopens it back to Ongoing / In Progress.
    """
    if SHEET_TASKS not in wb.sheetnames or SHEET_PROJECTS not in wb.sheetnames:
        return

    tasks = SheetAccessor(wb[SHEET_TASKS], SHEET_TASKS)

    # Find the project ID for this task
    project_id = ""
    task_row = tasks.find_row(task_id)
    if task_row:
        project_id = tasks.get(task_row, "Project ID")
    if not project_id:
        return

    # Collect all task statuses for this project
    statuses: list[str] = []
    for row in tasks.iter_rows():
        pid = tasks.get(row, "Project ID")
        if pid == project_id:
            st = tasks.get(row, "Status")
            statuses.append(st)

    if not statuses:
        return

    projects = SheetAccessor(wb[SHEET_PROJECTS], SHEET_PROJECTS)

    for row in projects.iter_rows():
        if projects.get_id(row) == project_id:
            if should_auto_complete_project(statuses):
                if projects.get_raw(row, "Date Completed") is None:
                    projects.set(row, "Status", "Completed")
                    projects.set(row, "Category", "Completed")
                    projects.set(row, "Date Completed", date.today())
            else:
                cat = projects.get(row, "Category")
                if cat and should_reopen_project(cat):
                    projects.set(row, "Status", "In Progress")
                    projects.set(row, "Category", "Ongoing")
                    projects.set(row, "Date Completed", None)
            return


def _read_field(wb, sheet_name: str, item_id: str, field_name: str) -> str | None:
    """Read a single field value from a row identified by *item_id*."""
    if sheet_name not in wb.sheetnames:
        return None
    accessor = SheetAccessor(wb[sheet_name], sheet_name)
    row = accessor.find_row(item_id)
    if row:
        return accessor.get(row, field_name)
    return None


def _update_fields_by_id(wb, sheet_name: str, columns, item_id: str, data: dict) -> None:
    """Update multiple fields on a row identified by *item_id*."""
    if sheet_name not in wb.sheetnames:
        return
    accessor = SheetAccessor(wb[sheet_name], sheet_name)
    row = accessor.find_row(item_id)
    if row is None:
        return
    # Map data keys to column indices and update
    col_names = {col.name for col in columns}
    for key, value in data.items():
        if key in col_names:
            accessor.set(row, key, value)


@register("move_task_to_project")
def move_task_to_project(wb, task_id: str, new_project_id: str) -> bool:
    """Update a task's Project ID foreign key."""
    if SHEET_TASKS not in wb.sheetnames:
        return False
    accessor = SheetAccessor(wb[SHEET_TASKS], SHEET_TASKS)
    row = accessor.find_row(task_id)
    if row:
        accessor.set(row, "Project ID", new_project_id)
        _sync_derived_sheets(wb)
        _notify(wb)
        return True
    return False


# ── Derived sheet sync ─────────────────────────────────────────────────────

def _sync_derived_sheets(wb) -> None:
    """Rebuild Timelines and Gantt after any mutation."""
    from helpers.schema.timelines import sync_timelines
    from helpers.schema.gantt import build_gantt_sheet
    sync_timelines(wb)
    build_gantt_sheet(wb)

