"""Linked-folder mappings — associates tasks with project folder paths.

Links are keyed by **task_id** (e.g. ``T-001``).  Legacy data keyed by
task title is migrated automatically via :func:`migrate_links`.
"""

from __future__ import annotations

from pathlib import Path

from helpers.io.json_store import load_json, save_json
from helpers.profile.config import links_file
from helpers.io.files import open_path


def load_links() -> dict[str, str]:
    """Return ``{task_id: folder_path}``."""
    return load_json(links_file(), default={})


def save_links(links: dict[str, str]) -> None:
    save_json(links_file(), links)


def get_link(task_id: str) -> str | None:
    return load_links().get(task_id)


def set_link(task_id: str, folder: str) -> None:
    links = load_links()
    links[task_id] = folder
    save_links(links)


def delete_link(task_id: str) -> None:
    links = load_links()
    if task_id in links:
        del links[task_id]
        save_links(links)


def open_linked_folder(task_id: str) -> bool:
    """Open the linked folder if it exists. Returns True on success."""
    folder = get_link(task_id)
    if folder and Path(folder).exists():
        open_path(folder)
        return True
    return False


def migrate_links(title_to_id: dict[str, str]) -> int:
    """Re-key legacy title-based entries to task IDs.

    Returns the number of entries migrated.
    """
    from helpers.attachments.migration import migrate_dict_store
    return migrate_dict_store(load_links, save_links, title_to_id)
