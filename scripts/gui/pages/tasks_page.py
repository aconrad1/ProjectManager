"""
Tasks page — hierarchical treeview: Project → Task → Deliverable.
Supports CRUD, attachments, links, notes via domain hierarchy.
"""
from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import (
    AG_DARK, AG_MID,
    PRIORITY_LABELS, STATUS_OPTIONS, CATEGORIES,
    TREEVIEW_TAG_COLORS,
)
from gui.dialogs.task_dialog import TaskDialog
from gui.dialogs.task_notes_dialog import TaskNotesDialog
from gui.dialogs.deliverable_dialog import DeliverableDialog
from gui.dialogs.project_dialog import ProjectDialog
from gui.dialogs.batch_dialog import BatchOperationDialog

from helpers.attachments.service import attach_files, open_attachments_folder
from helpers.attachments.links import set_link, open_linked_folder as _open_linked
from helpers.ui.state import load_ui_state, save_ui_state


class TasksPage(BasePage):
    KEY = "tasks"
    TITLE = "Tasks"

    def build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Maps treeview iid → domain node info dict
        self._node_index: dict[str, dict] = {}
        # Track whether DnD is available (for status bar message)
        self._dnd_available: bool = False

        # ── Restore persisted UI state ─────────────────────────────────────
        try:
            ui = load_ui_state()
        except Exception:
            ui = {}
        saved_filter = ui.get("tasks_filter", "All")
        saved_search = ui.get("tasks_search", "")

        # ── Header / filter bar ────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(top, text="Task Manager", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).pack(side="left")

        # Filter by category
        self._filter_var = ctk.StringVar(value=saved_filter)
        ctk.CTkOptionMenu(
            top, variable=self._filter_var,
            values=["All"] + CATEGORIES,
            width=180, command=lambda _: self._on_filter_change(),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkLabel(top, text="Filter:", font=("Segoe UI", 12)).pack(side="right")

        # Search box
        self._search_var = ctk.StringVar(value=saved_search)
        self._search_var.trace_add("write", lambda *_: self._on_filter_change())
        self._search_entry = ctk.CTkEntry(
            top, textvariable=self._search_var, placeholder_text="Search tasks…",
            width=200,
        )
        self._search_entry.pack(side="right", padx=(8, 16))

        # ── Treeview ───────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=0)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        cols = ("title", "supervisor", "site", "status", "priority", "scheduled", "time", "category")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings",
                                 selectmode="extended")
        self.tree.heading("#0",        text="")
        self.tree.heading("title",     text="Title")
        self.tree.heading("supervisor", text="Supervisor")
        self.tree.heading("site",      text="Site")
        self.tree.heading("status",    text="Status")
        self.tree.heading("priority",  text="Priority")
        self.tree.heading("scheduled", text="Scheduled")
        self.tree.heading("time",      text="Time (A/S)")
        self.tree.heading("category",  text="Category")

        self.tree.column("#0",        width=30, stretch=False)
        self.tree.column("title",      width=200, minwidth=120)
        self.tree.column("supervisor", width=120, minwidth=80)
        self.tree.column("site",       width=100, minwidth=60)
        self.tree.column("status",     width=110, minwidth=60)
        self.tree.column("priority",   width=100, minwidth=60)
        self.tree.column("scheduled",  width=90, minwidth=60)
        self.tree.column("time",       width=90, minwidth=60)
        self.tree.column("category",   width=110, minwidth=80)

        # Style the treeview to match branding
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=("Segoe UI", 10), rowheight=26,
                        fieldbackground="white")
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=AG_DARK, foreground="white")
        style.map("Treeview.Heading",
                  background=[("active", AG_MID)])
        style.map("Treeview",
                  background=[("selected", AG_MID)],
                  foreground=[("selected", "white")])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", lambda _: self._edit_selected_task())

        # ── Button bar ─────────────────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 2))

        ctk.CTkButton(btn_bar, text="Edit Selected", width=130, fg_color=AG_DARK,
                      hover_color=AG_MID, command=self._edit_selected_task).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar, text="Delete Selected", width=130, fg_color="#c0392b",
                      hover_color="#e74c3c", command=self._delete_selected_task).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar, text="Duplicate", width=100, fg_color="#2980b9",
                      hover_color="#3498db", command=self._duplicate_selected_task).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar, text="Add Project", width=110, fg_color="#27ae60",
                      hover_color="#2ecc71", command=self._add_project).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar, text="Batch Edit…", width=110, fg_color="#8e44ad",
                      hover_color="#9b59b6", command=self._batch_edit).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar, text="Refresh", width=100,
                      fg_color="gray", hover_color="darkgray",
                      command=self.app.reload_data).pack(side="right")

        # ── Second button row (attachments & links) ────────────────────────
        btn_bar2 = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar2.grid(row=3, column=0, sticky="ew", padx=16, pady=(2, 4))

        ctk.CTkButton(btn_bar2, text="Attach File", width=120, fg_color="#8e44ad",
                      hover_color="#9b59b6", command=self._attach_file_to_task).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar2, text="View Attachments", width=140, fg_color="#27ae60",
                      hover_color="#2ecc71", command=self._view_attachments).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar2, text="Link Folder", width=120, fg_color="#d35400",
                      hover_color="#e67e22", command=self._link_folder_to_task).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar2, text="Open Folder", width=120, fg_color="#16a085",
                      hover_color="#1abc9c", command=self._open_linked_folder).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_bar2, text="Task Notes", width=120, fg_color="#2c3e50",
                      hover_color="#34495e", command=self._open_task_notes).pack(side="left", padx=(0, 6))

        # ── Right-click context menu ───────────────────────────────────────
        self._ctx_menu = tk.Menu(self.tree, tearoff=0)
        # Project operations
        self._ctx_menu.add_command(label="Add Project", command=self._add_project)
        self._ctx_menu.add_command(label="Edit Project", command=self._edit_selected_project)
        self._ctx_menu.add_command(label="Delete Project", command=self._delete_selected_project)
        self._ctx_menu.add_separator()
        # Task operations
        self._ctx_menu.add_command(label="Edit Task", command=self._edit_selected_task)
        self._ctx_menu.add_command(label="Duplicate Task", command=self._duplicate_selected_task)
        self._ctx_menu.add_separator()
        # Status sub-menu
        status_menu = tk.Menu(self._ctx_menu, tearoff=0)
        for st in STATUS_OPTIONS:
            status_menu.add_command(label=st, command=lambda s=st: self._quick_set_status(s))
        self._ctx_menu.add_cascade(label="Set Status", menu=status_menu)
        # Priority sub-menu
        prio_menu = tk.Menu(self._ctx_menu, tearoff=0)
        for pk, pv in PRIORITY_LABELS.items():
            prio_menu.add_command(label=pv, command=lambda p=pk: self._quick_set_priority(p))
        self._ctx_menu.add_cascade(label="Set Priority", menu=prio_menu)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Attach File", command=self._attach_file_to_task)
        self._ctx_menu.add_command(label="View Attachments", command=self._view_attachments)
        self._ctx_menu.add_command(label="Link Folder", command=self._link_folder_to_task)
        self._ctx_menu.add_command(label="Open Linked Folder", command=self._open_linked_folder)
        self._ctx_menu.add_command(label="Task Notes", command=self._open_task_notes)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Add Deliverable", command=self._add_deliverable)
        self._ctx_menu.add_command(label="Edit Deliverable", command=self._edit_deliverable)
        self._ctx_menu.add_command(label="Delete Deliverable", command=self._delete_deliverable)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Delete Task", command=self._delete_selected_task)

        self.tree.bind("<Button-3>", self._show_context_menu)

        # ── Drag-and-drop support ──────────────────────────────────────────
        self._setup_drag_drop()

        # ── Status bar ─────────────────────────────────────────────────────
        self._status_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 10), text_color="gray",
        )
        self._status_label.grid(row=4, column=0, sticky="w", padx=18, pady=(0, 10))

    # ── public ─────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._populate_tree()
        self._restore_expansion()

    def focus_search(self) -> None:
        """Clear and focus the search entry."""
        self._search_var.set("")
        self._search_entry.focus_set()

    def _on_filter_change(self) -> None:
        """Called when filter or search changes — repopulate and persist."""
        self._populate_tree()
        self._persist_ui_state()

    def _persist_ui_state(self) -> None:
        """Save current filter, search, and expansion state."""
        try:
            ui = load_ui_state()
        except Exception:
            ui = {}
        ui["tasks_filter"] = self._filter_var.get()
        ui["tasks_search"] = self._search_var.get()
        # Save expanded project iids
        expanded = []
        for iid in self.tree.get_children():
            if self.tree.item(iid, "open"):
                expanded.append(iid)
        ui["tasks_expanded"] = expanded
        try:
            save_ui_state(ui)
        except Exception:
            pass  # non-critical

    def _restore_expansion(self) -> None:
        """Restore project expansion state from persisted UI state."""
        try:
            ui = load_ui_state()
        except Exception:
            return
        expanded = set(ui.get("tasks_expanded", []))
        if not expanded:
            return
        for iid in self.tree.get_children():
            if iid in expanded:
                self.tree.item(iid, open=True)
            else:
                self.tree.item(iid, open=False)

    def update_status_bar(self) -> None:
        profile = self.app.profile
        if not profile:
            self._status_label.configure(text="No profile loaded")
            return
        weekly = len(profile.tasks_for_category("Weekly"))
        ongoing = len(profile.tasks_for_category("Ongoing"))
        completed = len(profile.tasks_for_category("Completed"))
        from helpers.profile.profile import WORKBOOK_FILENAME
        dnd_tag = "" if self._dnd_available else "  |  ⚠ Drag-and-drop unavailable (install tkinterdnd2)"
        text = (
            f"Weekly: {weekly}  |  "
            f"Ongoing: {ongoing}  |  "
            f"Completed: {completed}  |  "
            f"Workbook: {WORKBOOK_FILENAME}"
            f"{dnd_tag}"
        )
        self._status_label.configure(text=text)

    # ── helpers ────────────────────────────────────────────────────────────
    def _selected_node(self) -> dict | None:
        """Return the node info dict for the selected treeview item, or None."""
        sel = self.tree.selection()
        if not sel:
            return None
        return self._node_index.get(sel[0])

    def _selected_task_title(self) -> str | None:
        """Return the title of the selected task (or parent task for deliverables)."""
        node = self._selected_node()
        if not node:
            return None
        if node["type"] == "task":
            return node["title"]
        if node["type"] == "deliverable":
            return node.get("task_title")
        return None

    def _selected_task_id(self) -> str | None:
        """Return the ID of the selected task (or parent task for deliverables)."""
        node = self._selected_node()
        if not node:
            return None
        if node["type"] == "task":
            return node["id"]
        if node["type"] == "deliverable":
            return node.get("task_id")
        return None

    # ── Project CRUD ───────────────────────────────────────────────────────
    def _add_project(self):
        def on_save(data: dict):
            self.app.service.add_project(data)
            self.refresh()

        ProjectDialog(self.winfo_toplevel(), title="Add Project", on_save=on_save)

    def _edit_selected_project(self):
        node = self._selected_node()
        if not node:
            messagebox.showinfo("No Selection", "Select a project first.")
            return
        if node["type"] != "project":
            messagebox.showinfo("Select a Project", "Please select a project row to edit.")
            return

        project = self.app.profile.find_project(node["id"])
        if not project:
            return

        def on_save(data: dict):
            self.app.service.edit_project(node["id"], data)
            self.refresh()

        ProjectDialog(self.winfo_toplevel(), title="Edit Project",
                      project=project, on_save=on_save)

    def _delete_selected_project(self):
        node = self._selected_node()
        if not node:
            messagebox.showinfo("No Selection", "Select a project first.")
            return
        if node["type"] != "project":
            messagebox.showinfo("Select a Project", "Please select a project row to delete.")
            return

        title = node["title"]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete project \"{title}\" and ALL its tasks and deliverables?",
        ):
            return
        self.app.service.delete_project(node["id"])
        self.refresh()

    # ── tree population ────────────────────────────────────────────────────
    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._node_index.clear()

        profile = self.app.profile
        if not profile:
            return

        cat_filter = self._filter_var.get()
        search = self._search_var.get().lower()

        for project in profile.projects:
            if cat_filter != "All" and project.category != cat_filter:
                continue

            matching_tasks = []
            for task in project.tasks:
                if search:
                    haystack = f"{task.title} {task.supervisor} {task.site} {task.status}".lower()
                    if search not in haystack:
                        continue
                matching_tasks.append(task)

            if not matching_tasks and search:
                continue

            proj_iid = f"proj_{project.id}"
            alloc = project.time_allocated_total
            spent = project.time_spent_total
            time_str = f"{alloc:.1f}/{spent:.1f}" if alloc or spent else ""
            self.tree.insert(
                "", "end", iid=proj_iid,
                values=(project.title, "", "", project.status, "",
                        "", time_str, project.category),
                open=True,
                tags=("project",),
            )
            self._node_index[proj_iid] = {
                "type": "project", "id": project.id, "title": project.title,
            }

            for task in matching_tasks:
                prio_label = PRIORITY_LABELS.get(task.priority, f"P{task.priority}")
                task_iid = f"task_{task.id}"
                sched = task.scheduled_date.strftime("%m/%d") if task.scheduled_date else ""
                t_alloc = task.time_allocated_total
                t_spent = task.time_spent_total
                t_time = f"{t_alloc:.1f}/{t_spent:.1f}" if t_alloc or t_spent else ""
                self.tree.insert(
                    proj_iid, "end", iid=task_iid,
                    values=(
                        task.title, task.supervisor, task.site,
                        task.status, prio_label, sched, t_time, project.category,
                    ),
                    tags=(f"p{task.priority}",),
                )
                self._node_index[task_iid] = {
                    "type": "task", "id": task.id, "title": task.title,
                    "project_id": project.id,
                }

                for deliv in task.deliverables:
                    d_iid = f"deliv_{deliv.id}"
                    pct = f"{deliv.percent_complete}%"
                    d_alloc = f"{deliv.time_allocated:.1f}" if deliv.time_allocated else ""
                    d_spent = f"{deliv.time_spent:.1f}" if deliv.time_spent else ""
                    d_time = f"{d_alloc}/{d_spent}" if d_alloc or d_spent else ""
                    self.tree.insert(
                        task_iid, "end", iid=d_iid,
                        values=(deliv.title, "", "", deliv.status, pct, "", d_time, ""),
                        tags=("deliverable",),
                    )
                    self._node_index[d_iid] = {
                        "type": "deliverable", "id": deliv.id,
                        "title": deliv.title, "task_id": task.id,
                        "task_title": task.title,
                    }

        # Colour-code by priority (config-driven)
        for prio in range(1, 6):
            bg = TREEVIEW_TAG_COLORS.get(f"p{prio}", "#ffffff")
            self.tree.tag_configure(f"p{prio}", background=bg)
        self.tree.tag_configure("project",
                                background=TREEVIEW_TAG_COLORS.get("project", "#dce6f5"),
                                font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("deliverable",
                                foreground=TREEVIEW_TAG_COLORS.get("deliverable_fg", "#555555"))

        self.update_status_bar()

    # ── Edit ───────────────────────────────────────────────────────────────
    def _edit_selected_task(self):
        node = self._selected_node()
        if not node:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        if node["type"] != "task":
            messagebox.showinfo("Select a Task", "Please select a task to edit (not a project or deliverable).")
            return

        task_id = node["id"]
        task = self.app.profile.find_task_global(task_id)
        if not task:
            return

        def on_save(data: dict):
            self.app.service.edit_task(task_id, data)
            self.refresh()

        TaskDialog(self.winfo_toplevel(), title="Edit Task", task=task,
                   project_id=node.get("project_id", ""), on_save=on_save)

    # ── Delete ─────────────────────────────────────────────────────────────
    def _delete_selected_task(self):
        node = self._selected_node()
        if not node:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        if node["type"] != "task":
            messagebox.showinfo("Select a Task", "Only tasks can be deleted from this view.")
            return

        title = node["title"]
        if not messagebox.askyesno("Confirm Delete", f"Delete task:\n\n\"{title}\"?"):
            return
        self.app.service.delete_task(node["id"])
        self.refresh()

    # ── Duplicate ──────────────────────────────────────────────────────────
    def _duplicate_selected_task(self):
        node = self._selected_node()
        if not node:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        if node["type"] != "task":
            messagebox.showinfo("Select a Task", "Please select a task to duplicate.")
            return

        task = self.app.profile.find_task_global(node["id"])
        if not task:
            return

        def on_save(data: dict):
            project_id = data.pop("project_id", node.get("project_id", ""))
            self.app.service.add_task(project_id, data)
            self.refresh()

        TaskDialog(self.winfo_toplevel(), title="Duplicate Task", task=task,
                   project_id=node.get("project_id", ""), on_save=on_save)

    # ── Attachments ────────────────────────────────────────────────────────
    def _attach_file_to_task(self):
        task_id = self._selected_task_id()
        title = self._selected_task_title()
        if not task_id:
            messagebox.showinfo("No Selection", "Select a task first.")
            return

        files = filedialog.askopenfilenames(
            title=f"Attach files to: {title}",
            filetypes=[("All Files", "*.*")],
        )
        if not files:
            return

        copied = attach_files(task_id, list(files))
        messagebox.showinfo(
            "Files Attached",
            f"Attached {len(copied)} file(s) to \"{title}\":\n\n" + "\n".join(copied),
        )

    def _view_attachments(self):
        task_id = self._selected_task_id()
        title = self._selected_task_title()
        if not task_id:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        if not open_attachments_folder(task_id):
            messagebox.showinfo("No Attachments", f"No attachments found for \"{title}\".")

    # ── Context Menu ───────────────────────────────────────────────────────
    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _quick_set_status(self, new_status: str):
        node = self._selected_node()
        if not node or node["type"] != "task":
            return
        self.app.service.set_status(node["id"], new_status)
        self.refresh()

    def _quick_set_priority(self, new_priority: int):
        node = self._selected_node()
        if not node or node["type"] != "task":
            return
        self.app.service.set_priority(node["id"], new_priority)
        self.refresh()

    # ── Batch Operations ───────────────────────────────────────────────────
    def _batch_edit(self):
        """Open batch edit dialog for all selected tasks."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Select one or more tasks first.")
            return

        # Collect task IDs from selected items (skip projects / deliverables)
        task_ids = []
        for iid in sel:
            node = self._node_index.get(iid)
            if node and node["type"] == "task":
                task_ids.append(node["id"])

        if not task_ids:
            messagebox.showinfo(
                "No Tasks Selected",
                "Select task rows (not projects or deliverables) for batch editing.",
            )
            return

        BatchOperationDialog(
            self.winfo_toplevel(),
            task_ids=task_ids,
            service=self.app.service,
            on_complete=self.refresh,
        )

    # ── Deliverable CRUD ───────────────────────────────────────────────────
    def _add_deliverable(self):
        node = self._selected_node()
        if not node:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        # Allow adding when task or its deliverable is selected
        if node["type"] == "task":
            task_id = node["id"]
        elif node["type"] == "deliverable":
            task_id = node["task_id"]
        else:
            messagebox.showinfo("Select a Task", "Select a task to add a deliverable to.")
            return

        def on_save(data: dict):
            self.app.service.add_deliverable(task_id, data)
            self.refresh()

        DeliverableDialog(self.winfo_toplevel(), title="Add Deliverable",
                          task_id=task_id, on_save=on_save)

    def _edit_deliverable(self):
        node = self._selected_node()
        if not node or node["type"] != "deliverable":
            messagebox.showinfo("Select a Deliverable", "Select a deliverable to edit.")
            return

        task = self.app.profile.find_task_global(node["task_id"])
        if not task:
            return
        deliv = task.find_deliverable(node["id"])
        if not deliv:
            return

        def on_save(data: dict):
            self.app.service.edit_deliverable(node["id"], data)
            self.refresh()

        DeliverableDialog(self.winfo_toplevel(), title="Edit Deliverable",
                          deliverable=deliv, task_id=node["task_id"],
                          on_save=on_save)

    def _delete_deliverable(self):
        node = self._selected_node()
        if not node or node["type"] != "deliverable":
            messagebox.showinfo("Select a Deliverable", "Select a deliverable to delete.")
            return
        title = node["title"]
        if not messagebox.askyesno("Confirm Delete", f"Delete deliverable:\n\n\"{title}\"?"):
            return
        self.app.service.delete_deliverable(node["id"])
        self.refresh()

    # ── Link Folder ────────────────────────────────────────────────────────
    def _link_folder_to_task(self):
        title = self._selected_task_title()
        if not title:
            messagebox.showinfo("No Selection", "Select a task first.")
            return

        folder = filedialog.askdirectory(title=f"Link project folder for: {title}")
        if not folder:
            return

        set_link(title, folder)
        messagebox.showinfo("Folder Linked", f"Linked folder for \"{title}\":\n\n{folder}")

    def _open_linked_folder(self):
        title = self._selected_task_title()
        if not title:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        if not _open_linked(title):
            messagebox.showinfo("No Linked Folder",
                                f"No linked folder found for \"{title}\".\n\n"
                                "Use 'Link Folder' to associate a project directory.")

    # ── Task Notes ─────────────────────────────────────────────────────────
    def _open_task_notes(self):
        task_id = self._selected_task_id()
        title = self._selected_task_title()
        if not task_id:
            messagebox.showinfo("No Selection", "Select a task first.")
            return
        TaskNotesDialog(self.winfo_toplevel(), task_id=task_id, task_title=title or "")

    # ── Drag-and-Drop ──────────────────────────────────────────────────────
    def _setup_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind("<<Drop>>", self._on_drop_files)
            self._dnd_available = True
        except ImportError:
            self._dnd_available = False
        except Exception:
            self._dnd_available = False

    def _on_drop_files(self, event):
        task_id = self._selected_task_id()
        title = self._selected_task_title()
        if not task_id:
            messagebox.showinfo("No Selection", "Select a task first, then drop files onto it.")
            return

        raw = event.data
        files: list[str] = []
        if "{" in raw:
            files = re.findall(r"\{([^}]+)\}", raw)
            remainder = re.sub(r"\{[^}]+\}", "", raw).strip()
            if remainder:
                files.extend(remainder.split())
        else:
            files = raw.split()

        valid = [f for f in files if Path(f).is_file()]
        if valid:
            copied = attach_files(task_id, valid)
            messagebox.showinfo(
                "Files Attached",
                f"Dropped {len(copied)} file(s) onto \"{title}\":\n\n" + "\n".join(copied),
            )
