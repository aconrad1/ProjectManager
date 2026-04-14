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
    except Exception:
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
