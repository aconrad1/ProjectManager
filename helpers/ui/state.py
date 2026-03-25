"""Persistent UI state — saves and restores filter, search, and expansion state.

Stores a per-profile ``ui_state.json`` inside the profile's ``data/`` directory
so that filter selections, search text, treeview expansion state, and other
transient UI preferences survive across sessions.

Usage::

    from helpers.ui.state import load_ui_state, save_ui_state

    state = load_ui_state()           # returns dict (empty on first run)
    state["tasks_filter"] = "Ongoing"
    save_ui_state(state)
"""

from __future__ import annotations

from pathlib import Path

from helpers.io.json_store import load_json, save_json
from helpers.profile.config import data_dir

_FILENAME = "ui_state.json"


def _state_path() -> Path:
    return data_dir() / _FILENAME


def load_ui_state() -> dict:
    """Load the persisted UI state for the active profile."""
    return load_json(_state_path(), default={})


def save_ui_state(state: dict) -> None:
    """Persist the UI state for the active profile."""
    save_json(_state_path(), state)
