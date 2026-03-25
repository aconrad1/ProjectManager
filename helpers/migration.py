"""One-time migration utilities for title-based → ID-based keying.

Called automatically on profile load when legacy (title-keyed) data is
detected.  Safe to run multiple times — already-migrated entries are
skipped.
"""

from __future__ import annotations

import logging
from helpers.domain.profile import Profile
from helpers.attachments.notes import migrate_notes
from helpers.attachments.links import migrate_links
from helpers.attachments.service import migrate_attachments

log = logging.getLogger(__name__)


def build_title_to_id_map(profile: Profile) -> dict[str, str]:
    """Return ``{task_title: task_id}`` for every task in *profile*.

    If two tasks share the same title, the **first** encountered wins
    (consistent with the legacy title-keyed behaviour).
    """
    mapping: dict[str, str] = {}
    for task in profile.all_tasks:
        if task.title and task.title not in mapping:
            mapping[task.title] = task.id
    return mapping


def migrate_to_id_keying(profile: Profile) -> None:
    """Migrate notes, links, and attachments from title-based to ID-based keys.

    This is safe to call on every load — each sub-migration is a no-op when
    all entries are already keyed by valid IDs.
    """
    title_to_id = build_title_to_id_map(profile)
    if not title_to_id:
        return

    n = migrate_notes(title_to_id)
    l = migrate_links(title_to_id)
    a = migrate_attachments(title_to_id)

    total = n + l + a
    if total:
        log.info("ID-keying migration: %d notes, %d links, %d attachment dirs migrated", n, l, a)
