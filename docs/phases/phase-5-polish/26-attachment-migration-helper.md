# Task 26: Extract Attachment Migration into Generic Helper

**Audit ID**: M-04  
**Effort**: Small  
**Phase**: 5 — Polish

---

## Objective

Extract the duplicated migration pattern from `notes.py`, `links.py`, and `service.py` into a generic `migrate_keyed_store()` function. Each module's `migrate_*()` function calls the generic helper.

---

## Audit Reference

> **M-04: Attachment Migration Logic Nearly Identical in 3 Files**
>
> Each `migrate_*()` function: loads data → checks if keys match ID regex → remaps title keys to ID keys → saves.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/attachments/migration.py` | **CREATE** — generic migration helper |
| `helpers/attachments/notes.py` | **MODIFY** — use generic helper |
| `helpers/attachments/links.py` | **MODIFY** — use generic helper |
| `helpers/attachments/service.py` | **MODIFY** — use generic helper (or keep separate since it's file-based) |

---

## Current Code — Duplicated Pattern

### notes.py — `migrate_notes()` (lines ~50–67)

```python
def migrate_notes(title_to_id: dict[str, str]) -> int:
    notes = load_notes()
    migrated = 0
    new_notes: dict[str, list[dict]] = {}
    for key, entries in notes.items():
        if _ID_RE.match(key):
            new_notes.setdefault(key, []).extend(entries)
        elif key in title_to_id:
            tid = title_to_id[key]
            new_notes.setdefault(tid, []).extend(entries)
            migrated += 1
        else:
            new_notes.setdefault(key, []).extend(entries)
    if migrated:
        save_notes(new_notes)
    return migrated
```

### links.py — `migrate_links()` (lines ~46–58) — same pattern, different types

```python
def migrate_links(title_to_id: dict[str, str]) -> int:
    links = load_links()
    migrated = 0
    new_links: dict[str, str] = {}
    for key, path in links.items():
        if _ID_RE.match(key):
            new_links[key] = path
        elif key in title_to_id:
            new_links[title_to_id[key]] = path
            migrated += 1
        else:
            new_links[key] = path
    if migrated:
        save_links(new_links)
    return migrated
```

### service.py — `migrate_attachments()` (lines ~61–78) — file-system migration

```python
def migrate_attachments(title_to_id: dict[str, str]) -> int:
    base = attachments_dir()
    if not base.exists():
        return 0
    migrated = 0
    for old_dir in list(base.iterdir()):
        if not old_dir.is_dir():
            continue
        dirname = old_dir.name
        if _ID_RE.match(dirname):
            continue
        for title, tid in title_to_id.items():
            if safe_filename(title) == dirname:
                new_dir = base / tid
                if not new_dir.exists():
                    old_dir.rename(new_dir)
                    migrated += 1
                break
    return migrated
```

---

## Required Changes

### Step 1: Create `helpers/attachments/migration.py`

```python
"""Generic key migration for title-based → ID-based stores."""

from __future__ import annotations

import re
from typing import Any, Callable, TypeVar

_ID_RE = re.compile(r"^[PTDW]-\d{3,}$")

T = TypeVar("T")


def migrate_dict_store(
    load_fn: Callable[[], dict[str, T]],
    save_fn: Callable[[dict[str, T]], None],
    title_to_id: dict[str, str],
    merge_fn: Callable[[dict[str, T], str, T], None] | None = None,
) -> int:
    """Migrate a dict-based store from title keys to ID keys.
    
    Args:
        load_fn: Function that returns the current store contents.
        save_fn: Function that persists the migrated store.
        title_to_id: Mapping of {task_title: task_id}.
        merge_fn: Optional function to handle merging values into the new dict.
                  Default behavior: new_store[new_key] = value.
    
    Returns:
        Number of entries migrated.
    """
    store = load_fn()
    migrated = 0
    new_store: dict[str, T] = {}

    for key, value in store.items():
        if _ID_RE.match(key):
            # Already migrated
            if merge_fn:
                merge_fn(new_store, key, value)
            else:
                new_store[key] = value
        elif key in title_to_id:
            new_key = title_to_id[key]
            if merge_fn:
                merge_fn(new_store, new_key, value)
            else:
                new_store[new_key] = value
            migrated += 1
        else:
            # Unresolvable — preserve under original key
            if merge_fn:
                merge_fn(new_store, key, value)
            else:
                new_store[key] = value

    if migrated:
        save_fn(new_store)
    return migrated
```

### Step 2: Simplify `notes.py`

```python
from helpers.attachments.migration import migrate_dict_store


def _merge_notes(store: dict, key: str, entries: list[dict]) -> None:
    store.setdefault(key, []).extend(entries)


def migrate_notes(title_to_id: dict[str, str]) -> int:
    return migrate_dict_store(load_notes, save_notes, title_to_id, merge_fn=_merge_notes)
```

### Step 3: Simplify `links.py`

```python
from helpers.attachments.migration import migrate_dict_store


def migrate_links(title_to_id: dict[str, str]) -> int:
    return migrate_dict_store(load_links, save_links, title_to_id)
```

### Step 4: Keep `service.py` migration mostly as-is

The `migrate_attachments()` function operates on the filesystem (renaming directories), not on a JSON dict. It doesn't fit the `migrate_dict_store()` pattern well. Keep it as a standalone function but ensure it uses the shared `_ID_RE` from the migration module:

```python
from helpers.attachments.migration import _ID_RE

def migrate_attachments(title_to_id: dict[str, str]) -> int:
    # ... existing filesystem-based logic, using shared _ID_RE ...
```

---

## Acceptance Criteria

1. `helpers/attachments/migration.py` exists with `migrate_dict_store()`
2. `notes.py` and `links.py` use the generic helper
3. `service.py` uses the shared `_ID_RE` (but keeps its filesystem logic)
4. All three `migrate_*` functions produce identical results
5. `_ID_RE` regex is defined in one place (migration.py)
6. `pytest tests/test_migration.py` and `tests/test_notes_id_keying.py` pass
7. The generic helper is independently testable

---

## Constraints

- The notes store uses `setdefault().extend()` merging — the generic helper must support this via `merge_fn`
- The links store uses simple key assignment — the generic helper's default behavior
- The attachments store is filesystem-based — it CANNOT use the generic dict helper
- Do NOT change the migration behavior — only deduplicate the implementation
- `_ID_RE` pattern must match the existing `^[PTDW]-\d{3,}$` pattern exactly
