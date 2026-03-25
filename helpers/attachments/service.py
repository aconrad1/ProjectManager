"""Attachment service — copy files to per-task folders and open them.

Attachment directories are keyed by **task_id** (e.g. ``T-001``).
Legacy directories named by task title are migrated via
:func:`migrate_attachments`.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from helpers.profile.config import attachments_dir
from helpers.io.files import safe_filename, open_path

_ID_RE = re.compile(r"^[A-Z]-\d{3,}$")


def task_attachment_dir(task_id: str) -> Path:
    """Return the attachment directory for *task_id*."""
    return attachments_dir() / task_id


def attach_files(task_id: str, sources: list[str | Path]) -> list[str]:
    """Copy *sources* into the task's attachment dir. Returns filenames copied."""
    dest = task_attachment_dir(task_id)
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for src in sources:
        src_path = Path(src)
        shutil.copy2(str(src_path), str(dest / src_path.name))
        copied.append(src_path.name)
    return copied


def list_attachments(task_id: str) -> list[Path]:
    """Return all files in the task's attachment directory."""
    d = task_attachment_dir(task_id)
    if d.exists():
        return [p for p in d.iterdir() if p.is_file()]
    return []


def open_attachments_folder(task_id: str) -> bool:
    """Open the attachment folder in the platform file manager."""
    d = task_attachment_dir(task_id)
    if d.exists() and any(d.iterdir()):
        open_path(d)
        return True
    return False


def delete_attachments(task_id: str) -> None:
    """Remove the entire attachment folder for *task_id*."""
    d = task_attachment_dir(task_id)
    if d.exists():
        shutil.rmtree(str(d))


def migrate_attachments(title_to_id: dict[str, str]) -> int:
    """Rename legacy title-based attachment directories to task IDs.

    Returns the number of directories migrated.
    """
    base = attachments_dir()
    if not base.exists():
        return 0
    migrated = 0
    for old_dir in list(base.iterdir()):
        if not old_dir.is_dir():
            continue
        dirname = old_dir.name
        if _ID_RE.match(dirname):
            continue  # already migrated
        # Try to find title that produced this safe_filename
        for title, tid in title_to_id.items():
            if safe_filename(title) == dirname:
                new_dir = base / tid
                if not new_dir.exists():
                    old_dir.rename(new_dir)
                    migrated += 1
                break
    return migrated
