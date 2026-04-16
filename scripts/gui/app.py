"""
AltaGas Weekly Report Generator — Desktop GUI (orchestrator)
=============================================================
Light orchestrator that holds shared state, sidebar navigation,
profile switching, keybindings, and delegates page rendering to
individual page modules under ``gui.pages.*``.

Usage:
    cd scripts
    python gui.py          # via shim
    python -m gui.run      # direct
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from tkinter import messagebox
from typing import Type

import customtkinter as ctk

_log = logging.getLogger(__name__)

# ── Ensure local imports work regardless of launch directory ───────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent.parent   # scripts/
_PROJECT_DIR = _SCRIPT_DIR.parent                       # project root
sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_PROJECT_DIR))

# ── Helpers ────────────────────────────────────────────────────────────────────
from helpers.profile.profile import (
    get_profiles, get_active_index, switch_profile, ensure_profile_dirs,
    reload as reload_profile,
)
import helpers.profile.profile as _prof
from helpers.profile.config import (
    workbook_path, markdown_dir, pdf_dir, profile_dir,
)
from helpers.io.paths import BASE_DIR, PROFILES_DIR
from helpers.data.workbook import load_workbook
from helpers.persistence.contract import (
    sync as sync_profile,
    save as save_profile_dual,
    detect_external_edits,
)
from helpers.domain.profile import Profile as DomainProfile
from helpers.commands.domain_service import DomainService

# ── Theme & base page ─────────────────────────────────────────────────────────
from gui.ui_theme import AG_DARK, AG_MID, AG_LIGHT
from gui.base_page import BasePage

# ── Page registry (config-driven — add new pages in page_registry.py) ─────────
from gui.page_registry import load_pages

# ── Ensure profile directories exist (only if profile is configured) ──────────
if _prof.USER_COMPANY and _prof.WORKBOOK_FILENAME:
    ensure_profile_dirs()


# ── Build page registry from config ───────────────────────────────────────────
_LOADED_PAGES = load_pages()   # [(key, PageClass, nav_label), ...]

PAGE_ORDER: list[str]              = [key for key, _, _   in _LOADED_PAGES]
PAGES: dict[str, Type[BasePage]]   = {key: cls for key, cls, _ in _LOADED_PAGES}
NAV_LABELS: dict[str, str]         = {key: lbl for key, _, lbl in _LOADED_PAGES}


# ═══════════════════════════════════════════════════════════════════════════════
#  APP ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    """Main application window — orchestrates pages, sidebar, and shared state."""

    def __init__(self):
        super().__init__()
        self.title(f"{_prof.USER_COMPANY or 'Setup'} — Weekly Report Generator")
        self.geometry("1150x740")
        self.minsize(950, 620)
        ctk.set_appearance_mode("light")

        # ── Shared state ───────────────────────────────────────────────────
        self.wb = None
        self.profile: DomainProfile | None = None
        self.service: DomainService | None = None
        self._active_page_key: str = "tasks"
        self._autosave_pending: bool = False
        self._autosave_id: str | None = None
        self._autosave_fail_count: int = 0
        self._last_edit_check: float = 0.0

        # ── Layout: sidebar + content container ────────────────────────────
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_sidebar()

        # ── Page container ─────────────────────────────────────────────────
        self._container = ctk.CTkFrame(self, corner_radius=0)
        self._container.grid(row=0, column=1, sticky="nsew")
        self._container.grid_columnconfigure(0, weight=1)
        self._container.grid_rowconfigure(0, weight=1)

        # ── Status bar ─────────────────────────────────────────────────────
        self._status_bar = ctk.CTkFrame(self, height=24, corner_radius=0, fg_color="#f0f0f0")
        self._status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._status_bar.grid_propagate(False)
        self._save_indicator = ctk.CTkLabel(
            self._status_bar, text="", font=("Segoe UI", 10), text_color="gray",
        )
        self._save_indicator.pack(side="right", padx=12)

        # ── Instantiate pages ──────────────────────────────────────────────
        self.pages: dict[str, BasePage] = {}
        for key in PAGE_ORDER:
            PageCls = PAGES[key]
            page = PageCls(self._container, app=self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

        # ── Boot ───────────────────────────────────────────────────────────
        self._load_or_prompt()
        self._bind_shortcuts()

    # ═══════════════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ═══════════════════════════════════════════════════════════════════════
    def _build_sidebar(self):
        # Destroy existing sidebar if rebuilding
        if hasattr(self, "_sidebar_frame") and self._sidebar_frame is not None:
            self._sidebar_frame.destroy()

        sb = ctk.CTkFrame(self, width=185, corner_radius=0, fg_color=AG_DARK)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        self._sidebar_frame = sb

        _sidebar_title = _prof.USER_COMPANY.split()[0] if _prof.USER_COMPANY else "Report"
        ctk.CTkLabel(sb, text=_sidebar_title, font=("Segoe UI", 24, "bold"),
                     text_color="white").pack(pady=(22, 0))
        ctk.CTkLabel(sb, text="Report Generator", font=("Segoe UI", 12),
                     text_color=AG_LIGHT).pack(pady=(0, 10))

        # ── Profile switcher (always visible) ──────────────────────────────
        profiles = get_profiles()
        profile_labels = [
            p.get("company") or p.get("name") or f"Profile {i+1}"
            for i, p in enumerate(profiles)
        ]
        self._profile_var = ctk.StringVar(value=profile_labels[get_active_index()])
        ctk.CTkOptionMenu(
            sb, variable=self._profile_var,
            values=profile_labels, width=160,
            fg_color=AG_MID, button_color=AG_MID,
            button_hover_color=AG_LIGHT,
            command=self._on_profile_switch,
        ).pack(padx=10, pady=(0, 18))

        # ── Nav buttons ────────────────────────────────────────────────────
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for key in PAGE_ORDER:
            label = NAV_LABELS[key]
            btn = ctk.CTkButton(
                sb, text=label, font=("Segoe UI", 13),
                fg_color="transparent", text_color="white",
                hover_color=AG_MID, anchor="w",
                height=40, corner_radius=6,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = btn

        ctk.CTkFrame(sb, fg_color="transparent").pack(expand=True)
        ctk.CTkLabel(sb, text=_prof.USER_NAME, font=("Segoe UI", 11, "bold"),
                     text_color="white").pack(side="bottom", pady=(0, 8))
        ctk.CTkLabel(sb, text=_prof.USER_ROLE, font=("Segoe UI", 10),
                     text_color=AG_LIGHT).pack(side="bottom")

    def rebuild_sidebar(self) -> None:
        """Rebuild the sidebar navigation (public API for pages)."""
        self._build_sidebar()

    # ── Profile switching ──────────────────────────────────────────────────
    def _on_profile_switch(self, selected_label: str):
        profiles = get_profiles()
        profile_labels = [
            p.get("company") or p.get("name") or f"Profile {i+1}"
            for i, p in enumerate(profiles)
        ]
        try:
            new_idx = profile_labels.index(selected_label)
        except ValueError:
            return
        if new_idx == get_active_index():
            return

        if self.wb is not None and self.profile is not None:
            if messagebox.askyesno("Save Before Switching?",
                                   "Save the current workbook before switching profiles?"):
                try:
                    save_profile_dual(self.profile, self.wb)
                    self.wb.save(str(workbook_path()))
                except Exception as e:
                    messagebox.showerror("Save Error", str(e))

        switch_profile(new_idx)
        reload_profile()
        ensure_profile_dirs()
        self._refresh_after_profile_change()

    def _refresh_after_profile_change(self) -> None:
        """Reload data, rebuild sidebar, and update the title bar after a profile change."""
        self.title(f"{_prof.USER_COMPANY} — Weekly Report Generator")
        self._build_sidebar()
        self.reload_data()

    # ═══════════════════════════════════════════════════════════════════════
    #  NAVIGATION
    # ═══════════════════════════════════════════════════════════════════════
    def show_page(self, key: str) -> None:
        # Check for external edits on tab change
        self._check_external_edits()
        for k, p in self.pages.items():
            p.grid_remove()
        self.pages[key].grid()
        self.pages[key].refresh()
        self._active_page_key = key
        for name, btn in self._nav_btns.items():
            btn.configure(fg_color=AG_MID if name == key else "transparent")

    def refresh_page(self, key: str) -> None:
        """Refresh a specific page if it exists."""
        page = self.pages.get(key)
        if page:
            page.refresh()

    # ═══════════════════════════════════════════════════════════════════════
    #  DATA LOADING  (AppContext)
    # ═══════════════════════════════════════════════════════════════════════
    def _profile_is_configured(self) -> bool:
        """Return True if the active profile has the minimum fields set."""
        return bool(_prof.USER_COMPANY and _prof.WORKBOOK_FILENAME)

    def _load_or_prompt(self) -> None:
        """Load data if the profile is configured, otherwise show the profile page."""
        if self._profile_is_configured():
            self.reload_data()
            self.show_page("tasks")
        else:
            # Unconfigured profile — show profile page for setup
            self.wb = None
            self.profile = None
            self.service = None
            self.show_page("profiles")

    def reload_data(self) -> None:
        if not self._profile_is_configured():
            # Nothing to load — keep profile page visible
            return

        wb_path = workbook_path()

        # Ensure the workbook exists (create from schema if needed)
        if not wb_path.exists():
            ensure_profile_dirs()
        if not wb_path.exists():
            # Still missing — scaffold failed or filename is invalid
            messagebox.showerror(
                "Workbook Not Found",
                f"Cannot find:\n{wb_path}\n\nCheck user_profile.yaml.",
            )
            return

        try:
            self.wb = load_workbook(wb_path)
            self.profile = sync_profile(
                self.wb,
                _prof.USER_COMPANY,
                wb_path,
                profile_name=_prof.USER_NAME,
                role=_prof.USER_ROLE,
                email=_prof.USER_EMAIL,
                phone=_prof.USER_PHONE,
                recipient_name=_prof.RECIPIENT_NAME,
                recipient_email=_prof.RECIPIENT_EMAIL,
                workbook_filename=_prof.WORKBOOK_FILENAME,
                daily_hours_budget=_prof.DAILY_HOURS_BUDGET,
            )
            self.service = DomainService(self.profile, self.wb, on_persist=self.mark_dirty)
            # Refresh active page after load
            active = self.pages.get(self._active_page_key)
            if active:
                active.refresh()
        except FileNotFoundError:
            messagebox.showerror(
                "Workbook Not Found",
                f"Cannot find:\n{wb_path}\n\nCheck user_profile.yaml.",
            )
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def log(self, text: str) -> None:
        gen = self.pages.get("generate")
        if gen and hasattr(gen, "log_write"):
            gen.log_write(text)

    def save_state(self) -> None:
        """Persist the current profile to JSON, workbook in-memory, and .xlsx on disk."""
        if self.profile and self.wb:
            # Check for external edits before overwriting
            self._check_external_edits()
            wb_path_val = workbook_path()
            save_profile_dual(self.profile, self.wb, wb_path=wb_path_val)
            try:
                self.wb.save(str(wb_path_val))
                self._update_save_indicator("Saved")
            except Exception as e:
                self._update_save_indicator(f"Save error: {e}")

    def save_and_refresh(self) -> None:
        """Save state and refresh the active page."""
        self.save_state()
        active = self.pages.get(self._active_page_key)
        if active:
            active.refresh()

    def mark_dirty(self) -> None:
        """Mark that an unsaved mutation has occurred; schedule debounced autosave."""
        self._update_save_indicator("Unsaved changes...")
        # Cancel any pending autosave
        if self._autosave_id is not None:
            self.after_cancel(self._autosave_id)
        # Schedule autosave after 2 seconds of inactivity
        self._autosave_id = self.after(2000, self._autosave)

    _MAX_AUTOSAVE_FAILURES: int = 3

    def _autosave(self) -> None:
        """Debounced autosave — writes .xlsx to disk."""
        self._autosave_id = None
        if not self.wb:
            return
        try:
            self.wb.save(str(workbook_path()))
            self._autosave_fail_count = 0
            self._update_save_indicator("Autosaved")
        except PermissionError:
            self._autosave_fail_count += 1
            _log.warning("Autosave failed (attempt %d): file may be locked by another program",
                         self._autosave_fail_count)
            self._update_save_indicator("Autosave failed — file locked")
            self._check_autosave_failures()
        except OSError as e:
            self._autosave_fail_count += 1
            _log.warning("Autosave failed (attempt %d): %s", self._autosave_fail_count, e)
            self._update_save_indicator("Autosave failed")
            self._check_autosave_failures()

    def _check_autosave_failures(self) -> None:
        """Show a persistent warning if autosave has failed too many times."""
        if self._autosave_fail_count >= self._MAX_AUTOSAVE_FAILURES:
            messagebox.showwarning(
                "Autosave Problem",
                f"Autosave has failed {self._autosave_fail_count} times in a row.\n\n"
                "Possible causes:\n"
                "• The workbook is open in Excel\n"
                "• The file is locked by OneDrive sync\n"
                "• Disk is full or read-only\n\n"
                "Your changes are preserved in memory. Try saving manually\n"
                "(Ctrl+S) or close other programs using the file.",
                parent=self,
            )
            self._autosave_fail_count = 0  # Reset to avoid repeated popups

    def _update_save_indicator(self, text: str) -> None:
        """Update the status bar save indicator text."""
        color = "#27ae60" if "Save" in text and "error" not in text.lower() and "fail" not in text.lower() else "gray"
        if "Unsaved" in text:
            color = "#e67e22"
        self._save_indicator.configure(text=text, text_color=color)

    def notify(self, title: str, message: str, level: str = "info") -> None:
        if level == "error":
            messagebox.showerror(title, message, parent=self)
        elif level == "warn":
            messagebox.showwarning(title, message, parent=self)
        else:
            messagebox.showinfo(title, message, parent=self)

    # ═══════════════════════════════════════════════════════════════════════
    #  KEYBINDINGS
    # ═══════════════════════════════════════════════════════════════════════
    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.show_page("add_task"))
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-g>", lambda e: self._trigger_generate())
        self.bind("<Delete>",    lambda e: self._trigger_delete())
        self.bind("<Control-s>", lambda e: self._trigger_save())
        self.bind("<Control-d>", lambda e: self.show_page("dashboard"))
        # Mid-session external edit detection on window focus
        self.bind("<FocusIn>", self._on_focus_in)

    def _focus_search(self):
        self.show_page("tasks")
        tasks_page = self.pages.get("tasks")
        if tasks_page and hasattr(tasks_page, "focus_search"):
            tasks_page.focus_search()

    def _trigger_generate(self):
        self.show_page("generate")
        gen = self.pages.get("generate")
        if gen and hasattr(gen, "_generate_reports"):
            gen._generate_reports()

    def _trigger_delete(self):
        tasks_page = self.pages.get("tasks")
        if tasks_page and hasattr(tasks_page, "_delete_selected_task"):
            tasks_page._delete_selected_task()

    def _trigger_save(self):
        gen = self.pages.get("generate")
        if gen and hasattr(gen, "_save_workbook"):
            gen._save_workbook()

    # ═══════════════════════════════════════════════════════════════════════
    #  MID-SESSION EXTERNAL EDIT DETECTION
    # ═══════════════════════════════════════════════════════════════════════
    _EDIT_CHECK_INTERVAL: float = 5.0  # seconds between external edit checks

    def _on_focus_in(self, event=None) -> None:
        """Called when the window regains focus — check for external edits."""
        # Only fire for the root window, not every child widget
        if event and event.widget is not self:
            return
        now = time.monotonic()
        if now - self._last_edit_check < self._EDIT_CHECK_INTERVAL:
            return  # Skip — checked recently
        self._last_edit_check = now
        self._check_external_edits()

    def _check_external_edits(self) -> None:
        """Detect external workbook modifications and prompt the user.

        Triggered on: window focus, tab/page change, save, generate.
        Uses hash-based comparison so it is immune to OneDrive mtime bumps.
        """
        if not self._profile_is_configured():
            return

        wb_path = workbook_path()
        if not wb_path.exists():
            return

        try:
            changed = detect_external_edits(_prof.USER_COMPANY, wb_path)
        except Exception:
            return  # Silently ignore hash errors

        if not changed:
            return

        answer = messagebox.askyesno(
            "External Edit Detected",
            "The workbook has been modified outside the application.\n\n"
            "Reload data from the workbook?\n\n"
            "Yes = import external changes (overwrites in-memory state)\n"
            "No = keep current state (will overwrite external changes on next save)",
            parent=self,
        )
        if answer:
            self.reload_data()
            self._update_save_indicator("Reloaded external changes")
        else:
            # User chose to keep current state — update the stored hash so
            # we don't keep prompting until the next genuine external edit.
            if self.profile and self.wb:
                save_profile_dual(self.profile, self.wb, wb_path=wb_path)
                self._update_save_indicator("External changes ignored")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
