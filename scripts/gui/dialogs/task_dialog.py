"""
TaskDialog — modal dialog for adding or editing a task (domain-based).
Uses domain attribute names for all data keys.
"""
from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from gui.ui_theme import (
    AG_DARK, AG_MID, PRIORITY_LABELS, STATUS_OPTIONS,
)
from helpers.domain.task import Task


class TaskDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a task."""

    def __init__(self, parent, title="Task", task: Task | None = None,
                 project_id: str = "", on_save=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("620x780")
        self.resizable(True, True)
        self.minsize(500, 640)
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save
        self._task = task  # None → add mode
        self._project_id = project_id

        pad = {"padx": 14, "pady": (4, 0)}

        # ── Scrollable content area ────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        # ── Project ID display (read-only info) ───────────────────────────────
        if project_id:
            ctk.CTkLabel(scroll, text=f"Project: {project_id}",
                         font=("Segoe UI", 11), text_color="gray").pack(anchor="w", **pad)

        # ── Fields ─────────────────────────────────────────────────────────────
        self.entries: dict[str, ctk.CTkEntry | ctk.CTkTextbox | ctk.CTkOptionMenu] = {}
        fields = [
            ("Title", "entry"),
            ("Supervisor", "entry"),
            ("Site", "entry"),
            ("Description", "text"),
            ("Commentary", "text"),
            ("Status", "option"),
            ("Priority", "priority"),
            ("Start Date", "date"),
            ("End Date", "date"),
            ("Deadline", "date"),
        ]
        for label, kind in fields:
            ctk.CTkLabel(scroll, text=label, font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
            if kind == "entry":
                w = ctk.CTkEntry(scroll, width=500)
                w.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
            elif kind == "text":
                w = ctk.CTkTextbox(scroll, width=500, height=80)
                w.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
            elif kind == "option":
                var = ctk.StringVar(value="In Progress")
                w = ctk.CTkOptionMenu(scroll, variable=var, values=STATUS_OPTIONS, width=260)
                w._variable = var
                w.pack(anchor="w", padx=14, pady=(2, 4))
            elif kind == "priority":
                var = ctk.StringVar(value="P3 - Medium")
                w = ctk.CTkOptionMenu(
                    scroll, variable=var,
                    values=list(PRIORITY_LABELS.values()), width=260,
                )
                w._variable = var
                w.pack(anchor="w", padx=14, pady=(2, 4))
            elif kind == "date":
                w = ctk.CTkEntry(scroll, width=200, placeholder_text="YYYY-MM-DD")
                w.pack(anchor="w", padx=14, pady=(2, 4))
            self.entries[label] = w

        # ── Pre-fill for edit mode ──────────────────────────────────────────────
        if task:
            mapping = {
                "Title": task.title,
                "Supervisor": task.supervisor,
                "Site": task.site,
                "Description": task.description,
                "Commentary": task.commentary,
            }
            for key, val in mapping.items():
                widget = self.entries[key]
                if isinstance(widget, ctk.CTkEntry):
                    widget.insert(0, val)
                elif isinstance(widget, ctk.CTkTextbox):
                    widget.insert("1.0", val)

            status_w = self.entries["Status"]
            status_w._variable.set(task.status if task.status in STATUS_OPTIONS else STATUS_OPTIONS[0])
            prio_w = self.entries["Priority"]
            prio_w._variable.set(PRIORITY_LABELS.get(task.priority, "P3 - Medium"))

            # Pre-fill date fields
            date_fields = {
                "Start Date": task.start,
                "End Date": task.end,
                "Deadline": task.deadline,
            }
            for key, dt in date_fields.items():
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

    # ── helpers ────────────────────────────────────────────────────────────
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
        # Extract priority int from label
        prio_str = self._get("Priority")
        prio_int = 3
        for k, v in PRIORITY_LABELS.items():
            if v == prio_str:
                prio_int = k
                break

        data = {
            "project_id": self._project_id,
            "title": title,
            "supervisor": self._get("Supervisor"),
            "site": self._get("Site"),
            "description": self._get("Description"),
            "commentary": self._get("Commentary"),
            "status": self._get("Status"),
            "priority": prio_int,
            "start": self._parse_date("Start Date"),
            "end": self._parse_date("End Date"),
            "deadline": self._parse_date("Deadline"),
        }
        if self._on_save:
            self._on_save(data)
        self.destroy()
