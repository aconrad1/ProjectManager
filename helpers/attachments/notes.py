"""Task notes (activity log) — CRUD backed by a JSON file.

Notes are keyed by **task_id** (e.g. ``T-001``).  Legacy data keyed by
task title is migrated automatically via :func:`migrate_notes`.
"""

from __future__ import annotations

from datetime import datetime

from helpers.io.json_store import load_json, save_json
from helpers.profile.config import notes_file


def load_notes() -> dict[str, list[dict]]:
    """Return ``{task_id: [{timestamp, text}, …]}``."""
    return load_json(notes_file(), default={})


def save_notes(notes: dict[str, list[dict]]) -> None:
    save_json(notes_file(), notes)


def add_note(task_id: str, text: str) -> None:
    """Append a timestamped note for *task_id*."""
    notes = load_notes()
    notes.setdefault(task_id, []).append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text,
    })
    save_notes(notes)


def list_notes(task_id: str) -> list[dict]:
    """Return notes for *task_id* (newest first)."""
    return list(reversed(load_notes().get(task_id, [])))


def delete_notes(task_id: str) -> None:
    """Remove all notes for *task_id*."""
    notes = load_notes()
    if task_id in notes:
        del notes[task_id]
        save_notes(notes)


def migrate_notes(title_to_id: dict[str, str]) -> int:
    """Re-key legacy title-based entries to task IDs.

    *title_to_id* maps ``{task_title: task_id}``.  Returns the number of
    entries migrated.  Entries already keyed by a valid ID (``T-\\d{3,}``)
    are left untouched.
    """
    from helpers.attachments.migration import migrate_dict_store

    def _merge_lists(
        target: dict[str, list[dict]], key: str, value: list[dict]
    ) -> None:
        target.setdefault(key, []).extend(value)

    return migrate_dict_store(load_notes, save_notes, title_to_id, merge_fn=_merge_lists)
