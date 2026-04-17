"""
Shared UI theme — colors, fonts, and constants for the GUI.

Brand colours and fonts are defined here.  Data-driven constants
(priority labels, status options, categories) are loaded from
``helpers/config/*.json`` — do NOT hard-code them here.
"""
from __future__ import annotations

from helpers.config import load as _load_cfg
from helpers.config.loader import (
    priority_labels as _load_priority_labels,
    valid_statuses as _load_valid_statuses,
    valid_categories as _load_valid_categories,
    status_color as _status_color,
    status_bg_color as _status_bg_color,
)

# ── Load config-driven constants ───────────────────────────────────────────────
_theme       = _load_cfg("theme")
_prio_cfg    = _load_cfg("priorities")

# ── AltaGas Brand Colors ──────────────────────────────────────────────────────
AG_DARK  = _theme["brand"]["dark"]
AG_MID   = _theme["brand"]["mid"]
AG_LIGHT = _theme["brand"]["light"]
AG_WASH  = _theme["brand"]["wash"]

# ── Fonts ──────────────────────────────────────────────────────────────────────
FONT_H1   = ("Segoe UI", 18, "bold")
FONT_H2   = ("Segoe UI", 14, "bold")
FONT_H3   = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_NAV  = ("Segoe UI", 13)
FONT_BTN  = ("Segoe UI", 13, "bold")
FONT_LOG  = ("Consolas", 11)

# ── Priority / Status / Category constants (dimension-table driven) ───────────
PRIORITY_LABELS: dict[int, str] = _load_priority_labels()

PRIORITY_COLORS: dict[int, str] = {
    p["value"]: p["color"] for p in _prio_cfg["values"]
}

STATUS_OPTIONS: list[str] = list(_load_valid_statuses())

STATUS_COLORS: dict[str, str] = {
    name: _status_color(name) for name in _load_valid_statuses()
}

CATEGORIES: list[str] = list(_load_valid_categories())

TREEVIEW_TAG_COLORS: dict[str, str] = _theme.get("treeview_tag_colors", {})

SITE_PALETTE: list[str] = _theme.get("site_palette", [
    "#003DA5", "#336BBF", "#2980b9", "#16a085",
    "#27ae60", "#8e44ad", "#d35400", "#c0392b",
])

STATUS_BG_COLORS: dict[str, str] = {
    name.lower(): _status_bg_color(name) for name in _load_valid_statuses()
}

GANTT_COLORS_DARK: dict[str, str] = _theme.get("gantt_colors_dark", {})
