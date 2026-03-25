"""
Add Task page — form for creating new tasks (domain-based).
"""
from __future__ import annotations

from datetime import date, datetime
from tkinter import messagebox

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import AG_DARK, AG_MID, PRIORITY_LABELS, STATUS_OPTIONS


class AddTaskPage(BasePage):
    KEY = "add_task"
    TITLE = "Add Task"

    def build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(scroll, text="Add New Task", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).pack(anchor="w", pady=(0, 10))

        # Project selector
        ctk.CTkLabel(scroll, text="Target Project", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(6, 0))
        self._project_var = ctk.StringVar(value="")
        self._project_menu = ctk.CTkOptionMenu(
            scroll, variable=self._project_var,
            values=["(no projects)"], width=400,
            command=self._on_project_changed,
        )
        self._project_menu.pack(anchor="w", pady=(2, 8))

        # Date Completed field (shown only when project category is Completed)
        self._date_completed_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._date_completed_label = ctk.CTkLabel(
            self._date_completed_frame, text="Date Completed (YYYY-MM-DD)",
            font=("Segoe UI", 12, "bold"),
        )
        self._date_completed_label.pack(anchor="w")
        self._date_completed_entry = ctk.CTkEntry(
            self._date_completed_frame, width=500,
            placeholder_text=date.today().isoformat(),
        )
        self._date_completed_entry.pack(anchor="w", pady=(2, 4))
        # Frame starts hidden; visibility is toggled by _on_project_changed
        self._date_completed_frame.pack(anchor="w", fill="x", pady=(0, 4))
        self._date_completed_frame.pack_forget()

        # Form fields
        self._add_entries: dict[str, ctk.CTkEntry | ctk.CTkTextbox | ctk.CTkOptionMenu] = {}
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
            ctk.CTkLabel(scroll, text=label, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(6, 0))
            if kind == "entry":
                w = ctk.CTkEntry(scroll, width=500)
                w.pack(anchor="w", pady=(2, 4))
            elif kind == "text":
                w = ctk.CTkTextbox(scroll, width=500, height=65)
                w.pack(anchor="w", pady=(2, 4))
            elif kind == "option":
                var = ctk.StringVar(value="In Progress")
                w = ctk.CTkOptionMenu(scroll, variable=var, values=STATUS_OPTIONS, width=280)
                w._variable = var
                w.pack(anchor="w", pady=(2, 4))
            elif kind == "priority":
                var = ctk.StringVar(value="P3 - Medium")
                w = ctk.CTkOptionMenu(scroll, variable=var, values=list(PRIORITY_LABELS.values()), width=280)
                w._variable = var
                w.pack(anchor="w", pady=(2, 4))
            elif kind == "date":
                w = ctk.CTkEntry(scroll, width=200, placeholder_text="YYYY-MM-DD")
                w.pack(anchor="w", pady=(2, 4))
            self._add_entries[label] = w

        ctk.CTkButton(
            scroll, text="Add Task", width=200, height=40,
            font=("Segoe UI", 14, "bold"), fg_color=AG_DARK, hover_color=AG_MID,
            command=self._do_add_task,
        ).pack(anchor="w", pady=(16, 8))

    # ── helpers ────────────────────────────────────────────────────────────
    def _on_project_changed(self, _selected: str = "") -> None:
        """Show or hide the Date Completed field based on the selected project's category."""
        project_id = self._resolve_project_id()
        profile = self.app.profile
        show = False
        if project_id and profile:
            project = profile.find_project(project_id)
            if project and project.category == "Completed":
                show = True
        if show:
            # Re-pack just after the project menu
            self._date_completed_frame.pack(anchor="w", fill="x", pady=(0, 4),
                                            after=self._project_menu)
        else:
            self._date_completed_frame.pack_forget()

    def _get_field(self, key: str) -> str:
        w = self._add_entries[key]
        if isinstance(w, ctk.CTkEntry):
            return w.get().strip()
        elif isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        elif hasattr(w, "_variable"):
            return w._variable.get()
        return ""

    def _clear_form(self):
        for key, w in self._add_entries.items():
            if isinstance(w, ctk.CTkEntry):
                w.delete(0, "end")
            elif isinstance(w, ctk.CTkTextbox):
                w.delete("1.0", "end")
        self._date_completed_entry.delete(0, "end")

    def _build_project_list(self) -> list[tuple[str, str]]:
        """Return list of (project_id, display_label) from the profile."""
        profile = self.app.profile
        if not profile:
            return []
        return [(p.id, f"{p.title} ({p.category})") for p in profile.projects]

    def refresh(self) -> None:
        """Refresh the project selector with current profile data."""
        projects = self._build_project_list()
        if projects:
            labels = [label for _, label in projects]
            self._project_menu.configure(values=labels)
            if not self._project_var.get() or self._project_var.get() not in labels:
                self._project_var.set(labels[0])
        else:
            self._project_menu.configure(values=["(no projects)"])
            self._project_var.set("(no projects)")

    def _resolve_project_id(self) -> str | None:
        """Map the selected display label back to a project ID."""
        selected = self._project_var.get()
        for pid, label in self._build_project_list():
            if label == selected:
                return pid
        return None

    def _do_add_task(self):
        title = self._get_field("Title")
        if not title:
            messagebox.showwarning("Missing Title", "Title is required.")
            return

        project_id = self._resolve_project_id()
        if not project_id:
            messagebox.showwarning(
                "No Project",
                "You need a project first.\n\n"
                "Go to the Tasks page and click 'Add Project' to create one.",
            )
            return

        # Parse priority
        prio_str = self._get_field("Priority")
        prio_int = 3
        for k, v in PRIORITY_LABELS.items():
            if v == prio_str:
                prio_int = k
                break

        data = {
            "title": title,
            "supervisor": self._get_field("Supervisor"),
            "site": self._get_field("Site"),
            "description": self._get_field("Description"),
            "commentary": self._get_field("Commentary"),
            "status": self._get_field("Status"),
            "priority": prio_int,
            "start": self._parse_date_field("Start Date"),
            "end": self._parse_date_field("End Date"),
            "deadline": self._parse_date_field("Deadline"),
        }

        # If the target project is Completed, stamp the Date Completed
        date_completed = None
        project = self.app.profile.find_project(project_id) if self.app.profile else None
        if project and project.category == "Completed":
            date_str = self._date_completed_entry.get().strip()
            if date_str:
                try:
                    date_completed = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    messagebox.showwarning("Invalid Date", "Date must be YYYY-MM-DD format.")
                    return
            else:
                date_completed = date.today()

        if date_completed:
            data["date_completed"] = date_completed

        self.app.service.add_task(project_id, data)
        self._clear_form()
        messagebox.showinfo("Task Added", f"'{title}' added to project.")

    def _parse_date_field(self, key: str):
        """Parse a YYYY-MM-DD date field, returning None if empty or invalid."""
        raw = self._get_field(key)
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None
