"""
Generate page — report generation buttons and output log.
"""
from __future__ import annotations

import threading
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import AG_DARK, AG_MID
from helpers.profile.config import workbook_path, pdf_dir, markdown_dir
from helpers.io.files import find_latest, open_path


class GeneratePage(BasePage):
    KEY = "generate"
    TITLE = "Generate"

    def build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._gen_event = threading.Event()  # set = generation in progress

        ctk.CTkLabel(self, text="Report Generation", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 10))

        # ── Action buttons ─────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        buttons = [
            ("Save Workbook",       self._save_workbook,    AG_MID,     160),
            ("Generate Reports",    self._generate_reports, AG_DARK,    180),
            ("Save & Close",        self._save_and_close,   "#2c3e50",  160),
            ("Open Latest Report",  self._open_latest,      "#27ae60",  180),
            ("Email Report",        self._email_report,     "#8e44ad",  160),
        ]
        for text, cmd, color, width in buttons:
            ctk.CTkButton(
                btn_frame, text=text, width=width, height=42,
                font=("Segoe UI", 13, "bold"), fg_color=color,
                command=cmd,
            ).pack(side="left", padx=(0, 8), pady=4)

        # ── Output log ─────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Output Log", font=("Segoe UI", 12, "bold"),
                     text_color=AG_DARK).grid(row=2, column=0, sticky="nw", padx=20, pady=(4, 0))
        self._log = ctk.CTkTextbox(self, font=("Consolas", 11), state="disabled")
        self._log.grid(row=3, column=0, sticky="nsew", padx=20, pady=(4, 16))
        self.grid_rowconfigure(3, weight=1)

    # ── logging helpers ────────────────────────────────────────────────────
    def log_write(self, text: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _log_after(self, text: str):
        """Thread-safe logging via after()."""
        self.after(0, lambda: self.log_write(text))

    # ── Save ───────────────────────────────────────────────────────────────
    def _save_workbook(self):
        try:
            self.app.save_state()
            from helpers.commands.utilities import save_workbook_cmd
            save_workbook_cmd(self.app.wb, log=self.log_write)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ── Generate ───────────────────────────────────────────────────────────
    def _generate_reports(self):
        if self._gen_event.is_set():
            return
        self._gen_event.set()
        self._log_clear()
        self.log_write("Starting report generation…\n")

        def run():
            try:
                from helpers.commands.report_pipeline import generate_reports
                result = generate_reports(log=self._log_after, today=date.today())
                # Marshal ALL state updates to the main thread
                self.after(0, lambda: self._apply_generation_result(result))
            except Exception as e:
                self._log_after(f"\nERROR: {e}")
                self.after(0, lambda: self._on_generation_failed(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _apply_generation_result(self, result: dict) -> None:
        """Apply generation results on the main thread."""
        self.app.wb = result["wb"]
        if "profile" in result:
            self.app.profile = result["profile"]
        tasks_page = self.app.pages.get("tasks")
        if tasks_page:
            tasks_page.refresh()
        self._gen_event.clear()
        messagebox.showinfo("Complete", "Reports generated successfully!")

    def _on_generation_failed(self, error_msg: str) -> None:
        """Handle generation failure on the main thread."""
        self._gen_event.clear()
        messagebox.showerror("Generation Failed", error_msg)

    # ── Save & Close ───────────────────────────────────────────────────────
    def _save_and_close(self):
        try:
            self.app.save_state()
            self.app.wb.save(str(workbook_path()))
            self.log_write("Workbook saved.")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
            return
        self.winfo_toplevel().destroy()

    # ── Open latest ────────────────────────────────────────────────────────
    def _open_latest(self):
        target = find_latest(pdf_dir(), "*.pdf") or find_latest(markdown_dir(), "*.md")
        if target:
            open_path(target)
        else:
            messagebox.showinfo("No Reports", "No reports found. Generate one first.")

    # ── Email ──────────────────────────────────────────────────────────────
    def _email_report(self):
        try:
            from helpers.commands.utilities import email_report
            email_report(log=self.log_write)
        except FileNotFoundError as e:
            messagebox.showinfo("No PDF", str(e))
        except Exception as e:
            messagebox.showerror("Email Error", str(e))
