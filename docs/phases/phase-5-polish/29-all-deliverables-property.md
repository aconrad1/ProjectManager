# Task 29: Add `all_deliverables` Property to Profile

**Audit ID**: N-03  
**Effort**: Tiny  
**Phase**: 5 — Polish

---

## Objective

Add an `all_deliverables` property to the `Profile` class (mirroring the existing `all_tasks` property) and use it in `workbook_writer.py` to replace the triple-nested list comprehension.

---

## Audit Reference

> **N-03: Workbook Writer Uses Triple-Nested List Comprehension**
>
> ```python
> [d for p in profile.projects for t in p.tasks for d in t.deliverables]
> ```
>
> Hard to read. Should add an `all_deliverables` property to `Profile`.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/domain/profile.py` | **MODIFY** — add `all_deliverables` property |
| `helpers/persistence/workbook_writer.py` | **MODIFY** — use `profile.all_deliverables` |

---

## Current Code

### Profile — existing `all_tasks` property (lines ~71–76)

```python
@property
def all_tasks(self) -> list[Task]:
    """Flat list of every task across all projects."""
    result: list[Task] = []
    for p in self.projects:
        result.extend(p.tasks)
    return result
```

### workbook_writer.py — triple-nested comprehension (lines ~178–186)

```python
for sheet_name, columns, writer_fn, items in [
    (SHEET_PROJECTS, PROJECTS_COLUMNS, _write_project_row,
     profile.projects),
    (SHEET_TASKS, TASKS_COLUMNS, _write_task_row,
     [t for p in profile.projects for t in p.tasks]),
    (SHEET_DELIVERABLES, DELIVERABLES_COLUMNS, _write_deliverable_row,
     [d for p in profile.projects for t in p.tasks for d in t.deliverables]),
]:
```

---

## Required Changes

### Step 1: Add `all_deliverables` property to `helpers/domain/profile.py`

```python
@property
def all_deliverables(self) -> list[Deliverable]:
    """Flat list of every deliverable across all projects and tasks."""
    result: list[Deliverable] = []
    for task in self.all_tasks:
        result.extend(task.deliverables)
    return result
```

Place it directly after the `all_tasks` property. Add the `Deliverable` import if not already present.

### Step 2: Use it in `helpers/persistence/workbook_writer.py`

```python
for sheet_name, columns, writer_fn, items in [
    (SHEET_PROJECTS, PROJECTS_COLUMNS, _write_project_row,
     profile.projects),
    (SHEET_TASKS, TASKS_COLUMNS, _write_task_row,
     profile.all_tasks),
    (SHEET_DELIVERABLES, DELIVERABLES_COLUMNS, _write_deliverable_row,
     profile.all_deliverables),
]:
```

---

## Acceptance Criteria

1. `Profile.all_deliverables` property exists and returns a flat list of all deliverables
2. `workbook_writer.py` uses `profile.all_deliverables` instead of the triple comprehension
3. The tasks line also uses `profile.all_tasks` (if not already)
4. `pytest tests/` passes
5. The generated workbook is identical

---

## Constraints

- Follow the same pattern as `all_tasks` — simple, readable loop
- The `Deliverable` type import may need to be added to `profile.py` (use `TYPE_CHECKING` guard if needed to avoid circular imports)
- Do NOT cache the property — it's computed fresh each time (same as `all_tasks`)
