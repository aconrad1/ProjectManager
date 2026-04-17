"""Generic key migration for title-based → ID-based stores."""

from __future__ import annotations

import re
from typing import Any, Callable, TypeVar

_ID_RE = re.compile(r"^[A-Z]-\d{3,}$")

T = TypeVar("T")


def migrate_dict_store(
    load_fn: Callable[[], dict[str, T]],
    save_fn: Callable[[dict[str, T]], None],
    title_to_id: dict[str, str],
    *,
    merge_fn: Callable[[dict[str, T], str, T], None] | None = None,
) -> int:
    """Migrate a dict-based store from title keys to ID keys.

    Args:
        load_fn: Function that returns the current store contents.
        save_fn: Function that persists the migrated store.
        title_to_id: Mapping of {task_title: task_id}.
        merge_fn: Optional function to handle merging values into the new dict.
                  Signature: ``merge_fn(new_store, key, value)``.
                  Default behavior: ``new_store[key] = value``.

    Returns:
        Number of entries migrated.
    """
    store = load_fn()
    migrated = 0
    new_store: dict[str, T] = {}

    def _default_merge(target: dict[str, T], key: str, value: T) -> None:
        target[key] = value

    do_merge = merge_fn or _default_merge

    for key, value in store.items():
        if _ID_RE.match(key):
            do_merge(new_store, key, value)
        elif key in title_to_id:
            do_merge(new_store, title_to_id[key], value)
            migrated += 1
        else:
            do_merge(new_store, key, value)

    if migrated:
        save_fn(new_store)
    return migrated
