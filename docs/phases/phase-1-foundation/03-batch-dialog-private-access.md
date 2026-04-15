# Task 3: Fix Batch Dialog Private Member Access

**Audit ID**: C-09  
**Effort**: Tiny  
**Phase**: 1 — Foundation

---

## Objective

Replace the batch dialog's direct access to `self._service._profile` (a private member of DomainService) with the existing public property `self._service.profile`.

---

## Audit Reference

> **C-09: Batch Dialog Accesses Private `_service._profile`**
>
> File: `scripts/gui/dialogs/batch_dialog.py` (line ~160)
>
> ```python
> profile = self._service._profile  # DIRECT ACCESS TO PRIVATE MEMBER
> ```

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/dialogs/batch_dialog.py` | **MODIFY** — change `_service._profile` → `_service.profile` |

---

## Current Code

### batch_dialog.py (line ~160, inside the date shift loop)

```python
if shift_start or shift_end or shift_deadline:
    for tid in self._task_ids:
        try:
            profile = self._service._profile          # ← PRIVATE ACCESS
            task = profile.find_task_global(tid)
            if not task:
                continue
            edits: dict = {}
            if shift_start and isinstance(task.start, date):
                edits["start"] = task.start + delta
            if shift_end and isinstance(task.end, date):
                edits["end"] = task.end + delta
            if shift_deadline and isinstance(task.deadline, date):
                edits["deadline"] = task.deadline + delta
            if edits:
                self._service.edit_task(tid, edits)
                changes += 1
        except Exception:
            pass
```

### DomainService already has a public property

```python
# helpers/commands/domain_service.py (lines 38–44)
@property
def profile(self) -> Profile:
    """The active profile."""
    return self._profile

@profile.setter
def profile(self, value: Profile) -> None:
    self._profile = value
```

---

## Required Changes

### Single change in `scripts/gui/dialogs/batch_dialog.py`

Replace:
```python
profile = self._service._profile
```

With:
```python
profile = self._service.profile
```

Additionally, move the `profile` lookup outside the loop since it doesn't change per iteration:

```python
if shift_start or shift_end or shift_deadline:
    profile = self._service.profile              # ← PUBLIC PROPERTY, outside loop
    for tid in self._task_ids:
        try:
            task = profile.find_task_global(tid)
            # ... rest unchanged
```

---

## Acceptance Criteria

1. No references to `self._service._profile` remain in `batch_dialog.py`
2. `self._service.profile` is used instead
3. Date shifting functionality works identically
4. `pytest tests/gui/test_batch_dialog.py` passes

---

## Constraints

- Do NOT modify `DomainService` — the public property already exists
- Do NOT change the batch dialog's behavior or error handling (the bare `except` is addressed in Task 5)
- This is a one-line fix (plus optional loop optimization)
