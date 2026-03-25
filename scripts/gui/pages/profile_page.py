"""
Profile Management page — CRUD for user profiles, live switching,
historical workbook import, and profile export/import.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from tkinter import messagebox, filedialog

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import AG_DARK, AG_MID, AG_LIGHT, AG_WASH
from helpers.profile.profile import (
    get_profiles, get_active_index, switch_profile, save_profile,
    init_profile, delete_profile, scaffold_profile,
    reload as reload_profile,
    ensure_profile_dirs,
)
from helpers.profile.config import workbook_path, profile_dir
from helpers.profile.portability import export_profile, import_profile
from helpers.io.paths import PROFILES_DIR


# ── Profile field definitions ─────────────────────────────────────────────────
_PROFILE_FIELDS: list[tuple[str, str, str]] = [
    # (yaml_key, display_label, placeholder)
    ("name",              "Name",              "Full name"),
    ("role",              "Role",              "Job title / role"),
    ("company",           "Company",           "Company or context name"),
    ("email",             "Email",             "you@company.com"),
    ("phone",             "Phone",             "Phone number"),
    ("recipient_name",    "Recipient",         "Manager / recipient name"),
    ("recipient_email",   "Recipient Email",   "manager@company.com"),
    ("workbook_filename", "Workbook Filename", "e.g. Projects.xlsx"),
    ("daily_hours_budget","Daily Hours Budget", "8.0"),
]


class ProfilePage(BasePage):
    KEY = "profiles"
    TITLE = "Profile Management"

    def build(self) -> None:
        self._selected_idx: int | None = None

        # ── Top-level horizontal split: list (left) + detail (right) ──────
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=14, pady=10)
        outer.grid_columnconfigure(0, weight=1, minsize=260)
        outer.grid_columnconfigure(1, weight=2, minsize=420)
        outer.grid_rowconfigure(0, weight=1)

        # ── LEFT: profile list ────────────────────────────────────────────
        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Profiles", font=("Segoe UI", 16, "bold"),
                     text_color=AG_DARK).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self._list_frame = ctk.CTkScrollableFrame(left, fg_color=AG_WASH)
        self._list_frame.grid(row=1, column=0, sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ctk.CTkButton(
            btn_row, text="+ New Profile", width=130, height=34,
            font=("Segoe UI", 12, "bold"), fg_color=AG_DARK, hover_color=AG_MID,
            command=self._new_profile,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="Delete", width=90, height=34,
            font=("Segoe UI", 12), fg_color="#c0392b", hover_color="#e74c3c",
            command=self._delete_profile,
        ).pack(side="left")

        # ── RIGHT: detail editor ──────────────────────────────────────────
        right = ctk.CTkFrame(outer, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._detail_title = ctk.CTkLabel(
            right, text="Select a profile", font=("Segoe UI", 16, "bold"),
            text_color=AG_DARK,
        )
        self._detail_title.grid(row=0, column=0, sticky="w", pady=(0, 6))

        detail_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        detail_scroll.grid(row=1, column=0, sticky="nsew")
        detail_scroll.grid_columnconfigure(1, weight=1)

        self._entries: dict[str, ctk.CTkEntry] = {}
        for r, (key, label, placeholder) in enumerate(_PROFILE_FIELDS):
            ctk.CTkLabel(
                detail_scroll, text=f"{label}:", font=("Segoe UI", 12, "bold"),
                width=140, anchor="e",
            ).grid(row=r, column=0, sticky="e", padx=(0, 10), pady=4)
            entry = ctk.CTkEntry(detail_scroll, placeholder_text=placeholder)
            entry.grid(row=r, column=1, sticky="ew", pady=4)
            self._entries[key] = entry

        # ── Action buttons below fields ───────────────────────────────────
        action_row = ctk.CTkFrame(right, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        ctk.CTkButton(
            action_row, text="Save Changes", width=150, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=AG_DARK, hover_color=AG_MID,
            command=self._save_profile,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_row, text="Switch To", width=120, height=38,
            font=("Segoe UI", 12), fg_color=AG_MID, hover_color=AG_DARK,
            command=self._switch_to_profile,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_row, text="Import Workbook…", width=160, height=38,
            font=("Segoe UI", 12), fg_color="gray", hover_color="darkgray",
            command=self._import_workbook,
        ).pack(side="left", padx=(0, 8))

        # ── Export / Import profile buttons ───────────────────────────────
        portability_row = ctk.CTkFrame(right, fg_color="transparent")
        portability_row.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        ctk.CTkButton(
            portability_row, text="Export Profile…", width=140, height=34,
            font=("Segoe UI", 12), fg_color="#2980b9", hover_color="#3498db",
            command=self._export_profile,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            portability_row, text="Import Profile…", width=140, height=34,
            font=("Segoe UI", 12), fg_color="#2980b9", hover_color="#3498db",
            command=self._import_profile_bundle,
        ).pack(side="left")

        self._status_label = ctk.CTkLabel(
            right, text="", font=("Segoe UI", 10), text_color="gray",
        )
        self._status_label.grid(row=4, column=0, sticky="w", pady=(6, 0))

    # ═══════════════════════════════════════════════════════════════════════
    #  REFRESH — rebuild the list from YAML
    # ═══════════════════════════════════════════════════════════════════════
    def refresh(self) -> None:
        self._rebuild_list()
        # Auto-select active profile
        active = get_active_index()
        self._select_profile(active)

    def _rebuild_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()

        profiles = get_profiles()
        active = get_active_index()
        for i, p in enumerate(profiles):
            label = p.get("company") or p.get("name") or f"Profile {i + 1}"
            is_active = i == active

            btn = ctk.CTkButton(
                self._list_frame,
                text=f"{'● ' if is_active else '   '}{label}",
                font=("Segoe UI", 12, "bold" if is_active else "normal"),
                fg_color=AG_MID if is_active else "transparent",
                text_color="white" if is_active else AG_DARK,
                hover_color=AG_LIGHT,
                anchor="w", height=36, corner_radius=6,
                command=lambda idx=i: self._select_profile(idx),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=4, pady=2)

    # ═══════════════════════════════════════════════════════════════════════
    #  SELECT / POPULATE DETAIL
    # ═══════════════════════════════════════════════════════════════════════
    def _select_profile(self, index: int) -> None:
        profiles = get_profiles()
        if index < 0 or index >= len(profiles):
            return
        self._selected_idx = index
        p = profiles[index]

        label = p.get("company") or p.get("name") or f"Profile {index + 1}"
        active_tag = " (active)" if index == get_active_index() else ""
        self._detail_title.configure(text=f"{label}{active_tag}")

        for key, entry in self._entries.items():
            entry.delete(0, "end")
            val = p.get(key, "")
            if val:
                entry.insert(0, str(val))

        self._status_label.configure(text="", text_color="gray")
        self._rebuild_list()

    # ═══════════════════════════════════════════════════════════════════════
    #  NEW PROFILE
    # ═══════════════════════════════════════════════════════════════════════
    def _new_profile(self) -> None:
        dialog = _NewProfileDialog(self, on_create=self._on_profile_created)
        dialog.focus()

    def _on_profile_created(self, data: dict) -> None:
        try:
            idx = init_profile(data)
            # Auto-switch to the new profile so its workbook/JSON get created
            switch_profile(idx)
            reload_profile()
            ensure_profile_dirs()
            self.app._build_sidebar()
            self.app.reload_data()
            self._rebuild_list()
            self._select_profile(idx)
            self._set_status("Profile created and activated.", ok=True)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  DELETE PROFILE
    # ═══════════════════════════════════════════════════════════════════════
    def _delete_profile(self) -> None:
        if self._selected_idx is None:
            return
        profiles = get_profiles()

        p = profiles[self._selected_idx]
        label = p.get("company") or p.get("name", "this profile")

        is_last = len(profiles) == 1
        if is_last:
            confirm = messagebox.askyesno(
                "Delete Last Profile",
                f"Delete profile \"{label}\"?\n\n"
                "A default fallback profile will be created automatically.",
                parent=self,
            )
            if not confirm:
                return
            remove_files = True
        else:
            remove_files = messagebox.askyesnocancel(
            "Delete Profile",
            f"Delete profile \"{label}\"?\n\n"
            "Yes = delete profile AND its files on disk\n"
            "No = remove from list only, keep files\n"
            "Cancel = abort",
            parent=self,
        )
        if remove_files is None:  # Cancel
            return

        try:
            delete_profile(self._selected_idx, remove_files=remove_files)
            reload_profile()
            ensure_profile_dirs()
            self.app._build_sidebar()
            self.app.reload_data()
            self._selected_idx = None
            self.refresh()
            self._set_status("Profile deleted.", ok=True)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  SAVE CHANGES
    # ═══════════════════════════════════════════════════════════════════════
    def _save_profile(self) -> None:
        if self._selected_idx is None:
            return
        data: dict = {}
        for key, entry in self._entries.items():
            val = entry.get().strip()
            if key == "daily_hours_budget":
                try:
                    data[key] = float(val) if val else 8.0
                except ValueError:
                    data[key] = 8.0
            else:
                data[key] = val

        if not data.get("name"):
            messagebox.showwarning("Missing Name", "Name is required.", parent=self)
            return
        if not data.get("company"):
            messagebox.showwarning("Missing Company", "Company is required.", parent=self)
            return

        # Auto-append .xlsx if missing
        wb_name = data.get("workbook_filename", "")
        if wb_name and not wb_name.lower().endswith(".xlsx"):
            data["workbook_filename"] = wb_name + ".xlsx"
            self._entries["workbook_filename"].delete(0, "end")
            self._entries["workbook_filename"].insert(0, data["workbook_filename"])

        try:
            save_profile(self._selected_idx, data)
            reload_profile()
            # Scaffold dirs in case company name changed
            scaffold_profile(data["company"], data.get("workbook_filename", ""))

            # Rebuild sidebar to reflect name/company changes
            self.app._build_sidebar()

            # If the edited profile is the active one, reload app data
            if self._selected_idx == get_active_index():
                self.app.reload_data()

            self._rebuild_list()
            self._set_status("Profile saved.", ok=True)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  SWITCH TO
    # ═══════════════════════════════════════════════════════════════════════
    def _switch_to_profile(self) -> None:
        if self._selected_idx is None:
            return
        if self._selected_idx == get_active_index():
            self._set_status("Already the active profile.")
            return

        # Save current workbook first
        if self.app.wb is not None and self.app.profile is not None:
            try:
                self.app.save_state()
            except Exception:
                pass

        try:
            switch_profile(self._selected_idx)
            reload_profile()
            ensure_profile_dirs()
            self.app._build_sidebar()
            self.app.reload_data()
            self.refresh()
            self._set_status("Switched to profile.", ok=True)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  IMPORT WORKBOOK
    # ═══════════════════════════════════════════════════════════════════════
    def _import_workbook(self) -> None:
        """Import data from a historical / external Excel workbook into the
        selected profile's template workbook.  Matches columns by header name.
        """
        if self._selected_idx is None:
            messagebox.showinfo("Select Profile", "Select a profile first.", parent=self)
            return

        src = filedialog.askopenfilename(
            title="Select workbook to import",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            parent=self,
        )
        if not src:
            return

        profiles = get_profiles()
        p = profiles[self._selected_idx]
        company = p.get("company", "")
        wb_name = p.get("workbook_filename", "")

        if not company or not wb_name:
            messagebox.showwarning(
                "Incomplete Profile",
                "The profile must have Company and Workbook Filename set before importing.",
                parent=self,
            )
            return

        try:
            from helpers.profile.import_workbook import import_historical_workbook
            stats = import_historical_workbook(src, company, wb_name)
            self._set_status(
                f"Imported: {stats['rows_imported']} rows across {stats['sheets_matched']} sheets. "
                f"{stats['cols_skipped']} columns skipped.",
                ok=True,
            )
            # Reload if this is the active profile
            if self._selected_idx == get_active_index():
                self.app.reload_data()
        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  EXPORT / IMPORT PROFILE BUNDLE
    # ═══════════════════════════════════════════════════════════════════════
    def _export_profile(self) -> None:
        """Export the selected profile as a .pmprofile bundle."""
        if self._selected_idx is None:
            messagebox.showinfo("Select Profile", "Select a profile first.", parent=self)
            return

        profiles = get_profiles()
        p = profiles[self._selected_idx]
        default_name = p.get("company", "profile")

        dest = filedialog.asksaveasfilename(
            title="Export Profile",
            defaultextension=".pmprofile",
            initialfile=f"{default_name}.pmprofile",
            filetypes=[("Profile bundle", "*.pmprofile"), ("All files", "*.*")],
            parent=self,
        )
        if not dest:
            return

        try:
            out = export_profile(self._selected_idx, Path(dest))
            self._set_status(f"Exported to {out.name}", ok=True)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    def _import_profile_bundle(self) -> None:
        """Import a .pmprofile bundle as a new profile."""
        src = filedialog.askopenfilename(
            title="Import Profile Bundle",
            filetypes=[("Profile bundle", "*.pmprofile"), ("All files", "*.*")],
            parent=self,
        )
        if not src:
            return

        try:
            idx = import_profile(Path(src))
            reload_profile()
            ensure_profile_dirs()
            self.app._build_sidebar()
            self.app.reload_data()
            self._rebuild_list()
            self._select_profile(idx)
            self._set_status("Profile imported successfully.", ok=True)
        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════════
    def _set_status(self, text: str, ok: bool = False) -> None:
        color = "#27ae60" if ok else "gray"
        self._status_label.configure(text=text, text_color=color)


# ═══════════════════════════════════════════════════════════════════════════════
#  NEW PROFILE DIALOG
# ═══════════════════════════════════════════════════════════════════════════════
class _NewProfileDialog(ctk.CTkToplevel):
    """Minimal dialog for creating a new profile — name + company are required."""

    def __init__(self, parent, on_create=None):
        super().__init__(parent)
        self.title("New Profile")
        self.geometry("440x420")
        self.resizable(True, True)
        self.minsize(360, 360)
        self.transient(parent)
        self.grab_set()

        self._on_create = on_create

        pad = {"padx": 14, "pady": (4, 0)}

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        self._entries: dict[str, ctk.CTkEntry] = {}
        for key, label, placeholder in _PROFILE_FIELDS:
            ctk.CTkLabel(scroll, text=f"{label}:", font=("Segoe UI", 12, "bold")).pack(anchor="w", **pad)
            entry = ctk.CTkEntry(scroll, placeholder_text=placeholder)
            entry.pack(anchor="w", fill="x", padx=14, pady=(2, 4))
            self._entries[key] = entry

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=10)
        ctk.CTkButton(
            btn_frame, text="Create", width=140, fg_color=AG_DARK,
            hover_color=AG_MID, command=self._create,
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Cancel", width=140, fg_color="gray",
            hover_color="darkgray", command=self.destroy,
        ).pack(side="right")

    def _create(self) -> None:
        data: dict = {}
        for key, entry in self._entries.items():
            val = entry.get().strip()
            if key == "daily_hours_budget":
                try:
                    data[key] = float(val) if val else 8.0
                except ValueError:
                    data[key] = 8.0
            else:
                data[key] = val

        if not data.get("name"):
            messagebox.showwarning("Missing Name", "Name is required.", parent=self)
            return
        if not data.get("company"):
            messagebox.showwarning("Missing Company", "Company is required.", parent=self)
            return

        # Auto-append .xlsx if missing
        wb_name = data.get("workbook_filename", "")
        if wb_name and not wb_name.lower().endswith(".xlsx"):
            data["workbook_filename"] = wb_name + ".xlsx"

        if self._on_create:
            self._on_create(data)
        self.destroy()
