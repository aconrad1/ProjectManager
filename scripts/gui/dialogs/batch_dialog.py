"""Batch Operations dialog — apply status, priority, or date changes to multiple tasks."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk

from gui.ui_theme import AG_DARK, AG_MID, STATUS_OPTIONS, PRIORITY_LABELS


class BatchOperationDialog(ctk.CTkToplevel):
    """Dialog for batch-applying changes to a set of task IDs.

    Parameters
    ----------
    parent : widget
        Parent window.
    task_ids : list[str]
        The T-NNN IDs to operate on.
    service : DomainService
        Mutation service.
    on_complete : callable
        Called after changes are applied so the caller can refresh.
    """

    def __init__(self, parent, *, task_ids: list[str], service, on_complete=None):
        super().__init__(parent)
        self.title("Batch Operations")
        self.geometry("480x420")
        self.resizable(True, True)
        self.minsize(400, 360)
        self.transient(parent)
        self.grab_set()

        self._task_ids = task_ids
        self._service = service
        self._on_complete = on_complete

        pad = {"padx": 16, "pady": (4, 0)}

        # Header
        ctk.CTkLabel(
            self, text=f"Batch Edit — {len(task_ids)} task(s)",
            font=("Segoe UI", 16, "bold"), text_color=AG_DARK,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            self, text="Leave fields blank to skip (no change).",
            font=("Segoe UI", 10), text_color="gray",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=0)

        # ── Status ──────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Set Status:", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", **pad
        )
        self._status_var = ctk.StringVar(value="")
        ctk.CTkOptionMenu(
            scroll, variable=self._status_var,
            values=["(no change)"] + STATUS_OPTIONS, width=280,
        ).pack(anchor="w", padx=16, pady=(2, 8))

        # ── Priority ────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Set Priority:", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", **pad
        )
        self._prio_labels = ["(no change)"] + list(PRIORITY_LABELS.values())
        self._prio_var = ctk.StringVar(value="(no change)")
        ctk.CTkOptionMenu(
            scroll, variable=self._prio_var,
            values=self._prio_labels, width=280,
        ).pack(anchor="w", padx=16, pady=(2, 8))

        # ── Date Shift ──────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Shift Dates (days):", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", **pad
        )
        shift_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        shift_frame.pack(anchor="w", padx=16, pady=(2, 4))

        self._shift_start_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            shift_frame, text="Shift Start", variable=self._shift_start_var,
        ).pack(side="left", padx=(0, 12))

        self._shift_end_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            shift_frame, text="Shift End", variable=self._shift_end_var,
        ).pack(side="left", padx=(0, 12))

        self._shift_deadline_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            shift_frame, text="Shift Deadline", variable=self._shift_deadline_var,
        ).pack(side="left")

        days_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        days_frame.pack(anchor="w", padx=16, pady=(2, 8))
        ctk.CTkLabel(days_frame, text="Days:", font=("Segoe UI", 11)).pack(side="left", padx=(0, 6))
        self._shift_days_entry = ctk.CTkEntry(days_frame, width=80, placeholder_text="0")
        self._shift_days_entry.pack(side="left")
        ctk.CTkLabel(
            days_frame, text="(negative = earlier)", font=("Segoe UI", 9),
            text_color="gray",
        ).pack(side="left", padx=(8, 0))

        # ── Action buttons ──────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(8, 12))

        ctk.CTkButton(
            btn_frame, text="Apply", width=140, height=36,
            font=("Segoe UI", 13, "bold"), fg_color=AG_DARK, hover_color=AG_MID,
            command=self._apply,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=36,
            fg_color="gray", hover_color="darkgray",
            command=self.destroy,
        ).pack(side="left")

    def _apply(self) -> None:
        changes = 0

        # Status
        status = self._status_var.get()
        if status and status != "(no change)":
            for tid in self._task_ids:
                try:
                    self._service.set_status(tid, status)
                    changes += 1
                except Exception:
                    pass

        # Priority
        prio_label = self._prio_var.get()
        if prio_label != "(no change)":
            prio_int = None
            for k, v in PRIORITY_LABELS.items():
                if v == prio_label:
                    prio_int = k
                    break
            if prio_int is not None:
                for tid in self._task_ids:
                    try:
                        self._service.set_priority(tid, prio_int)
                        changes += 1
                    except Exception:
                        pass

        # Date shifting
        shift_days_str = self._shift_days_entry.get().strip()
        if shift_days_str:
            try:
                shift_days = int(shift_days_str)
            except ValueError:
                messagebox.showwarning("Invalid", "Days must be an integer.", parent=self)
                return

            if shift_days != 0:
                delta = timedelta(days=shift_days)
                shift_start = self._shift_start_var.get()
                shift_end = self._shift_end_var.get()
                shift_deadline = self._shift_deadline_var.get()

                if shift_start or shift_end or shift_deadline:
                    for tid in self._task_ids:
                        try:
                            profile = self._service._profile
                            task = profile.find_task_global(tid)
                            if not task:
                                continue
                            edits: dict = {}
                            if shift_start and isinstance(task.start, date):
                                edits["start"] = task.start + delta
                            if shift_end and isinstance(task.end, date):
                                edits["end"] = task.end + delta
                            if shift_deadline and isinstance(task.deadline, date):
                                edits["deadline"] = task.deadline + delta
                            if edits:
                                self._service.edit_task(tid, edits)
                                changes += 1
                        except Exception:
                            pass

        if changes:
            if self._on_complete:
                self._on_complete()
            self.destroy()
        else:
            messagebox.showinfo(
                "No Changes", "No changes were applied. Check your selections.",
                parent=self,
            )
