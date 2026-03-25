"""Timelines sheet synchroniser.

Reads Projects / Tasks / Deliverables and writes corresponding rows to
the Timelines sheet.  Uses VLOOKUP formulas or direct cell references so
that updates to the source sheets propagate automatically.
"""

from __future__ import annotations

from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter

from helpers.data.tasks import clean
from helpers.schema.sheets import (
    SHEET_PROJECTS, SHEET_TASKS, SHEET_DELIVERABLES, SHEET_TIMELINES,
    SHEET_META,
)
from helpers.schema.columns import (
    TIMELINES_COLUMNS, headers_for,
    column_index as ci,
)


def _ensure_sheet(wb: Workbook, name: str):
    if name not in wb.sheetnames:
        wb.create_sheet(name)
    return wb[name]


def _write_headers(ws):
    for i, col in enumerate(TIMELINES_COLUMNS, start=1):
        ws.cell(row=1, column=i, value=col.name)


def _clear_data(ws):
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row)


def _vlookup(lookup_val_cell: str, table_range: str, col_idx: int) -> str:
    """Build a VLOOKUP formula string."""
    return f'=IFERROR(VLOOKUP({lookup_val_cell},{table_range},{col_idx},FALSE),"")'


def sync_timelines(wb: Workbook) -> int:
    """Rebuild the Timelines sheet from the three data sheets.

    Returns the number of rows written (excluding header).

    Each Project / Task / Deliverable becomes a row.  Title, dates, and
    status columns are VLOOKUP formulas referencing the source sheets so
    edits in the data sheets propagate to Timelines automatically.
    """
    ws = _ensure_sheet(wb, SHEET_TIMELINES)
    _clear_data(ws)
    _write_headers(ws)

    # Apply sheet metadata
    meta = SHEET_META.get(SHEET_TIMELINES)
    if meta:
        if meta.frozen_pane:
            ws.freeze_panes = meta.frozen_pane
        if meta.tab_color:
            ws.sheet_properties.tabColor = meta.tab_color

    row = 2  # data starts on row 2

    # Helper: determine VLOOKUP table range string for a sheet
    def table_range(sheet_name: str) -> str:
        s = wb[sheet_name] if sheet_name in wb.sheetnames else None
        if s is None:
            return ""
        max_col = get_column_letter(s.max_column)
        return f"'{sheet_name}'!$A:${max_col}"

    # ── Projects ───────────────────────────────────────────────────────────
    if SHEET_PROJECTS in wb.sheetnames:
        proj_ws = wb[SHEET_PROJECTS]
        proj_range = table_range(SHEET_PROJECTS)
        # Column indices in Projects sheet (1-based for VLOOKUP)
        p_title_col  = ci(SHEET_PROJECTS, "Title") + 1
        p_start_col  = ci(SHEET_PROJECTS, "Start Date") + 1
        p_end_col    = ci(SHEET_PROJECTS, "End Date") + 1
        p_dead_col   = ci(SHEET_PROJECTS, "Deadline") + 1
        p_status_col = ci(SHEET_PROJECTS, "Status") + 1

        for r in range(2, proj_ws.max_row + 1):
            pid = clean(proj_ws.cell(row=r, column=1).value)
            if not pid:
                continue
            a_ref = f"$A{row}"
            ws.cell(row=row, column=1, value=pid)           # Item ID
            ws.cell(row=row, column=2, value="Project")      # Item Type
            ws.cell(row=row, column=3).value = f'=IFERROR(VLOOKUP({a_ref},{proj_range},{p_title_col},FALSE),"")'
            ws.cell(row=row, column=4, value="")             # Parent ID (projects have none)
            ws.cell(row=row, column=5).value = f'=IFERROR(VLOOKUP({a_ref},{proj_range},{p_start_col},FALSE),"")'
            ws.cell(row=row, column=6).value = f'=IFERROR(IF(F{row}="","",G{row}-F{row}),"")'  # Duration
            ws.cell(row=row, column=7).value = f'=IFERROR(VLOOKUP({a_ref},{proj_range},{p_end_col},FALSE),"")'
            ws.cell(row=row, column=8).value = f'=IFERROR(VLOOKUP({a_ref},{proj_range},{p_dead_col},FALSE),"")'
            ws.cell(row=row, column=9).value = f'=IFERROR(VLOOKUP({a_ref},{proj_range},{p_status_col},FALSE),"")'
            ws.cell(row=row, column=10, value="")            # % Complete
            ws.cell(row=row, column=11, value="")            # Time Allocated (aggregated externally)
            ws.cell(row=row, column=12, value="")            # Time Spent (aggregated externally)
            ws.cell(row=row, column=13, value="")            # Scheduled Date (N/A for projects)
            ws.cell(row=row, column=14, value="")            # Milestones
            row += 1

    # ── Tasks ──────────────────────────────────────────────────────────────
    if SHEET_TASKS in wb.sheetnames:
        task_ws = wb[SHEET_TASKS]
        task_range = table_range(SHEET_TASKS)
        t_title_col  = ci(SHEET_TASKS, "Title") + 1
        t_start_col  = ci(SHEET_TASKS, "Start Date") + 1
        t_end_col    = ci(SHEET_TASKS, "End Date") + 1
        t_dead_col   = ci(SHEET_TASKS, "Deadline") + 1
        t_status_col = ci(SHEET_TASKS, "Status") + 1
        t_proj_col   = ci(SHEET_TASKS, "Project ID") + 1
        t_sched_col  = ci(SHEET_TASKS, "Scheduled Date") + 1

        for r in range(2, task_ws.max_row + 1):
            tid = clean(task_ws.cell(row=r, column=1).value)
            if not tid:
                continue
            a_ref = f"$A{row}"
            ws.cell(row=row, column=1, value=tid)
            ws.cell(row=row, column=2, value="Task")
            ws.cell(row=row, column=3).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_title_col},FALSE),"")'
            # Parent ID = Project ID
            ws.cell(row=row, column=4).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_proj_col},FALSE),"")'
            ws.cell(row=row, column=5).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_start_col},FALSE),"")'
            ws.cell(row=row, column=6).value = f'=IFERROR(IF(F{row}="","",G{row}-F{row}),"")'
            ws.cell(row=row, column=7).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_end_col},FALSE),"")'
            ws.cell(row=row, column=8).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_dead_col},FALSE),"")'
            ws.cell(row=row, column=9).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_status_col},FALSE),"")'
            ws.cell(row=row, column=10, value="")
            ws.cell(row=row, column=11, value="")            # Time Allocated (sum of deliverables — computed in domain)
            ws.cell(row=row, column=12, value="")            # Time Spent
            ws.cell(row=row, column=13).value = f'=IFERROR(VLOOKUP({a_ref},{task_range},{t_sched_col},FALSE),"")'
            ws.cell(row=row, column=14, value="")            # Milestones
            row += 1

    # ── Deliverables ───────────────────────────────────────────────────────
    if SHEET_DELIVERABLES in wb.sheetnames:
        del_ws = wb[SHEET_DELIVERABLES]
        del_range = table_range(SHEET_DELIVERABLES)
        d_title_col  = ci(SHEET_DELIVERABLES, "Title") + 1
        d_start_col  = ci(SHEET_DELIVERABLES, "Start Date") + 1
        d_end_col    = ci(SHEET_DELIVERABLES, "End Date") + 1
        d_dead_col   = ci(SHEET_DELIVERABLES, "Deadline") + 1
        d_status_col = ci(SHEET_DELIVERABLES, "Status") + 1
        d_task_col   = ci(SHEET_DELIVERABLES, "Task ID") + 1
        d_pct_col    = ci(SHEET_DELIVERABLES, "% Complete") + 1
        d_alloc_col  = ci(SHEET_DELIVERABLES, "Time Allocated") + 1
        d_spent_col  = ci(SHEET_DELIVERABLES, "Time Spent") + 1

        for r in range(2, del_ws.max_row + 1):
            did = clean(del_ws.cell(row=r, column=1).value)
            if not did:
                continue
            a_ref = f"$A{row}"
            ws.cell(row=row, column=1, value=did)
            ws.cell(row=row, column=2, value="Deliverable")
            ws.cell(row=row, column=3).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_title_col},FALSE),"")'
            ws.cell(row=row, column=4).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_task_col},FALSE),"")'
            ws.cell(row=row, column=5).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_start_col},FALSE),"")'
            ws.cell(row=row, column=6).value = f'=IFERROR(IF(F{row}="","",G{row}-F{row}),"")'
            ws.cell(row=row, column=7).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_end_col},FALSE),"")'
            ws.cell(row=row, column=8).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_dead_col},FALSE),"")'
            ws.cell(row=row, column=9).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_status_col},FALSE),"")'
            ws.cell(row=row, column=10).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_pct_col},FALSE),"")'
            ws.cell(row=row, column=11).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_alloc_col},FALSE),"")'
            ws.cell(row=row, column=12).value = f'=IFERROR(VLOOKUP({a_ref},{del_range},{d_spent_col},FALSE),"")'
            ws.cell(row=row, column=13, value="")            # Scheduled Date (N/A for deliverables)
            ws.cell(row=row, column=14, value="")            # Milestones
            row += 1

    return row - 2  # rows written
