# Task 18: Debounce External Edit Detection on Focus

**Audit ID**: C-10  
**Effort**: Small  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

Debounce the external edit detection that runs on every window focus event. Limit the check to at most once per 5 seconds to avoid repeated hash computations and messagebox prompts during rapid alt-tab sequences.

---

## Audit Reference

> **C-10: External Edit Detection Runs on Every Window Focus**
>
> Every time the window regains focus: reads the workbook file from disk, computes SHA-256 hash, compares to stored hash, shows a messagebox if changed. SHA-256 of a workbook can be expensive. Focus events fire frequently.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/app.py` | **MODIFY** — add time-based debounce to focus handler |

---

## Current Code

### Focus handler (lines ~451–464)

```python
def _on_focus_in(self, event=None) -> None:
    """Called when the window regains focus — check for external edits."""
    if event and event.widget is not self:
        return
    self._check_external_edits()
```

### External edit detection (lines ~467–495)

```python
def _check_external_edits(self) -> None:
    """Detect external workbook modifications and prompt the user."""
    if not self._profile_is_configured():
        return

    wb_path = workbook_path()
    if not wb_path.exists():
        return

    try:
        changed = detect_external_edits(_prof.USER_COMPANY, wb_path)
    except Exception:
        return

    if not changed:
        return

    answer = messagebox.askyesno(
        "External Edit Detected",
        "The workbook has been modified outside the application.\n\n"
        "Reload data from the workbook?\n\n"
        "Yes = import external changes (overwrites in-memory state)\n"
        "No = keep current state (will overwrite external changes on next save)",
        parent=self,
    )
    if answer:
        self.reload_data()
        self._update_save_indicator("Reloaded external changes")
    else:
        if self.profile and self.wb:
            save_profile_dual(self.profile, self.wb, wb_path=wb_path)
            self._update_save_indicator("External changes ignored")
```

---

## Required Changes

### Add time-based debounce to `_on_focus_in()`

```python
import time

# In __init__:
self._last_edit_check: float = 0.0
_EDIT_CHECK_INTERVAL: float = 5.0  # seconds

def _on_focus_in(self, event=None) -> None:
    """Called when the window regains focus — check for external edits."""
    if event and event.widget is not self:
        return
    now = time.monotonic()
    if now - self._last_edit_check < self._EDIT_CHECK_INTERVAL:
        return  # Skip — checked recently
    self._last_edit_check = now
    self._check_external_edits()
```

### Keep `_check_external_edits()` unchanged

The check method itself doesn't need changes. The debounce is in the caller.

---

## Acceptance Criteria

1. `_check_external_edits()` runs at most once per 5 seconds regardless of focus event frequency
2. The first focus event after 5+ seconds of no checks triggers a check
3. Rapid alt-tabbing does not cause repeated hash computations
4. External edit detection still works correctly when changes are present
5. The messagebox prompt still appears when an external edit is detected (just not repeatedly)
6. `pytest tests/gui/test_app_integration.py` passes

---

## Constraints

- Use `time.monotonic()` (not `time.time()`) for the timer — it's immune to system clock changes
- Do NOT move hash computation to a background thread in this task (that's a larger change)
- 5 seconds is the recommended interval — adjustable if needed
- Do NOT change `_check_external_edits()` itself — only debounce the caller
- The interval should be a class constant for easy adjustment
