# Task 19: Improve Autosave Error Handling

**Audit ID**: C-11  
**Effort**: Small  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

Improve the autosave error handling to log exceptions, track consecutive failures, and show a persistent warning if autosave fails repeatedly.

---

## Audit Reference

> **C-11: Autosave Silently Swallows Failures**
>
> ```python
> def _autosave(self) -> None:
>     if self.wb:
>         try:
>             self.wb.save(str(workbook_path()))
>             self._update_save_indicator("Autosaved")
>         except Exception:
>             self._update_save_indicator("Autosave failed")
> ```
>
> Fix: Log the exception. If autosave fails repeatedly (e.g., 3 times), show a persistent warning.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/app.py` | **MODIFY** — add logging, failure counter, persistent warning |

---

## Current Code (lines ~329–334)

```python
def _autosave(self) -> None:
    """Debounced autosave — writes .xlsx to disk."""
    self._autosave_id = None
    if self.wb:
        try:
            self.wb.save(str(workbook_path()))
            self._update_save_indicator("Autosaved")
        except Exception:
            self._update_save_indicator("Autosave failed")  # Brief indicator, then gone
```

---

## Required Changes

```python
import logging

_log = logging.getLogger(__name__)

# In __init__:
self._autosave_fail_count: int = 0
_MAX_AUTOSAVE_FAILURES: int = 3

def _autosave(self) -> None:
    """Debounced autosave — writes .xlsx to disk."""
    self._autosave_id = None
    if not self.wb:
        return
    try:
        self.wb.save(str(workbook_path()))
        self._autosave_fail_count = 0  # Reset on success
        self._update_save_indicator("Autosaved")
    except PermissionError:
        self._autosave_fail_count += 1
        _log.warning("Autosave failed (attempt %d): file may be locked by another program",
                     self._autosave_fail_count)
        self._update_save_indicator("Autosave failed — file locked")
        self._check_autosave_failures()
    except OSError as e:
        self._autosave_fail_count += 1
        _log.warning("Autosave failed (attempt %d): %s", self._autosave_fail_count, e)
        self._update_save_indicator("Autosave failed")
        self._check_autosave_failures()


def _check_autosave_failures(self) -> None:
    """Show a persistent warning if autosave has failed too many times."""
    if self._autosave_fail_count >= self._MAX_AUTOSAVE_FAILURES:
        messagebox.showwarning(
            "Autosave Problem",
            f"Autosave has failed {self._autosave_fail_count} times in a row.\n\n"
            "Possible causes:\n"
            "• The workbook is open in Excel\n"
            "• The file is locked by OneDrive sync\n"
            "• Disk is full or read-only\n\n"
            "Your changes are preserved in memory. Try saving manually\n"
            "(Ctrl+S) or close other programs using the file.",
            parent=self,
        )
        self._autosave_fail_count = 0  # Reset to avoid repeated popups
```

Key changes:
1. **Log the exception** with `logging.warning` including the attempt count
2. **Track consecutive failures** with `self._autosave_fail_count`
3. **Distinguish PermissionError** (common: file locked by Excel/OneDrive) from general OSError
4. **Show persistent warning** after 3 consecutive failures with actionable advice
5. **Reset counter** on success and after showing the warning (to avoid infinite popups)

---

## Acceptance Criteria

1. Autosave failures are logged with `logging.warning`
2. A counter tracks consecutive failures
3. After 3 consecutive failures, a `messagebox.showwarning` appears with helpful guidance
4. Successful autosave resets the failure counter
5. `PermissionError` gets a specific message ("file locked")
6. General `OSError` gets a generic message
7. `pytest tests/gui/test_app_integration.py` passes

---

## Constraints

- Do NOT catch `Exception` broadly — catch `PermissionError` and `OSError` specifically
- The warning dialog must not appear more than once per failure sequence (reset counter after showing)
- Do NOT use threading or background saves in this task
- The `_update_save_indicator` method continues to show brief status in the UI
- Do NOT add atomic write (temp file → rename) in this task — that's a future enhancement
