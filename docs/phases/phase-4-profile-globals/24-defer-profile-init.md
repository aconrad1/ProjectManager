# Task 24: Defer Profile Initialization

**Audit ID**: C-02  
**Effort**: Medium  
**Phase**: 4 — Profile Globals Refactor

---

## Objective

Remove the import-time code execution in `helpers/profile/profile.py` that loads YAML and mutates globals on import. Replace with an explicit `ensure_initialized()` function called once by entry points.

---

## Audit Reference

> **C-02: Profile Module Runs Code at Import Time**
>
> ```python
> # ── Initialise on import ──────────────────────────────────────────────────
> _profiles, _active_index = _load_profiles()
> _apply_profile(_active_index)
> ```
>
> Any module that imports from `helpers.profile.profile` triggers file I/O (YAML read) and global mutation. If the YAML file is missing, `sys.exit(1)` — a hard exit with no recovery.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/profile/profile.py` | **MODIFY** — defer initialization, add ensure_initialized() |
| `scripts/cli.py` or `scripts/cli/run.py` | **MODIFY** — call ensure_initialized() at startup |
| `scripts/gui.py` or `scripts/gui/app.py` | **MODIFY** — call ensure_initialized() at startup |

---

## Current Code

### Import-time execution (lines ~114–117)

```python
# ── Initialise on import ──────────────────────────────────────────────────────
_profiles, _active_index = _load_profiles()
_apply_profile(_active_index)
```

### _load_profiles() calls sys.exit(1) on missing YAML

```python
def _load_profiles() -> tuple[list[dict], int]:
    if not PROFILE_PATH.exists():
        # ... legacy check ...
        if not legacy.exists():
            print("ERROR: user_profile.yaml not found ...", file=sys.stderr)
            sys.exit(1)  # HARD EXIT — no recovery
    # ...
```

### Entry points import the module

```python
# scripts/gui/app.py
import helpers.profile.profile as _prof

if _prof.USER_COMPANY and _prof.WORKBOOK_FILENAME:
    ensure_profile_dirs()
```

---

## Required Changes

### Step 1: Replace import-time code with deferred initialization

```python
# Module-level state (uninitialized)
_profiles: list[dict] = []
_active_index: int = 0
_initialized: bool = False


def ensure_initialized() -> None:
    """Load profiles from YAML if not already done.
    
    Call this once from the app entry point (cli.py or gui.py).
    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _profiles, _active_index, _initialized
    if _initialized:
        return
    _profiles, _active_index = _load_profiles()
    _apply_profile(_active_index)
    _initialized = True


# REMOVE these lines:
# _profiles, _active_index = _load_profiles()
# _apply_profile(_active_index)
```

### Step 2: Replace sys.exit(1) with an exception

```python
class ProfileNotFoundError(Exception):
    """Raised when user_profile.yaml is missing."""
    pass


def _load_profiles() -> tuple[list[dict], int]:
    if not PROFILE_PATH.exists():
        # ... legacy check ...
        if not legacy.exists():
            raise ProfileNotFoundError(
                f"user_profile.yaml not found at {PROFILE_PATH}. "
                "Copy the template and fill in your details before running."
            )
    # ...
```

### Step 3: Call ensure_initialized() in entry points

**scripts/cli.py (or scripts/cli/run.py):**
```python
from helpers.profile.profile import ensure_initialized

def main():
    ensure_initialized()
    # ... rest of CLI startup ...
```

**scripts/gui.py (or scripts/gui/app.py):**
```python
from helpers.profile.profile import ensure_initialized

def main():
    ensure_initialized()
    # ... rest of GUI startup ...
```

### Step 4: Make get_active_config() safe before initialization

```python
def get_active_config() -> ProfileConfig:
    """Return the current profile configuration snapshot.
    
    Returns a default (empty) ProfileConfig if called before initialization.
    """
    return _active_config  # Already defaults to ProfileConfig() with empty fields
```

### Step 5: Guard functions that require initialization

```python
def switch_profile(index: int) -> None:
    ensure_initialized()
    # ... existing logic ...


def get_profiles() -> list[dict]:
    ensure_initialized()
    return list(_profiles)
```

---

## Acceptance Criteria

1. Importing `helpers.profile.profile` does NOT trigger YAML loading or global mutation
2. `ensure_initialized()` loads YAML and sets up the profile on first call
3. Subsequent calls to `ensure_initialized()` are no-ops
4. Both CLI and GUI entry points call `ensure_initialized()` before using profile data
5. A missing YAML file raises `ProfileNotFoundError` instead of calling `sys.exit(1)`
6. `get_active_config()` is safe to call before initialization (returns empty config)
7. `switch_profile()` and `get_profiles()` auto-initialize if needed
8. `pytest tests/` passes — tests may need to call `ensure_initialized()` in fixtures

---

## Constraints

- This change depends on Task 23 (ProfileConfig) being complete
- `ensure_initialized()` must be idempotent — safe to call from multiple places
- Do NOT use threading locks for initialization — the entry points are single-threaded at startup
- The `ProfileNotFoundError` exception must be catchable by the GUI for a graceful error dialog
- Keep the legacy YAML migration logic (moving from root to profiles/) intact
- Tests that mock profile data should not trigger real YAML loading
