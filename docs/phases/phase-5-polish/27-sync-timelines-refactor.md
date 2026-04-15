# Task 27: Refactor sync_timelines() to Table-Driven Approach

**Audit ID**: N-04  
**Effort**: Medium  
**Phase**: 5 — Polish

---

## Objective

Refactor the three repetitive VLOOKUP sections in `sync_timelines()` (Projects, Tasks, Deliverables) into a loop-driven approach using a configuration table. Eliminate the copy-paste column index lookups.

---

## Audit Reference

> **N-04: sync_timelines() Is 140 Lines of Repetitive Formula Building**
>
> The same VLOOKUP pattern repeats 3 times (Projects, Tasks, Deliverables) with minor variations.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/schema/timelines.py` | **MODIFY** — replace 3 repetitive sections with table-driven loop |

---

## Current Code Structure

### Projects section (lines ~97–108)
```python
proj_range = table_range(SHEET_PROJECTS)
p_title_col  = ci(SHEET_PROJECTS, "Title") + 1
p_start_col  = ci(SHEET_PROJECTS, "Start Date") + 1
p_end_col    = ci(SHEET_PROJECTS, "End Date") + 1
p_dead_col   = ci(SHEET_PROJECTS, "Deadline") + 1
p_status_col = ci(SHEET_PROJECTS, "Status") + 1

for r in range(2, proj_ws.max_row + 1):
    pid = clean(proj_ws.cell(row=r, column=1).value)
    if not pid:
        continue
    # VLOOKUP formula writing...
```

### Tasks section (lines ~109–126) — same pattern
```python
task_range = table_range(SHEET_TASKS)
t_title_col  = ci(SHEET_TASKS, "Title") + 1
t_start_col  = ci(SHEET_TASKS, "Start Date") + 1
t_end_col    = ci(SHEET_TASKS, "End Date") + 1
t_dead_col   = ci(SHEET_TASKS, "Deadline") + 1
t_status_col = ci(SHEET_TASKS, "Status") + 1
t_proj_col   = ci(SHEET_TASKS, "Project ID") + 1
t_sched_col  = ci(SHEET_TASKS, "Scheduled Date") + 1
```

### Deliverables section (lines ~127–150) — same pattern
```python
del_range = table_range(SHEET_DELIVERABLES)
d_title_col  = ci(SHEET_DELIVERABLES, "Title") + 1
d_start_col  = ci(SHEET_DELIVERABLES, "Start Date") + 1
d_end_col    = ci(SHEET_DELIVERABLES, "End Date") + 1
# ... etc.
```

---

## Required Changes

### Define a configuration table and iterate

```python
# Section configurations for the Timelines sheet
_TIMELINE_SECTIONS = [
    {
        "label": "Project",
        "sheet": SHEET_PROJECTS,
        "fields": ["Title", "Start Date", "End Date", "Deadline", "Status"],
    },
    {
        "label": "Task",
        "sheet": SHEET_TASKS,
        "fields": ["Title", "Start Date", "End Date", "Deadline", "Status",
                    "Project ID", "Scheduled Date"],
    },
    {
        "label": "Deliverable",
        "sheet": SHEET_DELIVERABLES,
        "fields": ["Title", "Start Date", "End Date", "Deadline", "Status",
                    "Task ID", "% Complete", "Time Allocated", "Time Spent"],
    },
]


def _write_timeline_section(
    tl_ws, start_row: int, section: dict, source_ws, wb
) -> int:
    """Write VLOOKUP formulas for one entity type.
    
    Returns the next available row after writing.
    """
    sheet_name = section["sheet"]
    data_range = table_range(sheet_name)
    field_cols = {f: ci(sheet_name, f) + 1 for f in section["fields"]}
    
    row = start_row
    for r in range(2, source_ws.max_row + 1):
        item_id = clean(source_ws.cell(row=r, column=1).value)
        if not item_id:
            continue
        
        tl_ws.cell(row=row, column=1, value=section["label"])
        tl_ws.cell(row=row, column=2, value=item_id)
        
        col = 3
        for field_name in section["fields"]:
            field_col = field_cols[field_name]
            formula = f'=IFERROR(VLOOKUP("{item_id}",{data_range},{field_col},FALSE),"")'
            tl_ws.cell(row=row, column=col, value=formula)
            col += 1
        
        row += 1
    
    return row
```

Then the main function becomes:

```python
def sync_timelines(wb) -> None:
    # ... header setup ...
    
    row = 2
    for section in _TIMELINE_SECTIONS:
        if section["sheet"] in wb.sheetnames:
            source_ws = wb[section["sheet"]]
            row = _write_timeline_section(tl_ws, row, section, source_ws, wb)
```

---

## Acceptance Criteria

1. The three repetitive sections are replaced by a single `_write_timeline_section()` function
2. `_TIMELINE_SECTIONS` configuration table defines what fields to write for each entity
3. The generated VLOOKUP formulas are identical to the previous implementation
4. `sync_timelines()` is significantly shorter (from ~140 lines to ~40–50)
5. `pytest tests/test_phase4_gantt_timeline.py` passes
6. Opening the workbook shows the same Timelines sheet content

---

## Constraints

- The VLOOKUP formulas must produce identical results — verify by comparing workbook output
- Do NOT change the Timelines sheet layout (column order, headers)
- The `table_range()` and `ci()` (column_index) helper functions stay unchanged
- If sections have unique behaviors (e.g., Deliverables has extra % Complete columns), the config table must accommodate that via the `fields` list
- This is an internal refactor — the sheet output must be byte-identical
