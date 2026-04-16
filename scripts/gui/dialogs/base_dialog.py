"""BaseDialog — shared base class for modal dialogs.

Provides the duplicated helper methods (_get, _parse_date) and the
standard Save/Cancel button frame that all three main dialogs share.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable

import customtkinter as ctk

from gui.ui_theme import AG_DARK, AG_MID


class BaseDialog(ctk.CTkToplevel):
    """Base class for modal dialogs.

    Subclasses must:
    - Call ``super().__init__(parent, ...)`` in their ``__init__``
    - Populate ``self.entries`` with their widgets
    - Implement ``_save()`` with their own validation and persistence logic
    - Call ``self._build_button_frame(self._save)`` to render the standard buttons
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.entries: dict = {}

    # ── Widget reader ──────────────────────────────────────────────────────

    def _get(self, key: str) -> str:
        """Read the current value from any supported widget type."""
        w = self.entries[key]
        if isinstance(w, ctk.CTkEntry):
            return w.get().strip()
        elif isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        elif hasattr(w, "_variable"):
            return w._variable.get()
        return ""

    # ── Date parser ────────────────────────────────────────────────────────

    def _parse_date(self, key: str):
        """Parse a YYYY-MM-DD date entry, returning None if empty/invalid."""
        raw = self._get(key)
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None

    # ── Button frame ───────────────────────────────────────────────────────

    def _build_button_frame(self, save_command: Callable) -> None:
        """Render the standard Save/Cancel button row."""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=10)
        ctk.CTkButton(
            btn_frame, text="Save", width=140, fg_color=AG_DARK,
            hover_color=AG_MID, command=save_command,
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Cancel", width=140, fg_color="gray",
            hover_color="darkgray", command=self.destroy,
        ).pack(side="right")
