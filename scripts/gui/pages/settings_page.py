"""
Settings page — application info, paths display, appearance toggle.

Profile editing has moved to the dedicated Profile Management page.
"""
from __future__ import annotations

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import AG_DARK, AG_MID
import helpers.profile.profile as _prof
from helpers.profile.profile import get_active_config
from helpers.profile.config import (
    workbook_path, reports_dir, exports_dir, data_dir, attachments_dir, profile_dir,
)
from helpers.io.paths import PROFILE_PATH
from helpers.io.files import open_path


class SettingsPage(BasePage):
    KEY = "settings"
    TITLE = "Settings"

    def build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=14)

        # ── Active profile summary (read-only) ────────────────────────────
        ctk.CTkLabel(scroll, text="Active Profile", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).pack(anchor="w", pady=(0, 4))

        self._profile_summary = ctk.CTkLabel(
            scroll, text="", font=("Segoe UI", 11), text_color="gray",
        )
        self._profile_summary.pack(anchor="w", pady=(0, 6))

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 8))
        ctk.CTkButton(
            btn_row, text="Manage Profiles", width=160, height=36,
            font=("Segoe UI", 13, "bold"), fg_color=AG_DARK, hover_color=AG_MID,
            command=lambda: self.app.show_page("profiles"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="Open YAML File", width=160,
            fg_color="gray", hover_color="darkgray",
            command=lambda: open_path(PROFILE_PATH),
        ).pack(side="left")

        # ── Application paths ──────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="", height=20).pack()
        ctk.CTkLabel(scroll, text="Application Paths", font=("Segoe UI", 14, "bold"),
                     text_color=AG_DARK).pack(anchor="w", pady=(0, 6))

        self._path_labels: list[tuple[str, ctk.CTkLabel]] = []
        path_fields = [
            "Profile Dir", "Workbook", "Reports", "Exports", "Data", "Attachments",
        ]
        for label in path_fields:
            row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=f"{label}:", font=("Segoe UI", 11, "bold"),
                         width=120, anchor="e").pack(side="left", padx=(0, 12))
            val_lbl = ctk.CTkLabel(row_frame, text="", font=("Segoe UI", 10),
                                   text_color="gray")
            val_lbl.pack(side="left")
            self._path_labels.append((label, val_lbl))

        # ── Appearance toggle ──────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="", height=20).pack()
        ctk.CTkLabel(scroll, text="Appearance", font=("Segoe UI", 14, "bold"),
                     text_color=AG_DARK).pack(anchor="w", pady=(0, 6))

        self._appearance_var = ctk.StringVar(value="Light")
        ctk.CTkOptionMenu(
            scroll, variable=self._appearance_var,
            values=["Light", "Dark", "System"], width=180,
            command=lambda v: ctk.set_appearance_mode(v.lower()),
        ).pack(anchor="w")

    def refresh(self) -> None:
        """Update displayed paths and profile summary from live state."""
        _cfg = get_active_config()
        self._profile_summary.configure(
            text=f"{_cfg.name}  ·  {_cfg.company}  ·  {_cfg.role}"
        )
        _path_values = {
            "Profile Dir":  str(profile_dir()),
            "Workbook":     str(workbook_path()),
            "Reports":      str(reports_dir()),
            "Exports":      str(exports_dir()),
            "Data":         str(data_dir()),
            "Attachments":  str(attachments_dir()),
        }
        for label, lbl_widget in self._path_labels:
            lbl_widget.configure(text=_path_values.get(label, ""))
