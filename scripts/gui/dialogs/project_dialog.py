"""ProjectDialog — modal dialog for adding or editing a project.

Uses domain attribute names for all data keys.
Provides all 12 project fields including Supervisor, Site, Priority, and Notes.
"""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from gui.ui_theme import AG_DARK, AG_MID, STATUS_OPTIONS, CATEGORIES, PRIORITY_LABELS
from helpers.domain.project import Project


class ProjectDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a project."""

    def __init__(self, parent, title="Project",
                 project: Project | None = None, on_save=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("540x750")
        self.resizable(True, True)
        self.minsize(420, 560)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        self._on_save = on_save
        self._project = project

        pad = {"padx": 14, "pady": (4, 0)}

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        # ── Fields ─────────────────────────────────────────────────────────
        self.entries: dict[str, ctk.CTkEntry | ctk.CTkTextbox | ctk.CTkOptionMenu] = {}

        # Title
        ctk.CTkLabel(scroll, text="Title", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_title = ctk.CTkEntry(scroll, width=460)
        w_title.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Title"] = w_title

        # Category
        ctk.CTkLabel(scroll, text="Category", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        var_cat = ctk.StringVar(value="Ongoing")
        w_cat = ctk.CTkOptionMenu(scroll, variable=var_cat, values=CATEGORIES, width=260)
        w_cat._variable = var_cat
        w_cat.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["Category"] = w_cat

        # Description
        ctk.CTkLabel(scroll, text="Description", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_desc = ctk.CTkTextbox(scroll, width=460, height=80)
        w_desc.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Description"] = w_desc

        # Status
        ctk.CTkLabel(scroll, text="Status", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        var_status = ctk.StringVar(value="Not Started")
        w_status = ctk.CTkOptionMenu(scroll, variable=var_status, values=STATUS_OPTIONS, width=260)
        w_status._variable = var_status
        w_status.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["Status"] = w_status

        # Supervisor
        ctk.CTkLabel(scroll, text="Supervisor", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_super = ctk.CTkEntry(scroll, width=460)
        w_super.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Supervisor"] = w_super

        # Site
        ctk.CTkLabel(scroll, text="Site", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_site = ctk.CTkEntry(scroll, width=460)
        w_site.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Site"] = w_site

        # Priority
        ctk.CTkLabel(scroll, text="Priority", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        prio_values = ["None"] + list(PRIORITY_LABELS.values())
        var_prio = ctk.StringVar(value="None")
        w_prio = ctk.CTkOptionMenu(scroll, variable=var_prio, values=prio_values, width=260)
        w_prio._variable = var_prio
        w_prio.pack(anchor="w", padx=14, pady=(2, 4))
        self.entries["Priority"] = w_prio

        # Notes
        ctk.CTkLabel(scroll, text="Notes", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
        w_notes = ctk.CTkTextbox(scroll, width=460, height=60)
        w_notes.pack(anchor="w", padx=14, pady=(2, 4), fill="x")
        self.entries["Notes"] = w_notes

        # Date fields
        for date_label in ("Start Date", "End Date", "Deadline", "Date Completed"):
            ctk.CTkLabel(scroll, text=date_label, font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
            w_date = ctk.CTkEntry(scroll, width=200, placeholder_text="YYYY-MM-DD")
            w_date.pack(anchor="w", padx=14, pady=(2, 4))
            self.entries[date_label] = w_date

        # ── Pre-fill for edit mode ─────────────────────────────────────────
        if project:
            w_title.insert(0, project.title)
            w_desc.insert("1.0", project.description)
            var_cat.set(project.category if project.category in CATEGORIES else CATEGORIES[0])
            var_status.set(project.status if project.status in STATUS_OPTIONS else STATUS_OPTIONS[0])
            if project.supervisor:
                w_super.insert(0, project.supervisor)
            if project.site:
                w_site.insert(0, project.site)
            if project.priority:
                var_prio.set(PRIORITY_LABELS.get(project.priority, "None"))
            if project.notes:
                w_notes.insert("1.0", project.notes)
            date_prefills = {
                "Start Date": project.start,
                "End Date": project.end,
                "Deadline": project.deadline,
                "Date Completed": project.date_completed,
            }
            for key, dt in date_prefills.items():
                if dt:
                    self.entries[key].insert(0, dt.isoformat())

        # ── Buttons ────────────────────────────────────────────────────────
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

        # Extract priority int from label
        prio_str = self._get("Priority")
        prio_int = 0
        for k, v in PRIORITY_LABELS.items():
            if v == prio_str:
                prio_int = k
                break

        data = {
            "title": title,
            "category": self._get("Category"),
            "description": self._get("Description"),
            "status": self._get("Status"),
            "supervisor": self._get("Supervisor"),
            "site": self._get("Site"),
            "priority": prio_int,
            "notes": self._get("Notes"),
            "start": self._parse_date("Start Date"),
            "end": self._parse_date("End Date"),
            "deadline": self._parse_date("Deadline"),
            "date_completed": self._parse_date("Date Completed"),
        }
        if self._on_save:
            self._on_save(data)
        self.destroy()
