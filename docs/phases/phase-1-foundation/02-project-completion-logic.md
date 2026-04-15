# Task 2: Extract Duplicate Project Completion Logic

**Audit ID**: C-03  
**Effort**: Small  
**Phase**: 1 — Foundation

---

## Objective

Extract the shared project auto-completion business rule ("if all tasks are Completed, auto-complete the parent project; if a task is reopened, revert the project to Ongoing") from two separate implementations into a single shared function. Both `domain_service.py` (GUI path) and `task_ops.py` (CLI path) must call this shared function.

---

## Audit Reference

> **C-03: Duplicate Project Auto-Completion Logic**
>
> Location 1: `helpers/commands/domain_service.py` — `_check_project_completion()` (22 lines, domain objects)  
> Location 2: `helpers/commands/task_ops.py` — `_check_project_completion_wb()` (49 lines, workbook cells)  
>
> Both implement the same business rule. The domain_service version operates on domain objects. The task_ops version does the same by navigating workbook cells.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/domain/rules.py` | **CREATE** — pure business rule function |
| `helpers/commands/domain_service.py` | **MODIFY** — call shared rule, simplify `_check_project_completion()` |
| `helpers/commands/task_ops.py` | **MODIFY** — call shared rule, simplify `_check_project_completion_wb()` |

---

## Current Code

### DomainService version (lines 332–352 of `helpers/commands/domain_service.py`)

```python
def _check_project_completion(self, task: Task) -> None:
    """Auto-complete or reopen the parent project based on task statuses."""
    parent = task.parent
    if not isinstance(parent, Project):
        return
    if not parent.tasks:
        return
    all_done = all(t.status.strip().lower() == "completed" for t in parent.tasks)
    if all_done:
        if not parent.date_completed:
            parent.status = "Completed"
            parent.category = "Completed"
            parent.date_completed = date.today()
    elif parent.category == "Completed":
        parent.status = "In Progress"
        parent.category = "Ongoing"
        parent.date_completed = None
```

### task_ops version (lines 363–418 of `helpers/commands/task_ops.py`)

```python
def _check_project_completion_wb(wb, task_id: str) -> None:
    """Auto-complete or reopen the parent project based on task statuses."""
    if SHEET_TASKS not in wb.sheetnames or SHEET_PROJECTS not in wb.sheetnames:
        return

    task_ws = wb[SHEET_TASKS]
    task_proj_col = column_index(SHEET_TASKS, "Project ID") + 1
    task_status_col = column_index(SHEET_TASKS, "Status") + 1

    # Find the project ID for this task
    project_id = None
    for r in range(2, task_ws.max_row + 1):
        if clean(task_ws.cell(row=r, column=1).value) == task_id:
            project_id = clean(task_ws.cell(row=r, column=task_proj_col).value)
            break
    if not project_id:
        return

    # Check if all tasks under this project are completed
    all_completed = True
    has_tasks = False
    for r in range(2, task_ws.max_row + 1):
        pid = clean(task_ws.cell(row=r, column=task_proj_col).value)
        if pid == project_id:
            has_tasks = True
            st = clean(task_ws.cell(row=r, column=task_status_col).value)
            if not _is_completed(st):
                all_completed = False
                break

    if not has_tasks:
        return

    proj_ws = wb[SHEET_PROJECTS]
    proj_status_col = column_index(SHEET_PROJECTS, "Status") + 1
    proj_cat_col    = column_index(SHEET_PROJECTS, "Category") + 1
    proj_date_col   = column_index(SHEET_PROJECTS, "Date Completed") + 1

    for r in range(2, proj_ws.max_row + 1):
        if clean(proj_ws.cell(row=r, column=1).value) == project_id:
            if all_completed:
                if proj_ws.cell(row=r, column=proj_date_col).value is None:
                    proj_ws.cell(row=r, column=proj_status_col, value="Completed")
                    proj_ws.cell(row=r, column=proj_cat_col, value="Completed")
                    proj_ws.cell(row=r, column=proj_date_col, value=date.today())
            else:
                cat = clean(proj_ws.cell(row=r, column=proj_cat_col).value)
                if cat and cat.lower() == "completed":
                    proj_ws.cell(row=r, column=proj_status_col, value="In Progress")
                    proj_ws.cell(row=r, column=proj_cat_col, value="Ongoing")
                    proj_ws.cell(row=r, column=proj_date_col, value=None)
            return
```

---

## Required Changes

### Step 1: Create `helpers/domain/rules.py`

Create a pure function that encodes the business rule without any data-store dependency:

```python
"""Pure business rules for the domain model.

These functions encode decisions that apply regardless of whether the caller
is operating on domain objects or workbook cells.
"""

from __future__ import annotations


def should_auto_complete_project(task_statuses: list[str]) -> bool:
    """Return True if all task statuses indicate completion."""
    if not task_statuses:
        return False
    return all(s.strip().lower() == "completed" for s in task_statuses)


def should_reopen_project(project_category: str) -> bool:
    """Return True if a project should be reverted from Completed to Ongoing."""
    return project_category.strip().lower() == "completed"
```

This module must:
- Live in `helpers/domain/` (it's a pure business rule, no persistence dependency)
- Have zero imports from persistence, schema, or UI layers
- Be independently testable

### Step 2: Modify `helpers/commands/domain_service.py`

Replace the inline logic in `_check_project_completion()` with calls to the shared functions:

```python
from helpers.domain.rules import should_auto_complete_project, should_reopen_project

def _check_project_completion(self, task: Task) -> None:
    parent = task.parent
    if not isinstance(parent, Project):
        return
    if not parent.tasks:
        return
    statuses = [t.status for t in parent.tasks]
    if should_auto_complete_project(statuses):
        if not parent.date_completed:
            parent.status = "Completed"
            parent.category = "Completed"
            parent.date_completed = date.today()
    elif should_reopen_project(parent.category):
        parent.status = "In Progress"
        parent.category = "Ongoing"
        parent.date_completed = None
```

### Step 3: Modify `helpers/commands/task_ops.py`

Replace the inline status-check logic in `_check_project_completion_wb()` with calls to the shared functions. The workbook cell navigation stays — only the decision logic changes:

```python
from helpers.domain.rules import should_auto_complete_project, should_reopen_project

def _check_project_completion_wb(wb, task_id: str) -> None:
    # ... (same workbook navigation to collect statuses) ...
    
    # Collect all task statuses for this project
    statuses = []
    for r in range(2, task_ws.max_row + 1):
        pid = clean(task_ws.cell(row=r, column=task_proj_col).value)
        if pid == project_id:
            st = clean(task_ws.cell(row=r, column=task_status_col).value)
            statuses.append(st)
    
    if not statuses:
        return
    
    # ... (navigate to project row) ...
    
    if should_auto_complete_project(statuses):
        if proj_ws.cell(row=r, column=proj_date_col).value is None:
            proj_ws.cell(row=r, column=proj_status_col, value="Completed")
            proj_ws.cell(row=r, column=proj_cat_col, value="Completed")
            proj_ws.cell(row=r, column=proj_date_col, value=date.today())
    elif should_reopen_project(cat):
        proj_ws.cell(row=r, column=proj_status_col, value="In Progress")
        proj_ws.cell(row=r, column=proj_cat_col, value="Ongoing")
        proj_ws.cell(row=r, column=proj_date_col, value=None)
```

---

## Acceptance Criteria

1. `helpers/domain/rules.py` exists with `should_auto_complete_project()` and `should_reopen_project()`
2. Both functions have zero imports from persistence, schema, commands, or UI layers
3. `domain_service._check_project_completion()` calls the shared rule functions
4. `task_ops._check_project_completion_wb()` calls the shared rule functions
5. The business behavior is identical: auto-complete when all done, reopen when task reopened
6. `pytest tests/` passes
7. Both the GUI path (DomainService) and CLI path (task_ops) produce the same results

---

## Constraints

- The new module lives in `helpers/domain/` — it is a pure business rule with no data layer dependencies
- Do NOT change the workbook cell navigation in `task_ops.py` — only extract the decision logic
- Do NOT change the domain object manipulation in `domain_service.py` — only extract the decision logic
- The shared functions take primitive arguments (lists of strings, single strings) — no domain objects or workbook references
- `_is_completed()` in `task_ops.py` can remain as a local helper (it's a status string normalizer), but consider whether `should_auto_complete_project()` subsumes it
