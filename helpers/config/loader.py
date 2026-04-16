"""Config loader — reads and caches JSON config files.

All JSON config files live alongside this module in ``helpers/config/``.
``load(name)`` returns the parsed JSON, cached after first read.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

_CONFIG_DIR = Path(__file__).resolve().parent

DEFAULT_DEADLINE_WINDOWS = {
    "recent_completed_days": 7,
    "extended_completed_days": 30,
    "upcoming_deadline_days": 14,
    "snapshot_lookback_days": 7,
}


@lru_cache(maxsize=32)
def load(name: str) -> Any:
    """Load and cache a JSON config file by name (without extension).

    Example::

        from helpers.config import load
        statuses = load("status")["values"]
    """
    path = _CONFIG_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_field_map(entity: str) -> dict[str, str]:
    """Return ``{gui_label: domain_attribute}`` for *entity* (task | deliverable | project)."""
    fields = load("fields")
    return fields.get(entity, {})


def load_reverse_field_map(entity: str) -> dict[str, str]:
    """Return ``{domain_attribute: gui_label}`` for *entity*."""
    return {v: k for k, v in load_field_map(entity).items()}


# ── Dimension-table accessors (cached at first call) ─────────────────────────

def _status_records() -> list[dict]:
    return load("status")["values"]


def _category_records() -> list[dict]:
    return load("categories")["values"]


def _priority_records() -> list[dict]:
    return load("priorities")["values"]


# -- Status helpers --

def valid_statuses() -> set[str]:
    """All recognised status names."""
    return {s["name"] for s in _status_records()}


def default_status() -> str:
    """The default status for newly created items (first non-terminal status)."""
    for s in _status_records():
        if not s.get("is_terminal"):
            return s["name"]
    return _status_records()[0]["name"]


def terminal_statuses() -> set[str]:
    """Statuses that mark an item as finished (e.g. 'Completed')."""
    return {s["name"] for s in _status_records() if s.get("is_terminal")}


def active_statuses() -> set[str]:
    """Statuses that indicate ongoing work."""
    return {s["name"] for s in _status_records() if s.get("tier") == "active"}


def reopen_status() -> str:
    """The status to assign when reopening a completed item (first active status)."""
    for s in _status_records():
        if s.get("tier") == "active":
            return s["name"]
    return default_status()


def excluded_statuses() -> frozenset[str]:
    """Case-folded statuses excluded from scheduling (terminal + inactive non-default)."""
    return frozenset(
        s["name"].lower() for s in _status_records()
        if s.get("is_terminal") or s.get("tier") == "inactive" and s["name"] != default_status()
    )


def completion_aliases() -> set[str]:
    """Case-folded keywords that should be treated as completed."""
    aliases: set[str] = set()
    for s in _status_records():
        if s.get("is_terminal"):
            aliases.add(s["name"].lower())
            for a in s.get("completion_aliases", []):
                aliases.add(a.lower())
    return aliases


def status_color(name: str) -> str:
    """Hex colour string for a given status name (exact or case-insensitive)."""
    for s in _status_records():
        if s["name"] == name:
            return s["color"]
    key = name.strip().lower()
    for s in _status_records():
        if s["name"].lower() == key:
            return s["color"]
    return "#95a5a6"


def status_bg_color(name: str) -> str:
    """Background colour for a given status (case-insensitive lookup)."""
    key = name.strip().lower()
    for s in _status_records():
        if s["name"].lower() == key:
            return s["bg_color"]
    return "#F2F3F4"


def status_gantt_color(name: str) -> str:
    """Gantt chart colour for a given status (case-insensitive lookup)."""
    key = name.strip().lower()
    for s in _status_records():
        if s["name"].lower() == key:
            return s["gantt_color"]
    return "#B0B0B0"


# -- Category helpers --

def valid_categories() -> tuple[str, ...]:
    """All recognised categories as a tuple (preserves order)."""
    return tuple(c["name"] for c in _category_records())


def terminal_categories() -> set[str]:
    """Categories that mark an item as finished."""
    return {c["name"] for c in _category_records() if c.get("is_terminal")}


def active_categories() -> set[str]:
    """Non-terminal categories (e.g. Weekly, Ongoing)."""
    return {c["name"] for c in _category_records() if not c.get("is_terminal")}


def default_category() -> str:
    """The default category for newly created projects."""
    for c in _category_records():
        if c.get("default_for_new"):
            return c["name"]
    return _category_records()[0]["name"]


# -- Priority helpers --

def priority_range() -> tuple[int, int]:
    """(min, max) inclusive priority range."""
    cfg = load("priorities")
    return tuple(cfg["range"])  # type: ignore[return-value]


def default_priority() -> int:
    """Default priority for new items."""
    return load("priorities")["default"]


def priority_labels() -> dict[int, str]:
    """``{1: 'P1 - Urgent', ...}`` mapping."""
    return {p["value"]: p["label"] for p in _priority_records()}


def priority_tiers() -> dict[str, set[int]]:
    """``{'urgent': {1}, 'high': {2}, ...}`` mapping."""
    tiers: dict[str, set[int]] = {}
    for p in _priority_records():
        tiers.setdefault(p["tier"], set()).add(p["value"])
    return tiers


def priority_badge_class(value: int) -> str:
    """CSS badge class name for a priority value."""
    for p in _priority_records():
        if p["value"] == value:
            return p.get("badge_class", "bg")
    return "bg"


def priority_badge_label(value: int) -> str:
    """Display label for priority badge (e.g. 'P1 Urgent')."""
    for p in _priority_records():
        if p["value"] == value:
            # Badge labels strip the dash: "P1 - Urgent" → "P1 Urgent"
            return p["label"].replace(" - ", " ")
    return f"P{value}"


def load_deadline_windows(
    *,
    log: Callable[[str], None] | None = None,
    auto_repair: bool = True,
) -> dict[str, int]:
    """Load deadline/report windows with validation and optional self-healing.

    Returns a fully-populated dict containing all expected keys. If
    ``deadlines.json`` is missing or malformed, defaults are used and the file
    is rewritten when ``auto_repair`` is enabled.
    """
    path = _CONFIG_DIR / "deadlines.json"

    if not path.exists():
        if log:
            log("   ⚠ Config 'deadlines.json' is missing. Using defaults and recreating the file.")
        if auto_repair:
            path.write_text(json.dumps(DEFAULT_DEADLINE_WINDOWS, indent=4) + "\n", encoding="utf-8")
            load.cache_clear()
        return dict(DEFAULT_DEADLINE_WINDOWS)

    raw: Any
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        if log:
            log("   ⚠ Config 'deadlines.json' is invalid JSON. Using defaults and repairing the file.")
        if auto_repair:
            path.write_text(json.dumps(DEFAULT_DEADLINE_WINDOWS, indent=4) + "\n", encoding="utf-8")
            load.cache_clear()
        return dict(DEFAULT_DEADLINE_WINDOWS)

    cfg = raw if isinstance(raw, dict) else {}
    windows: dict[str, int] = {}
    repaired = False

    for key, default in DEFAULT_DEADLINE_WINDOWS.items():
        val = cfg.get(key)
        if isinstance(val, bool):
            val = None
        if isinstance(val, (int, float)):
            n = int(val)
            if n > 0:
                windows[key] = n
                continue
        windows[key] = default
        repaired = True

    if repaired and log:
        log("   ⚠ Config 'deadlines.json' had missing/invalid values. Defaults were applied.")

    if repaired and auto_repair:
        path.write_text(json.dumps(windows, indent=4) + "\n", encoding="utf-8")
        load.cache_clear()

    return windows
