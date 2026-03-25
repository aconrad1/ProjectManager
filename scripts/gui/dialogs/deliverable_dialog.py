"""
DeliverableDialog — modal dialog for adding or editing a deliverable.
Uses domain attribute names for all data keys.
"""
from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from gui.ui_theme import AG_DARK, AG_MID, STATUS_OPTIONS
from helpers.domain.deliverable import Deliverable


class DeliverableDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a deliverable."""

    def __init__(self, parent, title="Deliverable",
                 deliverable: Deliverable | None = None,
                 task_id: str = "", on_save=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("520x560")
        self.resizable(True, True)
        self.minsize(400, 440)
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save
        self._deliverable = deliverable
        self._task_id = task_id

        pad = {"padx": 14, "pady": (4, 0)}

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        if task_id:
            ctk.CTkLabel(scroll, text=f"Task: {task_id}",
                         font=("Segoe UI", 11), text_color="gray").pack(anchor="w", **pad)

        # ── Fields ─────────────────────────────────────────────────────────────
        self.entries: dict[str, ctk.CTkEntry | ctk.CTkTextbox | ctk.CTkOptionMenu] = {}

        ctk.CTkLabel(scroll, text="Title", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_title = ctk.CTkEntry(scroll, width=440)
        w_title.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Title"] = w_title

        ctk.CTkLabel(scroll, text="Description", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_desc = ctk.CTkTextbox(scroll, width=440, height=80)
        w_desc.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Description"] = w_desc

        ctk.CTkLabel(scroll, text="Status", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        var_status = ctk.StringVar(value="Not Started")
        w_status = ctk.CTkOptionMenu(scroll, variable=var_status, values=STATUS_OPTIONS, width=260)
        w_status._variable = var_status
        w_status.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["Status"] = w_status

        ctk.CTkLabel(scroll, text="% Complete", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_pct = ctk.CTkEntry(scroll, width=120, placeholder_text="0")
        w_pct.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["% Complete"] = w_pct

        ctk.CTkLabel(scroll, text="Time Allocated (hrs)", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_alloc = ctk.CTkEntry(scroll, width=120, placeholder_text="0.0")
        w_alloc.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["Time Allocated"] = w_alloc

        ctk.CTkLabel(scroll, text="Time Spent (hrs)", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_spent = ctk.CTkEntry(scroll, width=120, placeholder_text="0.0")
        w_spent.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["Time Spent"] = w_spent

        # Date fields
        for date_label in ("Start Date", "End Date", "Deadline"):
            ctk.CTkLabel(scroll, text=date_label, font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
            w_date = ctk.CTkEntry(scroll, width=200, placeholder_text="YYYY-MM-DD")
            w_date.pack(anchor="w", padx=14, pady=(2, 4))
            self.entries[date_label] = w_date

        # ── Pre-fill for edit mode ─────────────────────────────────────────────
        if deliverable:
            w_title.insert(0, deliverable.title)
            w_desc.insert("1.0", deliverable.description)
            var_status.set(deliverable.status if deliverable.status in STATUS_OPTIONS else STATUS_OPTIONS[0])
            w_pct.insert(0, str(deliverable.percent_complete))
            if deliverable.time_allocated is not None:
                w_alloc.insert(0, str(deliverable.time_allocated))
            if deliverable.time_spent is not None:
                w_spent.insert(0, str(deliverable.time_spent))
            date_prefills = {
                "Start Date": deliverable.start,
                "End Date": deliverable.end,
                "Deadline": deliverable.deadline,
            }
            for key, dt in date_prefills.items():
                if dt:
                    self.entries[key].insert(0, dt.isoformat())

        # ── Buttons ────────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=10)
        ctk.CTkButton(
            btn_frame, text="Save", width=140, fg_color=AG_DARK,
            hover_color=AG_MID, command=self._save,
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Cancel", width=140, fg_color="gray",
            hover_color="darkgray", command=self.destroy,
        ).pack(side="right")

    def _get(self, key: str) -> str:
        w = self.entries[key]
        if isinstance(w, ctk.CTkEntry):
            return w.get().strip()
        elif isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        elif hasattr(w, "_variable"):
            return w._variable.get()
        return ""

    def _parse_date(self, key: str):
        """Parse a YYYY-MM-DD date entry, returning None if empty/invalid."""
        raw = self._get(key)
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _save(self):
        title = self._get("Title")
        if not title:
            messagebox.showwarning("Missing Title", "Title is required.", parent=self)
            return

        pct_str = self._get("% Complete")
        try:
            pct = int(pct_str) if pct_str else 0
        except ValueError:
            messagebox.showwarning("Invalid %", "% Complete must be a number.", parent=self)
            return

        alloc_str = self._get("Time Allocated")
        spent_str = self._get("Time Spent")
        try:
            time_allocated = float(alloc_str) if alloc_str else None
        except ValueError:
            messagebox.showwarning("Invalid Time", "Time Allocated must be a number.", parent=self)
            return
        try:
            time_spent = float(spent_str) if spent_str else None
        except ValueError:
            messagebox.showwarning("Invalid Time", "Time Spent must be a number.", parent=self)
            return

        data = {
            "title": title,
            "description": self._get("Description"),
            "status": self._get("Status"),
            "percent_complete": max(0, min(100, pct)),
            "time_allocated": time_allocated,
            "time_spent": time_spent,
            "start": self._parse_date("Start Date"),
            "end": self._parse_date("End Date"),
            "deadline": self._parse_date("Deadline"),
        }
        if self._on_save:
            self._on_save(data)
        self.destroy()
