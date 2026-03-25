"""
Dashboard page — stat cards, priority breakdown, recent completions,
site distribution, and priority spotlight.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

import customtkinter as ctk

from gui.base_page import BasePage
from gui.ui_theme import AG_DARK, AG_MID, AG_WASH
from helpers.profile.config import pdf_dir, markdown_dir
from helpers.io.files import find_latest, open_path


class DashboardPage(BasePage):
    KEY = "dashboard"
    TITLE = "Dashboard"

    def build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        ctk.CTkLabel(top, text="Dashboard", font=("Segoe UI", 18, "bold"),
                     text_color=AG_DARK).pack(side="left")
        ctk.CTkButton(top, text="Open Latest Report", width=160, fg_color=AG_MID,
                      command=self._open_latest).pack(side="right", padx=(8, 0))
        ctk.CTkButton(top, text="Refresh", width=100, fg_color="gray",
                      hover_color="darkgray",
                      command=self.refresh).pack(side="right")

        # ── Dashboard content (scrollable) ─────────────────────────────────
        self._dash_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._dash_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Stat cards row
        self._dash_cards_frame = ctk.CTkFrame(self._dash_scroll, fg_color="transparent")
        self._dash_cards_frame.pack(fill="x", pady=(0, 10))

        # Priority breakdown section
        self._dash_priority_frame = ctk.CTkFrame(self._dash_scroll, fg_color="transparent")
        self._dash_priority_frame.pack(fill="x", pady=(0, 10))

        # Completed this week section
        self._dash_recent_frame = ctk.CTkFrame(self._dash_scroll, fg_color="transparent")
        self._dash_recent_frame.pack(fill="x", pady=(0, 10))

        # Site distribution section
        self._dash_site_frame = ctk.CTkFrame(self._dash_scroll, fg_color="transparent")
        self._dash_site_frame.pack(fill="x", pady=(0, 10))

        # Top priorities section
        self._dash_top_frame = ctk.CTkFrame(self._dash_scroll, fg_color="transparent")
        self._dash_top_frame.pack(fill="x", pady=(0, 10))

    # ── public ─────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        profile = self.app.profile
        if not profile:
            return

        weekly = profile.tasks_for_category("Weekly")
        ongoing = profile.tasks_for_category("Ongoing")
        completed = profile.tasks_for_category("Completed")
        all_active = weekly + ongoing
        today = date.today()
        week_ago = today - timedelta(days=7)
        thirty_ago = today - timedelta(days=30)

        # ── Stat cards ─────────────────────────────────────────────────────
        for w in self._dash_cards_frame.winfo_children():
            w.destroy()

        stats = [
            ("Weekly Tasks", len(weekly), AG_DARK),
            ("Ongoing Projects", len(ongoing), AG_MID),
            ("Completed", len(completed), "#27ae60"),
            ("Total Active", len(all_active), "#2c3e50"),
        ]
        for i, (label, count, color) in enumerate(stats):
            card = ctk.CTkFrame(self._dash_cards_frame, corner_radius=8,
                                fg_color=color, width=200, height=90)
            card.pack(side="left", expand=True, fill="x", padx=(0 if i == 0 else 8, 0))
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=str(count), font=("Segoe UI", 28, "bold"),
                         text_color="white").pack(pady=(12, 0))
            ctk.CTkLabel(card, text=label, font=("Segoe UI", 11),
                         text_color="white").pack()

        # ── Priority breakdown ─────────────────────────────────────────────
        for w in self._dash_priority_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._dash_priority_frame, text="Priority Breakdown",
                     font=("Segoe UI", 14, "bold"), text_color=AG_DARK).pack(anchor="w", pady=(4, 6))

        prio_counts = Counter(t.priority for t in all_active)
        total_active = len(all_active) or 1
        prio_colors = {1: "#c0392b", 2: "#e67e22", 3: "#f39c12", 4: "#7f8c8d", 5: "#bdc3c7"}
        prio_names = {1: "P1 Urgent", 2: "P2 High", 3: "P3 Medium", 4: "P4 Low", 5: "P5 Background"}

        for p in range(1, 6):
            count = prio_counts.get(p, 0)
            pct = count / total_active
            row = ctk.CTkFrame(self._dash_priority_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=prio_names[p], font=("Segoe UI", 10),
                         width=110, anchor="e").pack(side="left", padx=(0, 8))
            bar_bg = ctk.CTkFrame(row, fg_color="#e0e0e0", height=18, corner_radius=4)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(0, 8))
            bar_bg.pack_propagate(False)
            if pct > 0:
                bar_fill = ctk.CTkFrame(bar_bg, fg_color=prio_colors[p],
                                        corner_radius=4)
                bar_fill.place(relwidth=max(pct, 0.02), relheight=1.0)
            ctk.CTkLabel(row, text=f"{count} ({pct:.0%})", font=("Segoe UI", 10),
                         width=70).pack(side="left")

        # ── Completed this week ────────────────────────────────────────────
        for w in self._dash_recent_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._dash_recent_frame, text="Recently Completed",
                     font=("Segoe UI", 14, "bold"), text_color=AG_DARK).pack(anchor="w", pady=(8, 6))

        recent_completed = [
            t for t in completed
            if t.date_completed and t.date_completed >= week_ago
        ]
        if recent_completed:
            for t in recent_completed:
                row = ctk.CTkFrame(self._dash_recent_frame, fg_color=AG_WASH,
                                   corner_radius=6)
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"  {t.title}", font=("Segoe UI", 11, "bold"),
                             anchor="w").pack(side="left", padx=8, pady=4)
                date_str = t.date_completed.strftime("%b %d") if t.date_completed else ""
                ctk.CTkLabel(row, text=date_str, font=("Segoe UI", 10),
                             text_color="gray").pack(side="right", padx=8, pady=4)
        else:
            ctk.CTkLabel(self._dash_recent_frame, text="  No tasks completed in the last 7 days.",
                         font=("Segoe UI", 10), text_color="gray").pack(anchor="w")

        month_completed = [t for t in completed
                           if t.date_completed and t.date_completed >= thirty_ago]
        ctk.CTkLabel(self._dash_recent_frame,
                     text=f"  Last 30 days: {len(month_completed)} completed",
                     font=("Segoe UI", 10), text_color="gray").pack(anchor="w", pady=(4, 0))

        # ── Site distribution ──────────────────────────────────────────────
        for w in self._dash_site_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._dash_site_frame, text="Site Distribution",
                     font=("Segoe UI", 14, "bold"), text_color=AG_DARK).pack(anchor="w", pady=(8, 6))

        site_counts: Counter = Counter()
        for t in all_active:
            sites = [s.strip() for s in t.site.replace("&", ",").split(",") if s.strip()]
            if not sites or sites == ["N/A"]:
                sites = ["Unassigned"]
            for s in sites:
                site_counts[s] += 1

        if site_counts:
            site_total = sum(site_counts.values()) or 1
            site_colors = ["#003DA5", "#336BBF", "#2980b9", "#16a085", "#27ae60",
                           "#8e44ad", "#d35400", "#c0392b"]
            for i, (site, cnt) in enumerate(site_counts.most_common(8)):
                pct = cnt / site_total
                row = ctk.CTkFrame(self._dash_site_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=site, font=("Segoe UI", 10),
                             width=160, anchor="e").pack(side="left", padx=(0, 8))
                bar_bg = ctk.CTkFrame(row, fg_color="#e0e0e0", height=18, corner_radius=4)
                bar_bg.pack(side="left", fill="x", expand=True, padx=(0, 8))
                bar_bg.pack_propagate(False)
                if pct > 0:
                    color = site_colors[i % len(site_colors)]
                    bar_fill = ctk.CTkFrame(bar_bg, fg_color=color, corner_radius=4)
                    bar_fill.place(relwidth=max(pct, 0.02), relheight=1.0)
                ctk.CTkLabel(row, text=f"{cnt} ({pct:.0%})", font=("Segoe UI", 10),
                             width=70).pack(side="left")
        else:
            ctk.CTkLabel(self._dash_site_frame, text="  No site data available.",
                         font=("Segoe UI", 10), text_color="gray").pack(anchor="w")

        # ── Top priority tasks (P1 & P2) ───────────────────────────────────
        for w in self._dash_top_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._dash_top_frame, text="Priority Spotlight",
                     font=("Segoe UI", 14, "bold"), text_color=AG_DARK).pack(anchor="w", pady=(8, 6))

        spotlight = sorted([t for t in all_active if t.priority <= 2],
                           key=lambda t: t.priority)[:6]
        if spotlight:
            for t in spotlight:
                pcolor = "#c0392b" if t.priority == 1 else "#e67e22"
                row = ctk.CTkFrame(self._dash_top_frame, fg_color="white",
                                   corner_radius=6, border_width=1, border_color=pcolor)
                row.pack(fill="x", pady=2)
                badge = ctk.CTkLabel(row, text=f"P{t.priority}", font=("Segoe UI", 10, "bold"),
                                     text_color="white", fg_color=pcolor,
                                     corner_radius=4, width=30)
                badge.pack(side="left", padx=(6, 4), pady=4)
                ctk.CTkLabel(row, text=t.title, font=("Segoe UI", 11, "bold"),
                             anchor="w").pack(side="left", padx=4, pady=4)
                ctk.CTkLabel(row, text=f"{t.status}  |  {t.site}",
                             font=("Segoe UI", 10), text_color="gray").pack(side="right", padx=8, pady=4)
        else:
            ctk.CTkLabel(self._dash_top_frame,
                         text="  No urgent or high-priority tasks. Nice!",
                         font=("Segoe UI", 10), text_color="gray").pack(anchor="w")

    # ── internal ───────────────────────────────────────────────────────────
    def _open_latest(self):
        target = find_latest(pdf_dir(), "*.pdf") or find_latest(markdown_dir(), "*.md")
        if target:
            open_path(target)
        else:
            from tkinter import messagebox
            messagebox.showinfo("No Reports", "No reports found. Generate one first.")
