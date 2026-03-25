"""
Weekly Planner page — 7-day × 5-priority grid showing scheduled tasks
for the current week.  Supports multi-task slots and partial allocation.

Displays daily time budget utilisation and warns when a day is
over-capacity.

Driven by ``compute_schedule()`` from the scheduling engine and the
profile's ``daily_hours_budget`` constant.
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import (
    AG_DARK, AG_MID, AG_LIGHT, AG_WASH,
    PRIORITY_LABELS, PRIORITY_COLORS,
)
from helpers.scheduling.engine import compute_schedule, daily_hours, week_start_date


# ── Layout constants ───────────────────────────────────────────────────────────
CELL_MIN_W = 130
CELL_H = 56
MULTI_CELL_H = 42       # per-task height inside a multi-task slot
HEADER_H = 48
LABEL_W = 110
BUDGET_BAR_H = 22
_STATUS_BG = {
    "in progress":  "#D6EAF8",
    "on track":     "#D5F5E3",
    "not started":  "#F2F3F4",
    "ongoing":      "#D6EAF8",
    "recurring":    "#D6EAF8",
    "on hold":      "#FADBD8",
    "completed":    "#ABEBC6",
}


class SchedulerPage(BasePage):
    KEY = "scheduler"
    TITLE = "Weekly Planner"
    OPTIONAL = True

    def build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header bar ─────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(top, text="Weekly Planner", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).pack(side="left")

        self._week_label = ctk.CTkLabel(
            top, text="", font=("Segoe UI", 11), text_color="gray",
        )
        self._week_label.pack(side="left", padx=(16, 0))

        self._warning_label = ctk.CTkLabel(
            top, text="", font=("Segoe UI", 11, "bold"), text_color="#c0392b",
        )
        self._warning_label.pack(side="right")

        # Week navigation
        ctk.CTkButton(
            top, text="This Week", width=90, height=30,
            fg_color=AG_MID, hover_color=AG_DARK,
            command=self._go_this_week,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            top, text="▶", width=36, height=30,
            fg_color="gray", hover_color="darkgray",
            command=self._go_next_week,
        ).pack(side="right", padx=(2, 0))
        ctk.CTkButton(
            top, text="◀", width=36, height=30,
            fg_color="gray", hover_color="darkgray",
            command=self._go_prev_week,
        ).pack(side="right")

        # ── Scrollable grid area ───────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))

        self._week_start: date = week_start_date(date.today())

    # ── Navigation ─────────────────────────────────────────────────────────
    def _go_this_week(self):
        self._week_start = week_start_date(date.today())
        self._render()

    def _go_prev_week(self):
        self._week_start -= timedelta(days=7)
        self._render()

    def _go_next_week(self):
        self._week_start += timedelta(days=7)
        self._render()

    # ── Public ─────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._render()

    # ── Rendering ──────────────────────────────────────────────────────────
    def _render(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        profile = self.app.profile
        if not profile:
            ctk.CTkLabel(self._scroll, text="No profile loaded.",
                         font=("Segoe UI", 12), text_color="gray").pack(pady=20)
            return

        ws = self._week_start
        we = ws + timedelta(days=6)
        self._week_label.configure(
            text=f"{ws.strftime('%b %d')} – {we.strftime('%b %d, %Y')}"
        )

        # Run scheduler
        schedule = compute_schedule(profile, ws)
        hours_per_day = daily_hours(schedule)
        budget = profile.daily_hours_budget

        # Build lookup: (day_offset, priority) → [(task, hours), ...]
        grid: dict[tuple[int, int], list[tuple[object, float]]] = {}
        for day, pri_map in schedule.items():
            offset = (day - ws).days
            if 0 <= offset < 7:
                for pri, entries in pri_map.items():
                    grid.setdefault((offset, pri), []).extend(entries)

        # Check for overloaded days
        overloaded = []
        for d in range(7):
            day = ws + timedelta(days=d)
            hrs = hours_per_day.get(day, 0.0)
            if hrs > budget:
                overloaded.append(day.strftime("%a"))

        if overloaded:
            self._warning_label.configure(
                text=f"⚠ Over capacity: {', '.join(overloaded)}"
            )
        else:
            self._warning_label.configure(text="")

        # Configure grid columns
        container = self._scroll
        container.grid_columnconfigure(0, minsize=LABEL_W)
        for d in range(7):
            container.grid_columnconfigure(d + 1, weight=1, minsize=CELL_MIN_W)

        # ── Day headers ────────────────────────────────────────────────────
        # Empty top-left corner
        ctk.CTkLabel(container, text="", width=LABEL_W).grid(row=0, column=0)

        today = date.today()
        for d in range(7):
            day = ws + timedelta(days=d)
            is_today = day == today
            is_weekend = day.weekday() >= 5

            day_text = day.strftime("%a\n%b %d")
            fg = AG_DARK if is_today else (AG_MID if not is_weekend else "gray")
            font = ("Segoe UI", 11, "bold") if is_today else ("Segoe UI", 10)

            header = ctk.CTkLabel(
                container, text=day_text, font=font,
                text_color="white", fg_color=fg,
                height=HEADER_H, corner_radius=4,
            )
            header.grid(row=0, column=d + 1, sticky="ew", padx=2, pady=(0, 2))

        # ── Budget utilisation bar row ─────────────────────────────────────
        ctk.CTkLabel(
            container, text="Budget", font=("Segoe UI", 9, "bold"),
            text_color=AG_DARK, width=LABEL_W, anchor="e",
        ).grid(row=1, column=0, sticky="e", padx=(0, 8))

        for d in range(7):
            day = ws + timedelta(days=d)
            hrs = hours_per_day.get(day, 0.0)
            pct = min(hrs / budget, 1.5) if budget > 0 else 0
            is_over = hrs > budget

            bar_frame = ctk.CTkFrame(container, height=BUDGET_BAR_H, fg_color="#f0f0f0",
                                     corner_radius=3)
            bar_frame.grid(row=1, column=d + 1, sticky="ew", padx=2, pady=2)
            bar_frame.grid_propagate(False)
            bar_frame.grid_columnconfigure(0, weight=1)

            fill_color = "#e74c3c" if is_over else ("#27ae60" if pct > 0.5 else AG_MID)
            fill_w = max(1, int(pct / 1.5 * 100))  # percentage of frame

            fill = ctk.CTkFrame(bar_frame, fg_color=fill_color, corner_radius=2)
            fill.place(relx=0, rely=0.1, relwidth=min(fill_w / 100, 1.0), relheight=0.8)

            label_text = f"{hrs:.1f}/{budget:.0f}h" if hrs > 0 else "—"
            ctk.CTkLabel(
                bar_frame, text=label_text, font=("Segoe UI", 8),
                text_color="#333" if not is_over else "#c0392b",
            ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Priority rows ──────────────────────────────────────────────────
        for pri in range(1, 6):
            row_idx = pri + 1  # offset for header + budget rows
            label = PRIORITY_LABELS.get(pri, f"P{pri}")
            color = PRIORITY_COLORS.get(pri, AG_DARK)

            ctk.CTkLabel(
                container, text=label, font=("Segoe UI", 10, "bold"),
                text_color=color, width=LABEL_W, anchor="e",
            ).grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=2)

            for d in range(7):
                slot = grid.get((d, pri))
                if slot:
                    self._render_slot_cell(container, row_idx, d + 1, slot)
                else:
                    empty = ctk.CTkFrame(container, fg_color="#fafafa",
                                         corner_radius=4, height=CELL_H)
                    empty.grid(row=row_idx, column=d + 1, sticky="nsew",
                               padx=2, pady=2)

    # ── Cell rendering ─────────────────────────────────────────────────────
    def _render_slot_cell(self, container, row_idx: int, col: int,
                          slot: list[tuple[object, float]]) -> None:
        """Render a (day, priority) cell that may hold multiple task entries."""
        if len(slot) == 1:
            task, hrs = slot[0]
            self._render_single_task_cell(container, row_idx, col, task, hrs)
        else:
            # Multi-task cell
            cell_h = max(CELL_H, MULTI_CELL_H * len(slot) + 4)
            outer = ctk.CTkFrame(container, fg_color="#f5f5f5", corner_radius=4,
                                 height=cell_h)
            outer.grid(row=row_idx, column=col, sticky="nsew", padx=2, pady=2)
            outer.grid_propagate(False)
            for task, hrs in slot:
                status_key = task.status.strip().lower()
                bg = _STATUS_BG.get(status_key, "#f5f5f5")
                mini = ctk.CTkFrame(outer, fg_color=bg, corner_radius=3,
                                    height=MULTI_CELL_H)
                mini.pack(fill="x", padx=2, pady=1)
                mini.pack_propagate(False)
                title = task.title
                if len(title) > 24:
                    title = title[:22] + "…"
                ctk.CTkLabel(
                    mini, text=title, font=("Segoe UI", 8, "bold"),
                    text_color="#333", anchor="nw",
                ).pack(anchor="nw", padx=4, pady=(2, 0))
                ctk.CTkLabel(
                    mini, text=f"{hrs:.1f}h", font=("Segoe UI", 7),
                    text_color="gray", anchor="nw",
                ).pack(anchor="nw", padx=4)

    @staticmethod
    def _render_single_task_cell(container, row_idx: int, col: int,
                                 task, hrs: float) -> None:
        """Render a cell with a single task entry."""
        status_key = task.status.strip().lower()
        bg = _STATUS_BG.get(status_key, "#f5f5f5")

        cell = ctk.CTkFrame(container, fg_color=bg, corner_radius=4,
                            height=CELL_H)
        cell.grid(row=row_idx, column=col, sticky="nsew", padx=2, pady=2)
        cell.grid_propagate(False)

        title = task.title
        if len(title) > 28:
            title = title[:26] + "…"
        ctk.CTkLabel(
            cell, text=title, font=("Segoe UI", 9, "bold"),
            text_color="#333", wraplength=CELL_MIN_W - 12,
            anchor="nw", justify="left",
        ).pack(anchor="nw", padx=6, pady=(4, 0))

        sub = task.status
        if hrs > 0:
            sub += f"  ({hrs:.1f}h)"
        ctk.CTkLabel(
            cell, text=sub, font=("Segoe UI", 8),
            text_color="gray", anchor="nw",
        ).pack(anchor="nw", padx=6)
