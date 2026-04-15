# Task 4: Add Public `rebuild_sidebar()` to App

**Audit ID**: M-11  
**Effort**: Tiny  
**Phase**: 1 — Foundation

---

## Objective

Expose `_build_sidebar()` on the App class as a public method `rebuild_sidebar()` so that `profile_page.py` does not need to call a private method. Update all call sites in `profile_page.py` to use the public API.

---

## Audit Reference

> **M-11: Profile Page Calls Private App Methods**
>
> File: `scripts/gui/pages/profile_page.py` (lines 218, 264, 310, 342, 438)
>
> ```python
> self.app._build_sidebar()  # Private method
> self.app.reload_data()
> ```

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/app.py` | **MODIFY** — add `rebuild_sidebar()` public method |
| `scripts/gui/pages/profile_page.py` | **MODIFY** — replace `_build_sidebar()` calls with `rebuild_sidebar()` |

---

## Current Code

### app.py — private `_build_sidebar()` (line ~125)

```python
def _build_sidebar(self):
    # Destroy existing sidebar if rebuilding
    if hasattr(self, "_sidebar_frame") and self._sidebar_frame is not None:
        self._sidebar_frame.destroy()
    # ... sidebar construction code
```

### profile_page.py — 5 call sites using the private method

All follow the same pattern:
```python
self.app._build_sidebar()
self.app.reload_data()
```

Found at approximately lines: 218, 264–265, 310, 342–343, 438–439.

---

## Required Changes

### Step 1: Add public method to `scripts/gui/app.py`

Add a public `rebuild_sidebar()` method that delegates to `_build_sidebar()`:

```python
def rebuild_sidebar(self) -> None:
    """Rebuild the sidebar navigation (public API for pages)."""
    self._build_sidebar()
```

Place this near `_build_sidebar()` for locality.

### Step 2: Update all call sites in `scripts/gui/pages/profile_page.py`

Replace every instance of:
```python
self.app._build_sidebar()
```

With:
```python
self.app.rebuild_sidebar()
```

There are 5 occurrences (approximately lines 218, 264, 310, 342, 438).

---

## Acceptance Criteria

1. `rebuild_sidebar()` exists as a public method on App
2. Zero calls to `self.app._build_sidebar()` remain in `profile_page.py`
3. All 5 call sites use `self.app.rebuild_sidebar()` instead
4. `self.app.reload_data()` calls are NOT changed (reload_data is already public)
5. `pytest tests/` passes — specifically `tests/gui/test_app_integration.py`

---

## Constraints

- Do NOT rename or remove `_build_sidebar()` — it may be used internally in `app.py`
- Do NOT change `reload_data()` — it is already public
- The new method is a simple delegation — no new logic
- Do NOT add this to the `AppContext` protocol yet (that can be done in a future cleanup)
