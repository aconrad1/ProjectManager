"""
Shared UI theme — colors, fonts, and constants for the GUI.

Brand colours and fonts are defined here.  Data-driven constants
(priority labels, status options, categories) are loaded from
``helpers/config/*.json`` — do NOT hard-code them here.
"""
from __future__ import annotations

from helpers.config import load as _load_cfg

# ── Load config-driven constants ───────────────────────────────────────────────
_theme       = _load_cfg("theme")
_status_cfg  = _load_cfg("status")
_cat_cfg     = _load_cfg("categories")

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

# ── Priority / Status / Category constants (config-driven) ────────────────────
PRIORITY_LABELS: dict[int, str] = {
    int(k): v for k, v in _theme["priority_labels"].items()
}

PRIORITY_COLORS: dict[int, str] = {
    int(k): v for k, v in _theme["priority_colors"].items()
}

STATUS_OPTIONS: list[str] = _status_cfg["values"]

STATUS_COLORS: dict[str, str] = _theme.get("status_colors", {})

CATEGORIES: list[str] = _cat_cfg["values"]

TREEVIEW_TAG_COLORS: dict[str, str] = _theme.get("treeview_tag_colors", {})
