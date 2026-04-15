# Task 10: Create RowReader for Workbook Cell Access

**Audit ID**: C-13  
**Effort**: Medium  
**Phase**: 2 — Separation of Concerns

---

## Objective

Create a thin `RowReader` abstraction that replaces repeated `ws.cell(row=r, column=column_index(sheet, "Field") + 1).value` patterns in `task_ops.py`. This eliminates the manual `column_index() + 1` calculations and `clean()` wrapping scattered throughout the module.

---

## Audit Reference

> **C-13: task_ops Module Does Cell-Level Workbook Navigation (357 Lines)**
>
> Repeatedly uses `ws.cell(row=r, column=col_idx).value` with manual `column_index() + 1` calculations. No abstraction layer. `column_index() + 1` appears 16+ times.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/persistence/row_reader.py` | **CREATE** — thin cell access abstraction |
| `helpers/commands/task_ops.py` | **MODIFY** — use RowReader instead of manual cell access |

---

## Current Code

### Repeated pattern in task_ops.py

**Pattern 1: Column lookup + 1 (appears 16+ times)**
```python
task_proj_col = column_index(SHEET_TASKS, "Project ID") + 1
task_status_col = column_index(SHEET_TASKS, "Status") + 1
```

**Pattern 2: Cell read with clean() (appears throughout)**
```python
if clean(task_ws.cell(row=r, column=1).value) == task_id:
    project_id = clean(task_ws.cell(row=r, column=task_proj_col).value)
```

**Pattern 3: Cell write (appears in mutation functions)**
```python
proj_ws.cell(row=r, column=proj_status_col, value="Completed")
proj_ws.cell(row=r, column=proj_cat_col, value="Completed")
proj_ws.cell(row=r, column=proj_date_col, value=date.today())
```

**Pattern 4: Row scan by ID (appears in every CRUD function)**
```python
for r in range(2, task_ws.max_row + 1):
    if clean(task_ws.cell(row=r, column=1).value) == target_id:
        # ... do something with this row
        break
```

### Example: `_check_project_completion_wb()` (lines ~363–418)

```python
task_ws = wb[SHEET_TASKS]
task_proj_col = column_index(SHEET_TASKS, "Project ID") + 1
task_status_col = column_index(SHEET_TASKS, "Status") + 1

project_id = None
for r in range(2, task_ws.max_row + 1):
    if clean(task_ws.cell(row=r, column=1).value) == task_id:
        project_id = clean(task_ws.cell(row=r, column=task_proj_col).value)
        break

# ... later ...

for r in range(2, task_ws.max_row + 1):
    pid = clean(task_ws.cell(row=r, column=task_proj_col).value)
    if pid == project_id:
        has_tasks = True
        st = clean(task_ws.cell(row=r, column=task_status_col).value)
        # ...

proj_ws = wb[SHEET_PROJECTS]
proj_status_col = column_index(SHEET_PROJECTS, "Status") + 1
proj_cat_col = column_index(SHEET_PROJECTS, "Category") + 1
proj_date_col = column_index(SHEET_PROJECTS, "Date Completed") + 1

for r in range(2, proj_ws.max_row + 1):
    if clean(proj_ws.cell(row=r, column=1).value) == project_id:
        proj_ws.cell(row=r, column=proj_status_col, value="Completed")
        # ...
```

---

## Required Changes

### Step 1: Create `helpers/persistence/row_reader.py`

```python
"""Thin abstraction for reading/writing workbook rows by column name."""

from __future__ import annotations

from typing import Any

from openpyxl.worksheet.worksheet import Worksheet

from helpers.schema.columns import column_index


def _clean(value: Any) -> str:
    """Normalize a cell value to a stripped string."""
    if value is None:
        return ""
    return str(value).strip()


class SheetAccessor:
    """Read/write cells by column name instead of index.
    
    Usage:
        accessor = SheetAccessor(ws, sheet_name)
        row = accessor.find_row("T-001")             # find row by ID
        status = accessor.get(row, "Status")          # read cell
        accessor.set(row, "Status", "Completed")      # write cell
    """

    def __init__(self, ws: Worksheet, sheet_name: str) -> None:
        self.ws = ws
        self._sheet_name = sheet_name
        self._col_cache: dict[str, int] = {}

    def _col(self, field: str) -> int:
        """Return 1-based column index for *field*, with caching."""
        if field not in self._col_cache:
            self._col_cache[field] = column_index(self._sheet_name, field) + 1
        return self._col_cache[field]

    def get(self, row: int, field: str) -> str:
        """Read and clean a cell value by row number and field name."""
        return _clean(self.ws.cell(row=row, column=self._col(field)).value)

    def get_raw(self, row: int, field: str) -> Any:
        """Read a cell value without cleaning (preserves type)."""
        return self.ws.cell(row=row, column=self._col(field)).value

    def set(self, row: int, field: str, value: Any) -> None:
        """Write a value to a cell by row number and field name."""
        self.ws.cell(row=row, column=self._col(field), value=value)

    def get_id(self, row: int) -> str:
        """Read the ID from column 1 (cleaned)."""
        return _clean(self.ws.cell(row=row, column=1).value)

    def find_row(self, target_id: str) -> int | None:
        """Find the 1-based row number for *target_id* in column 1."""
        for r in range(2, self.ws.max_row + 1):
            if self.get_id(r) == target_id:
                return r
        return None

    def iter_rows(self):
        """Yield 1-based row numbers for all data rows (skips header)."""
        for r in range(2, self.ws.max_row + 1):
            if self.get_id(r):
                yield r
```

### Step 2: Refactor `helpers/commands/task_ops.py`

Replace manual cell access with `SheetAccessor`. Example for `_check_project_completion_wb()`:

**Before:**
```python
task_ws = wb[SHEET_TASKS]
task_proj_col = column_index(SHEET_TASKS, "Project ID") + 1
task_status_col = column_index(SHEET_TASKS, "Status") + 1

for r in range(2, task_ws.max_row + 1):
    if clean(task_ws.cell(row=r, column=1).value) == task_id:
        project_id = clean(task_ws.cell(row=r, column=task_proj_col).value)
        break
```

**After:**
```python
tasks = SheetAccessor(wb[SHEET_TASKS], SHEET_TASKS)
row = tasks.find_row(task_id)
if not row:
    return
project_id = tasks.get(row, "Project ID")
```

Apply similar refactoring to all functions in `task_ops.py` that use the manual pattern. Key functions to refactor:

- `delete_task()` — row scan + cascade delete
- `_check_project_completion_wb()` — multi-sheet scan + update
- `set_status()` — row scan + update + completion check
- `set_priority()` — row scan + update
- `add_task()` — row write

---

## Acceptance Criteria

1. `helpers/persistence/row_reader.py` exists with `SheetAccessor` class
2. No `column_index(SHEET_*, "Field") + 1` patterns remain in `task_ops.py`
3. No raw `ws.cell(row=r, column=N)` calls remain in `task_ops.py` (use `SheetAccessor` instead)
4. All `task_ops` functions produce identical results
5. `pytest tests/` passes
6. The `SheetAccessor` class is independently testable with a mock worksheet

---

## Constraints

- The `SheetAccessor` lives in `helpers/persistence/` — it depends on `helpers/schema/columns.py`
- Do NOT change `workbook_writer.py` in this task — it can adopt `SheetAccessor` later
- Do NOT change the public API of any `task_ops` function
- The `_clean()` function in `row_reader.py` should match the existing `clean()` behavior in `task_ops.py`
- Keep `SheetAccessor` minimal — it's an accessor, not an ORM
