# Task 1: Extract Shared Dialog Base Class

**Audit ID**: M-03  
**Effort**: Small  
**Phase**: 1 — Foundation

---

## Objective

Extract duplicated dialog helper methods (`_get()`, `_parse_date()`, and button frame layout) from three dialog files into a shared `BaseDialog` class. All three dialogs should inherit from this base class.

---

## Audit Reference

> **M-03: Dialog Helper Methods Duplicated Across 3 Files**
>
> Files: `scripts/gui/dialogs/task_dialog.py`, `project_dialog.py`, `deliverable_dialog.py`
>
> All three independently implement `_get(key)`, `_parse_date(key)`, and button frame layout (Save + Cancel buttons with identical styling).

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/dialogs/base_dialog.py` | **CREATE** — new shared base class |
| `scripts/gui/dialogs/task_dialog.py` | **MODIFY** — inherit from BaseDialog, remove duplicated methods |
| `scripts/gui/dialogs/project_dialog.py` | **MODIFY** — inherit from BaseDialog, remove duplicated methods |
| `scripts/gui/dialogs/deliverable_dialog.py` | **MODIFY** — inherit from BaseDialog, remove duplicated methods |

---

## Current Code (Duplicated in All 3 Dialogs)

### `_get()` method (identical in all three)

```python
def _get(self, key: str) -> str:
    w = self.entries[key]
    if isinstance(w, ctk.CTkEntry):
        return w.get().strip()
    elif isinstance(w, ctk.CTkTextbox):
        return w.get("1.0", "end").strip()
    elif hasattr(w, "_variable"):
        return w._variable.get()
    return ""
```

### `_parse_date()` method (identical in all three)

```python
def _parse_date(self, key: str):
    """Parse a YYYY-MM-DD date entry, returning None if empty/invalid."""
    raw = self._get(key)
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None
```

### Button frame layout (identical structure in all three)

```python
btn_frame = ctk.CTkFrame(self, fg_color="transparent")
btn_frame.pack(fill="x", padx=14, pady=10)
ctk.CTkButton(
    btn_frame, text="Save", width=140, fg_color=AG_DARK,
    hover_color=AG_MID, command=self._save,
).pack(side="left")
ctk.CTkButton(
    btn_frame, text="Cancel", width=140, fg_color="gray",
    hover_color="darkgray", command=self.destroy,
).pack(side="right")
```

---

## Required Changes

### Step 1: Create `scripts/gui/dialogs/base_dialog.py`

Create a new `BaseDialog` class that inherits from `ctk.CTkToplevel` and provides:

1. `self.entries: dict` — initialized in `__init__` as an empty dict for subclass use
2. `_get(self, key: str) -> str` — the shared widget reader
3. `_parse_date(self, key: str) -> date | None` — the shared date parser
4. `_build_button_frame(self, save_command: Callable) -> None` — creates the standard Save/Cancel button layout

The base class must import `customtkinter as ctk`, `datetime`, and the theme constants (`AG_DARK`, `AG_MID`) from `scripts/gui/ui_theme.py`.

### Step 2: Modify each dialog to inherit from `BaseDialog`

For each of `task_dialog.py`, `project_dialog.py`, `deliverable_dialog.py`:

1. Change the class to inherit from `BaseDialog` instead of `ctk.CTkToplevel`
2. Call `super().__init__(...)` in `__init__`
3. Remove the duplicated `_get()` method
4. Remove the duplicated `_parse_date()` method
5. Replace the inline button frame code with `self._build_button_frame(self._save)`
6. Ensure `self.entries` dict is populated as before (the base class initializes it empty)

### Step 3: Verify imports

Ensure all three dialogs import from the new base:

```python
from scripts.gui.dialogs.base_dialog import BaseDialog
```

Or using relative imports if the dialogs already use them:

```python
from .base_dialog import BaseDialog
```

---

## Acceptance Criteria

1. All three dialogs function identically to before (Save, Cancel, date parsing, widget reading)
2. `_get()` and `_parse_date()` exist only in `base_dialog.py`, not in any subclass
3. Button frame styling (colors, widths, layout) is unchanged
4. `pytest tests/` passes — specifically:
   - `tests/gui/test_batch_dialog.py`
   - `tests/gui/test_deliverable_dialog.py`
   - `tests/gui/test_add_task_page.py`
5. No new dependencies introduced
6. Each dialog's `_save()` method still works correctly (it is NOT extracted — each dialog has unique save logic)

---

## Constraints

- Do NOT extract `_save()` — each dialog has unique validation and persistence logic
- Do NOT change the visual appearance of any dialog
- Do NOT add features or parameters beyond what's needed for deduplication
- The base class lives in `scripts/gui/dialogs/`, not in `helpers/` (it has UI dependencies)
- Use relative imports within the `scripts/gui/dialogs/` package
