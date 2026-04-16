"""Project Timeline page -- canvas-based Gantt view grouped by project.

Tasks are bars; deliverables are thin sub-bars beneath their parent task.
Use this for long-term planning across weeks and months.  For the current
week's schedule, see the Weekly Planner page.

Tasks without a start date appear in a *No Scheduled Start* section at
the bottom so they are never invisible.  Right-click any bar for quick
adjustments (edit, shift ±1 day).
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import (
    AG_DARK, CATEGORIES, GANTT_COLORS_DARK,
)
from helpers.config import load as load_config
from helpers.config.loader import status_gantt_color
from helpers.reporting.gantt import GanttRow, prepare_gantt_data

# ── Layout constants ───────────────────────────────────────────────────────────
ROW_HEIGHT = 26
SUBROW_HEIGHT = 20
LABEL_WIDTH = 260
HEADER_HEIGHT = 44
DAY_WIDTH_DEFAULT = 16


class GanttPage(BasePage):
    KEY = "gantt"
    TITLE = "Project Timeline"

    def build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        theme = load_config("theme")
        self._gantt_colors = theme.get("gantt_colors", {})
        self._gantt_colors_dark = theme.get("gantt_colors_dark", {})
        self._dark_mode = False

        # Row-data index used by the right-click handler
        self._rows: list[GanttRow] = []
        self._row_y_ranges: list[tuple[int, int]] = []  # (y_top, y_bottom) per row
        self._render_after_id: str | None = None  # debounce handle

        # ── Header bar ─────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(top, text="Project Timeline", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).pack(side="left")

        # Dark mode toggle
        self._dark_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            top, text="Dark Mode", variable=self._dark_var,
            command=self._toggle_dark_mode,
        ).pack(side="right", padx=(16, 0))

        # Filter
        self._filter_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            top, variable=self._filter_var,
            values=["All"] + CATEGORIES,
            width=160, command=lambda _: self._render(),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkLabel(top, text="Filter:", font=("Segoe UI", 12)).pack(side="right")

        # Day-width slider
        self._day_width_var = tk.IntVar(value=DAY_WIDTH_DEFAULT)
        ctk.CTkLabel(top, text="Zoom:", font=("Segoe UI", 12)).pack(side="right", padx=(16, 4))
        ctk.CTkSlider(
            top, from_=4, to=40, variable=self._day_width_var,
            width=120, command=lambda _: self._render(),
        ).pack(side="right")

        # ── Canvas area ────────────────────────────────────────────────────
        self._canvas_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        self._canvas_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self._canvas_frame.grid_columnconfigure(0, weight=1)
        self._canvas_frame.grid_rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self._canvas_frame, bg="white", highlightthickness=0)
        vsb = tk.Scrollbar(self._canvas_frame, orient="vertical", command=self._canvas.yview)
        hsb = tk.Scrollbar(self._canvas_frame, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._canvas.bind("<Configure>", self._on_configure)
        self._canvas.bind("<Button-3>", self._on_right_click)

    # ── public ─────────────────────────────────────────────────────────────
    def _on_configure(self, event=None) -> None:
        """Debounced handler for canvas resize — delays render by 100ms."""
        if self._render_after_id is not None:
            self.after_cancel(self._render_after_id)
        self._render_after_id = self.after(100, self._render)

    def refresh(self) -> None:
        self._render()

    # ── drawing ────────────────────────────────────────────────────────────
    def _render(self):
        c = self._canvas
        c.delete("all")
        self._rows = []
        self._row_y_ranges = []

        profile = self.app.profile
        dark = self._dark_mode

        if not profile:
            c.create_text(200, 60, text="No profile loaded", anchor="w",
                          font=("Segoe UI", 12),
                          fill=self._dk("text_dim", GANTT_COLORS_DARK.get("text_dim", "#A0A0B0")) if dark else "gray")
            return

        cat_filter = self._filter_var.get()
        day_w = max(4, self._day_width_var.get())

        data = prepare_gantt_data(profile.projects, cat_filter)
        rows = data.rows

        if not rows:
            c.create_text(200, 60, text="No tasks found.",
                          anchor="w", font=("Segoe UI", 12),
                          fill=self._dk("text_dim", GANTT_COLORS_DARK.get("text_dim", "#A0A0B0")) if dark else "gray")
            return

        range_start = data.range_start
        range_end = data.range_end
        total_days = data.total_days

        self._rows = rows

        # Compute total height
        total_h = HEADER_HEIGHT
        for r in rows:
            total_h += SUBROW_HEIGHT if r.type == "deliverable" else ROW_HEIGHT

        content_w = LABEL_WIDTH + total_days * day_w + 20
        c.configure(scrollregion=(0, 0, content_w, total_h + 20))

        # ── Header ─────────────────────────────────────────────────────────
        hdr_color = (self._dk("header", AG_DARK) if dark
                     else self._gantt_colors.get("header", AG_DARK))
        c.create_rectangle(0, 0, content_w, HEADER_HEIGHT, fill=hdr_color, outline="")
        c.create_text(8, 12, text="Task / Deliverable", anchor="nw",
                      font=("Segoe UI", 9, "bold"), fill="white")

        # Month labels
        cur = range_start.replace(day=1)
        while cur <= range_end:
            dx = (cur - range_start).days
            if dx >= 0:
                x = LABEL_WIDTH + dx * day_w
                c.create_text(x + 4, 6, text=cur.strftime("%b %Y"),
                              anchor="nw", font=("Segoe UI", 8, "bold"), fill="white")
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)

        # Week tick marks
        if day_w >= 8:
            for d in range(total_days):
                dt = range_start + timedelta(days=d)
                if dt.weekday() == 0:
                    x = LABEL_WIDTH + d * day_w
                    c.create_text(x + 2, HEADER_HEIGHT - 14,
                                  text=dt.strftime("%d"), anchor="nw",
                                  font=("Segoe UI", 7), fill="white")
                    # Vertical grid line
                    grid_color = self._dk("grid_line", GANTT_COLORS_DARK.get("grid_line", "#333355")) if dark else "#e8e8e8"
                    c.create_line(x, HEADER_HEIGHT, x, total_h,
                                  fill=grid_color, width=1)

        # Today line
        today = date.today()
        if range_start <= today <= range_end:
            tx = LABEL_WIDTH + (today - range_start).days * day_w
            today_color = self._dk("today_line", GANTT_COLORS_DARK.get("today_line", "#FF6B6B")) if dark else "#e74c3c"
            c.create_line(tx, HEADER_HEIGHT, tx, total_h,
                          fill=today_color, width=2, dash=(4, 2))

        # ── Rows ───────────────────────────────────────────────────────────
        y = HEADER_HEIGHT
        for i, row in enumerate(rows):
            rtype = row.type
            rh = SUBROW_HEIGHT if rtype == "deliverable" else ROW_HEIGHT
            y_top = y
            y_mid = y + rh // 2

            # Background
            if rtype == "project":
                bg = self._dk("project_bg", "#2A2A4A") if dark else "#dce6f5"
                c.create_rectangle(0, y, content_w, y + rh, fill=bg, outline="")
            elif rtype == "section":
                bg = self._dk("section_bg", "#3A3020") if dark else "#e8dcc8"
                c.create_rectangle(0, y, content_w, y + rh, fill=bg, outline="")
            elif i % 2 == 0:
                bg = self._dk("row_even", "#252538") if dark else "#fafafa"
                c.create_rectangle(0, y, content_w, y + rh, fill=bg, outline="")
            elif dark:
                bg = self._dk("row_odd", "#1E1E2E")
                c.create_rectangle(0, y, content_w, y + rh, fill=bg, outline="")

            # Label
            label = row.label
            if rtype in ("project", "section"):
                font = ("Segoe UI", 9, "bold")
                indent = 6
                if dark:
                    fill_color = self._dk("text", "#E0E0E0")
                else:
                    fill_color = "#333" if rtype == "project" else "#7a6840"
            elif rtype == "deliverable":
                font = ("Segoe UI", 8)
                indent = 28
                fill_color = self._dk("text_dim", "#A0A0B0") if dark else "#333"
            else:
                font = ("Segoe UI", 9)
                indent = 14
                fill_color = self._dk("text", "#E0E0E0") if dark else "#333"

            disp = label if len(label) <= 34 else label[:32] + "…"
            c.create_text(indent, y_mid, text=disp, anchor="w", font=font, fill=fill_color)

            # Bar (for tasks and deliverables with dates)
            if rtype in ("task", "deliverable") and row.start and row.end:
                bar_start = (row.start - range_start).days
                bar_end = (row.end - range_start).days
                bar_end = max(bar_end, bar_start + 1)

                x1 = LABEL_WIDTH + bar_start * day_w
                x2 = LABEL_WIDTH + bar_end * day_w
                bar_h = rh - 8 if rtype == "task" else rh - 6

                fill = self._bar_color(row.status)
                c.create_rectangle(x1, y + 4, x2, y + 4 + bar_h,
                                   fill=fill, outline="#ffffff", width=1)

                # Progress overlay for deliverables
                if rtype == "deliverable" and row.pct > 0:
                    pct = min(row.pct, 100) / 100.0
                    px2 = x1 + (x2 - x1) * pct
                    palette = self._gantt_colors_dark if dark else self._gantt_colors
                    c.create_rectangle(x1, y + 4, px2, y + 4 + bar_h,
                                       fill=palette.get("completed", "#2E8B57"),
                                       outline="", width=0)

                # Deadline marker
                if row.deadline:
                    dl_x = LABEL_WIDTH + (row.deadline - range_start).days * day_w
                    sz = 4
                    c.create_polygon(
                        dl_x, y_mid - sz,
                        dl_x + sz, y_mid,
                        dl_x, y_mid + sz,
                        dl_x - sz, y_mid,
                        fill="#c0392b", outline="#c0392b",
                    )

            # Row divider
            div_color = self._dk("divider", "#333355") if dark else "#e0e0e0"
            c.create_line(0, y + rh, content_w, y + rh, fill=div_color)
            self._row_y_ranges.append((y_top, y + rh))
            y += rh

    # ── right-click context menu ───────────────────────────────────────────

    def _hit_row(self, canvas_y: int) -> GanttRow | None:
        """Return the row at *canvas_y*, or None."""
        for idx, (y_top, y_bot) in enumerate(self._row_y_ranges):
            if y_top <= canvas_y < y_bot:
                return self._rows[idx] if idx < len(self._rows) else None
        return None

    def _on_right_click(self, event: tk.Event) -> None:
        """Show context menu when right-clicking a task or deliverable bar."""
        # Convert widget coords to canvas coords (accounts for scroll)
        cy = self._canvas.canvasy(event.y)
        row = self._hit_row(cy)
        if not row or row.type not in ("task", "deliverable"):
            return
        if not row.item_id:
            return

        menu = tk.Menu(self._canvas, tearoff=0)
        item_id = row.item_id
        has_dates = bool(row.start)

        menu.add_command(label=f"Edit {item_id}…",
                         command=lambda: self._open_edit_dialog(item_id))

        if has_dates:
            menu.add_separator()
            menu.add_command(label="Shift Start +1 day",
                             command=lambda: self._shift_date(item_id, "start", 1))
            menu.add_command(label="Shift Start −1 day",
                             command=lambda: self._shift_date(item_id, "start", -1))
            menu.add_separator()
            menu.add_command(label="Shift End +1 day",
                             command=lambda: self._shift_date(item_id, "end", 1))
            menu.add_command(label="Shift End −1 day",
                             command=lambda: self._shift_date(item_id, "end", -1))

        menu.tk_popup(event.x_root, event.y_root)

    # ── context-menu actions ───────────────────────────────────────────────

    def _shift_date(self, item_id: str, field: str, days: int) -> None:
        """Shift the start or end date of an item by *days* and persist."""
        service = self.app.service
        profile = self.app.profile
        if not service or not profile:
            return

        node = profile.find_by_id(item_id)
        if not node:
            return

        prefix = item_id.split("-")[0].upper() if "-" in item_id else ""
        if prefix not in ("T", "D"):
            return

        current = getattr(node, field, None)
        if not isinstance(current, date):
            return

        new_date = current + timedelta(days=days)

        if prefix == "T":
            service.edit_task(item_id, {field: new_date})
        else:
            service.edit_deliverable(item_id, {field: new_date})

        self._render()

    def _open_edit_dialog(self, item_id: str) -> None:
        """Open the appropriate edit dialog for *item_id*."""
        profile = self.app.profile
        if not profile:
            return

        node = profile.find_by_id(item_id)
        if not node:
            return

        from helpers.domain.task import Task
        from helpers.domain.deliverable import Deliverable

        if isinstance(node, Task):
            try:
                from gui.dialogs.task_dialog import TaskDialog

                def on_save(data: dict) -> None:
                    self.app.service.edit_task(item_id, data)
                    self._render()

                TaskDialog(
                    self.winfo_toplevel(),
                    title="Edit Task",
                    task=node,
                    project_id=node.project_id,
                    on_save=on_save,
                )
            except ImportError:
                pass
        elif isinstance(node, Deliverable):
            try:
                from gui.dialogs.deliverable_dialog import DeliverableDialog

                def on_save(data: dict) -> None:
                    self.app.service.edit_deliverable(item_id, data)
                    self._render()

                DeliverableDialog(
                    self.winfo_toplevel(),
                    title="Edit Deliverable",
                    deliverable=node,
                    task_id=node.task_id,
                    on_save=on_save,
                )
            except ImportError:
                pass

    # ── dark-mode helpers ───────────────────────────────────────────────

    def _dk(self, key: str, fallback: str = "") -> str:
        """Return the dark-palette colour for *key*, or *fallback*."""
        return self._gantt_colors_dark.get(key, fallback)

    def _toggle_dark_mode(self) -> None:
        self._dark_mode = self._dark_var.get()
        bg = self._dk("bg", "#1E1E2E") if self._dark_mode else "white"
        self._canvas.configure(bg=bg)
        self._canvas_frame.configure(fg_color=bg)
        self._render()

    def _bar_color(self, status: str) -> str:
        return status_gantt_color(status)
