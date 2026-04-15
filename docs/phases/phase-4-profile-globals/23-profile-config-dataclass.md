# Task 23: Replace Profile Globals with ProfileConfig Dataclass

**Audit ID**: C-01  
**Effort**: Large  
**Phase**: 4 — Profile Globals Refactor

---

## Objective

Replace the 11 mutable global variables in `helpers/profile/profile.py` with a frozen `ProfileConfig` dataclass. Provide a `get_active_config()` function that returns the current snapshot. Update all consumers (~10 files) to use the new API.

---

## Audit Reference

> **C-01: Profile Module Uses 11 Global Variables Mutated at Runtime**
>
> Every module importing these holds stale values until `reload()` is called. Tests cannot run in parallel. No thread safety.
>
> **Consumers** (all hold potentially stale references):
> - `helpers/commands/report_pipeline.py`
> - `helpers/commands/utilities.py`
> - `helpers/profile/config.py`
> - `scripts/gui/app.py`
> - `scripts/gui/pages/settings_page.py`
> - `scripts/cli/run.py`
> - `helpers/profile/portability.py`

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/profile/profile.py` | **MODIFY** — add ProfileConfig, get_active_config(), keep backward-compat aliases |
| `helpers/profile/config.py` | **MODIFY** — use get_active_config() |
| `helpers/commands/report_pipeline.py` | **MODIFY** — use get_active_config() |
| `helpers/commands/utilities.py` | **MODIFY** — use get_active_config() |
| `helpers/profile/portability.py` | **MODIFY** — use get_active_config() |
| `scripts/gui/app.py` | **MODIFY** — use get_active_config() |
| `scripts/gui/pages/profile_page.py` | **MODIFY** — use get_active_config() |
| `scripts/gui/pages/settings_page.py` | **MODIFY** — use get_active_config() |
| `scripts/cli/run.py` | **MODIFY** — use get_active_config() |

---

## Current Code

### 11 global variables (lines ~71–81)

```python
USER_NAME: str = ""
USER_ROLE: str = ""
USER_COMPANY: str = ""
USER_EMAIL: str = ""
USER_PHONE: str = ""
RECIPIENT_NAME: str = ""
RECIPIENT_EMAIL: str = ""
WORKBOOK_FILENAME: str = ""
DAILY_HOURS_BUDGET: float = 8.0
WEEKLY_HOURS_BUDGET: float = 40.0
```

### _apply_profile() mutates them (lines ~84–110)

```python
def _apply_profile(index: int) -> None:
    global USER_NAME, USER_ROLE, USER_COMPANY, USER_EMAIL, USER_PHONE
    global RECIPIENT_NAME, RECIPIENT_EMAIL, WORKBOOK_FILENAME
    global DAILY_HOURS_BUDGET, WEEKLY_HOURS_BUDGET
    global _active_index

    _active_index = index
    p = _profiles[index]
    USER_NAME = p.get("name", "")
    USER_ROLE = p.get("role", "")
    USER_COMPANY = p.get("company", "")
    # ... etc.
```

### Consumer examples

```python
# report_pipeline.py — imports all globals at top level
from helpers.profile.profile import (
    USER_NAME, USER_COMPANY, USER_EMAIL, USER_PHONE,
    RECIPIENT_NAME, RECIPIENT_EMAIL, WORKBOOK_FILENAME,
    DAILY_HOURS_BUDGET, WEEKLY_HOURS_BUDGET,
)

# app.py — accesses via module reference
import helpers.profile.profile as _prof
# ...
if _prof.USER_COMPANY and _prof.WORKBOOK_FILENAME:
    ensure_profile_dirs()
```

---

## Required Changes

### Step 1: Create ProfileConfig dataclass in `helpers/profile/profile.py`

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileConfig:
    """Immutable snapshot of the active profile configuration."""
    name: str = ""
    role: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    recipient_name: str = ""
    recipient_email: str = ""
    workbook_filename: str = ""
    daily_hours_budget: float = 8.0
    weekly_hours_budget: float = 40.0
```

### Step 2: Add `get_active_config()` function

```python
_active_config: ProfileConfig = ProfileConfig()


def get_active_config() -> ProfileConfig:
    """Return the current profile configuration snapshot."""
    return _active_config


def _apply_profile(index: int) -> None:
    global _active_index, _active_config
    _active_index = index
    p = _profiles[index]
    _active_config = ProfileConfig(
        name=p.get("name", ""),
        role=p.get("role", ""),
        company=p.get("company", ""),
        email=p.get("email", ""),
        phone=str(p.get("phone", "")),
        recipient_name=p.get("recipient_name", ""),
        recipient_email=p.get("recipient_email", ""),
        workbook_filename=p.get("workbook_filename", ""),
        daily_hours_budget=float(p.get("daily_hours_budget", 8.0)),
        weekly_hours_budget=float(p.get("weekly_hours_budget", 40.0)),
    )
    # Backward compatibility: update legacy globals
    _sync_legacy_globals()
```

### Step 3: Keep backward-compatible globals (temporarily)

To avoid a big-bang rewrite, keep the old globals but update them from `_active_config`:

```python
def _sync_legacy_globals() -> None:
    """Keep legacy globals in sync for backward compatibility.
    
    DEPRECATED: Consumers should use get_active_config() instead.
    """
    global USER_NAME, USER_ROLE, USER_COMPANY, USER_EMAIL, USER_PHONE
    global RECIPIENT_NAME, RECIPIENT_EMAIL, WORKBOOK_FILENAME
    global DAILY_HOURS_BUDGET, WEEKLY_HOURS_BUDGET
    
    cfg = _active_config
    USER_NAME = cfg.name
    USER_ROLE = cfg.role
    USER_COMPANY = cfg.company
    USER_EMAIL = cfg.email
    USER_PHONE = cfg.phone
    RECIPIENT_NAME = cfg.recipient_name
    RECIPIENT_EMAIL = cfg.recipient_email
    WORKBOOK_FILENAME = cfg.workbook_filename
    DAILY_HOURS_BUDGET = cfg.daily_hours_budget
    WEEKLY_HOURS_BUDGET = cfg.weekly_hours_budget
```

### Step 4: Update consumers one at a time

For each consumer file, replace global imports with `get_active_config()` calls:

**Before (report_pipeline.py):**
```python
from helpers.profile.profile import USER_NAME, USER_COMPANY, ...

def generate_reports(...):
    log(f"Generating for {USER_NAME} at {USER_COMPANY}")
```

**After:**
```python
from helpers.profile.profile import get_active_config

def generate_reports(...):
    cfg = get_active_config()
    log(f"Generating for {cfg.name} at {cfg.company}")
```

**Before (app.py):**
```python
import helpers.profile.profile as _prof
# ...
if _prof.USER_COMPANY and _prof.WORKBOOK_FILENAME:
```

**After:**
```python
from helpers.profile.profile import get_active_config
# ...
cfg = get_active_config()
if cfg.company and cfg.workbook_filename:
```

### Step 5: Update all ~10 consumer files

Process each file in order (smallest impact first):

1. `helpers/profile/config.py` — wraps globals in functions, easy update
2. `helpers/commands/utilities.py` — imports 3 globals
3. `helpers/profile/portability.py` — imports profile globals
4. `helpers/commands/report_pipeline.py` — imports all 10 globals (biggest single consumer)
5. `scripts/cli/run.py` — imports all globals for CLI startup
6. `scripts/gui/app.py` — uses `_prof.USER_COMPANY` etc.
7. `scripts/gui/pages/profile_page.py` — profile editing page
8. `scripts/gui/pages/settings_page.py` — settings display

---

## Acceptance Criteria

1. `ProfileConfig` dataclass exists in `helpers/profile/profile.py`
2. `get_active_config()` returns a frozen `ProfileConfig` snapshot
3. All consumer files use `get_active_config()` instead of importing globals directly
4. Legacy globals still exist and are kept in sync (for any consumers not yet updated)
5. `switch_profile()` and `reload()` properly update the `ProfileConfig`
6. `pytest tests/` passes — all existing tests work with the new API
7. Tests can create `ProfileConfig` instances directly (no global state needed)

---

## Constraints

- **Backward compatibility is mandatory** — keep legacy globals during the transition
- Update one consumer file at a time — commit after each works
- The `ProfileConfig` is `frozen=True` — consumers can't accidentally mutate it
- Do NOT remove the legacy globals until all consumers are confirmed updated
- `get_active_config()` must always return a valid instance (never `None`)
- The YAML reading/writing logic stays unchanged — only the in-memory representation changes

## Migration Strategy

1. Add `ProfileConfig` + `get_active_config()` + `_sync_legacy_globals()` first — commit
2. Update consumers one at a time, testing after each — commit per file
3. Once all consumers are updated, the legacy globals and `_sync_legacy_globals()` can be removed in a final cleanup commit
