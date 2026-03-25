"""Config loader — reads and caches JSON config files.

All JSON config files live alongside this module in ``helpers/config/``.
``load(name)`` returns the parsed JSON, cached after first read.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(__file__).resolve().parent


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
