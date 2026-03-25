"""
TaskNotesDialog — modal dialog for viewing and adding timestamped task notes.
"""
from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from gui.ui_theme import AG_DARK, AG_MID
from helpers.attachments.notes import load_notes as _load_notes, save_notes as _save_notes


class TaskNotesDialog(ctk.CTkToplevel):
    """Dialog for viewing and adding timestamped notes to a task."""

    def __init__(self, parent, task_id: str, task_title: str = ""):
        super().__init__(parent)
        display_name = task_title or task_id
        self.title(f"Notes — {display_name}")
        self.geometry("520x480")
        self.resizable(True, True)
        self.minsize(400, 350)
        self.transient(parent)
        self.grab_set()

        self._task_id = task_id

        ctk.CTkLabel(self, text=f"Activity Log: {display_name}",
                     font=("Segoe UI", 14, "bold"), text_color=AG_DARK,
                     wraplength=480).pack(anchor="w", padx=14, pady=(12, 6))

        # ── Existing notes display ─────────────────────────────────────────
        self._notes_display = ctk.CTkTextbox(self, font=("Consolas", 10), state="disabled")
        self._notes_display.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # ── New note entry ─────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Add Note:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14)
        self._note_entry = ctk.CTkTextbox(self, height=60)
        self._note_entry.pack(fill="x", padx=14, pady=(2, 6))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkButton(btn_frame, text="Add Note", width=120, fg_color=AG_DARK,
                      hover_color=AG_MID, command=self._add_note).pack(side="left")
        ctk.CTkButton(btn_frame, text="Close", width=100, fg_color="gray",
                      hover_color="darkgray", command=self.destroy).pack(side="right")

        self._refresh_notes()

    def _refresh_notes(self):
        notes = _load_notes()
        entries = notes.get(self._task_id, [])

        self._notes_display.configure(state="normal")
        self._notes_display.delete("1.0", "end")
        if entries:
            for entry in reversed(entries):  # newest first
                self._notes_display.insert("end", f"[{entry['timestamp']}]\n{entry['text']}\n\n")
        else:
            self._notes_display.insert("end", "No notes yet.")
        self._notes_display.configure(state="disabled")

    def _add_note(self):
        text = self._note_entry.get("1.0", "end").strip()
        if not text:
            return
        notes = _load_notes()
        if self._task_id not in notes:
            notes[self._task_id] = []
        notes[self._task_id].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": text,
        })
        _save_notes(notes)
        self._note_entry.delete("1.0", "end")
        self._refresh_notes()
