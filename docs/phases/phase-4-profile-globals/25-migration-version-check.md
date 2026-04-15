# Task 25: Add Migration Version Check to Skip Redundant Migration

**Audit ID**: C-15  
**Effort**: Small  
**Phase**: 4 — Profile Globals Refactor

---

## Objective

Add a migration version flag to `domain.json` metadata so the title→ID migration in `contract.py` only runs when needed, instead of on every profile load. Log when migration actually executes.

---

## Audit Reference

> **C-15: Migration Runs Silently on Every Profile Load**
>
> ```python
> from helpers.migration import migrate_to_id_keying
> migrate_to_id_keying(profile)
> ```
>
> Every call to `load_profile()` triggers migration, which loads/saves JSON files from disk. No logging, no confirmation.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/persistence/contract.py` | **MODIFY** — check version before migrating |
| `helpers/persistence/serializer.py` | **MODIFY** — add migration_version to _meta |
| `helpers/migration.py` | **MODIFY** — add logging, return whether migration occurred |

---

## Current Code

### contract.py — unconditional migration call (lines ~171–172)

```python
from helpers.migration import migrate_to_id_keying
migrate_to_id_keying(profile)
```

### serializer.py — current _meta envelope

```python
SCHEMA_VERSION = 1

def serialize_profile(profile: Profile, workbook_hash: str = "") -> str:
    envelope = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "workbook_hash": workbook_hash,
            "last_modified": datetime.now(tz=timezone.utc).isoformat(),
        },
        **profile.to_dict(),
    }
```

### migration.py — runs every time, no version check

```python
def migrate_to_id_keying(profile: Profile) -> None:
    title_to_id = build_title_to_id_map(profile)
    if not title_to_id:
        return

    n = migrate_notes(title_to_id)
    l = migrate_links(title_to_id)
    a = migrate_attachments(title_to_id)

    total = n + l + a
    if total:
        log.info("ID-keying migration: %d notes, %d links, %d attachment dirs migrated", n, l, a)
```

---

## Required Changes

### Step 1: Add `migration_version` to serializer _meta

```python
# helpers/persistence/serializer.py

SCHEMA_VERSION = 1
MIGRATION_VERSION = 2  # Increment when new migrations are added

def serialize_profile(profile: Profile, workbook_hash: str = "") -> str:
    envelope = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "migration_version": MIGRATION_VERSION,
            "workbook_hash": workbook_hash,
            "last_modified": datetime.now(tz=timezone.utc).isoformat(),
        },
        **profile.to_dict(),
    }
    return json.dumps(envelope, indent=2, ensure_ascii=False, default=str)
```

Add a helper to read the migration version from a JSON file:

```python
def read_migration_version(json_path: Path) -> int:
    """Read the migration_version from a domain.json file. Returns 0 if absent."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return int(data.get("_meta", {}).get("migration_version", 0))
    except (OSError, json.JSONDecodeError, ValueError):
        return 0
```

### Step 2: Check version before migrating in contract.py

```python
from helpers.persistence.serializer import read_migration_version, MIGRATION_VERSION

# In load_profile():
json_path = ...  # path to domain.json
current_version = read_migration_version(json_path)
if current_version < MIGRATION_VERSION:
    from helpers.migration import migrate_to_id_keying
    migrate_to_id_keying(profile)
    log.info("Migration complete (version %d → %d)", current_version, MIGRATION_VERSION)
    # Re-save to update the migration version in _meta
    # (This happens naturally if contract.save() is called, or force it here)
```

### Step 3: Add logging to migration.py

```python
import logging

log = logging.getLogger(__name__)

def migrate_to_id_keying(profile: Profile) -> None:
    """Migrate notes, links, and attachments from title-based to ID-based keys."""
    title_to_id = build_title_to_id_map(profile)
    if not title_to_id:
        log.debug("No tasks found for migration — skipping")
        return

    n = migrate_notes(title_to_id)
    l = migrate_links(title_to_id)
    a = migrate_attachments(title_to_id)

    total = n + l + a
    if total:
        log.info("ID-keying migration: %d notes, %d links, %d attachment dirs migrated", n, l, a)
    else:
        log.debug("ID-keying migration: all entries already migrated")
```

---

## Acceptance Criteria

1. `domain.json` _meta envelope includes `migration_version`
2. `load_profile()` only calls `migrate_to_id_keying()` when `migration_version < MIGRATION_VERSION`
3. After migration, re-saving the profile stamps the new `migration_version`
4. Subsequent loads skip migration entirely (no file I/O from migration code)
5. Migration execution is logged at INFO level
6. Migration skipping is logged at DEBUG level
7. `pytest tests/` passes — especially `test_migration.py` and `test_phase5_persistence.py`

---

## Constraints

- `MIGRATION_VERSION = 2` (version 1 = original schema, version 2 = ID-keyed)
- Files without `migration_version` in _meta are treated as version 0 (need migration)
- Do NOT change the migration logic itself — only add the version check wrapper
- The version check must handle missing/corrupt JSON gracefully (default to 0)
- Keep `migrate_to_id_keying()` safe to call multiple times (it already is) — the version check is an optimization, not a correctness requirement
