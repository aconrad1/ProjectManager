# Task 14: Add `find_by_id()` to Profile for Generic ID Resolution

**Audit ID**: M-05  
**Effort**: Small  
**Phase**: 2 — Separation of Concerns

---

## Objective

Add a `find_by_id(item_id)` method to the `Profile` class that resolves any prefixed ID (P-NNN, T-NNN, D-NNN) to the corresponding domain object. Replace manual ID prefix parsing in `gantt_page.py` with this method.

---

## Audit Reference

> **M-05: pages/gantt_page.py — Direct ID Prefix Parsing**
>
> ```python
> prefix = item_id.split("-")[0] if "-" in item_id else ""
> if prefix == "T":
>     node = self.app.profile.find_task_global(item_id)
> elif prefix == "D":
>     node = self._find_deliverable(item_id)
> ```
>
> The page is parsing the ID format directly, coupling it to the ID naming scheme.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/domain/profile.py` | **MODIFY** — add `find_by_id()` method |
| `scripts/gui/pages/gantt_page.py` | **MODIFY** — use `find_by_id()` instead of prefix parsing |

---

## Current Code

### gantt_page.py — ID prefix parsing appears twice

**In `_shift_date()` (line ~376):**
```python
def _shift_date(self, item_id: str, field: str, days: int) -> None:
    service = self.app.service
    if not service:
        return

    prefix = item_id.split("-")[0] if "-" in item_id else ""
    if prefix == "T":
        node = self.app.profile.find_task_global(item_id)
    elif prefix == "D":
        node = self._find_deliverable(item_id)
    else:
        return

    if not node:
        return

    current = getattr(node, field, None)
    if not isinstance(current, date):
        return
    new_date = current + timedelta(days=days)

    if prefix == "T":
        service.edit_task(item_id, {field: new_date})
    else:
        service.edit_deliverable(item_id, {field: new_date})
    self._render()
```

**In `_open_edit_dialog()` (line ~399):**
```python
def _open_edit_dialog(self, item_id: str) -> None:
    prefix = item_id.split("-")[0] if "-" in item_id else ""
    if prefix == "T":
        node = self.app.profile.find_task_global(item_id)
        # ... open TaskDialog ...
    elif prefix == "D":
        node = self._find_deliverable(item_id)
        # ... open DeliverableDialog ...
```

**Private helper in gantt_page.py (line ~417):**
```python
def _find_deliverable(self, deliverable_id: str):
    if not self.app.profile:
        return None
    for task in self.app.profile.all_tasks:
        d = task.find_deliverable(deliverable_id)
        if d:
            return d
    return None
```

### Profile — existing find methods (helpers/domain/profile.py)

```python
def find_project(self, project_id: str) -> Project | None:
    for p in self.projects:
        if p.id == project_id:
            return p
    return None

def find_task_global(self, task_id: str) -> Task | None:
    for p in self.projects:
        t = p.find_task(task_id)
        if t:
            return t
    return None
```

### helpers/schema/ids.py — existing parse function

```python
def parse_id(value: str) -> tuple[str, int]:
    """Parse 'P-003' → ('P', 3).  Raises ValueError on bad format."""
    m = _ID_PATTERN.match(str(value).strip())
    if not m:
        raise ValueError(f"Invalid ID format: {value!r}")
    return m.group(1), int(m.group(2))
```

---

## Required Changes

### Step 1: Add `find_by_id()` to `helpers/domain/profile.py`

```python
def find_by_id(self, item_id: str) -> Project | Task | Deliverable | None:
    """Resolve any prefixed ID (P-NNN, T-NNN, D-NNN) to the domain object."""
    if not item_id or "-" not in item_id:
        return None
    prefix = item_id.split("-")[0].upper()
    if prefix == "P":
        return self.find_project(item_id)
    if prefix == "T":
        return self.find_task_global(item_id)
    if prefix == "D":
        for task in self.all_tasks:
            d = task.find_deliverable(item_id)
            if d:
                return d
    return None
```

Add the necessary imports at the top of the file (Deliverable type for the return annotation).

### Step 2: Update `scripts/gui/pages/gantt_page.py`

**Replace `_shift_date()` prefix parsing:**
```python
def _shift_date(self, item_id: str, field: str, days: int) -> None:
    service = self.app.service
    if not service:
        return

    node = self.app.profile.find_by_id(item_id)
    if not node:
        return

    current = getattr(node, field, None)
    if not isinstance(current, date):
        return
    new_date = current + timedelta(days=days)

    prefix = item_id.split("-")[0].upper()
    if prefix == "T":
        service.edit_task(item_id, {field: new_date})
    elif prefix == "D":
        service.edit_deliverable(item_id, {field: new_date})
    self._render()
```

Note: The `prefix` check for dispatching to `edit_task()` vs `edit_deliverable()` still needs the prefix — but the node lookup is now centralized.

**Replace `_open_edit_dialog()` prefix parsing:**
```python
def _open_edit_dialog(self, item_id: str) -> None:
    node = self.app.profile.find_by_id(item_id)
    if not node:
        return
    # Use isinstance to dispatch to the right dialog
    from helpers.domain.task import Task
    from helpers.domain.deliverable import Deliverable
    if isinstance(node, Task):
        # ... open TaskDialog ...
    elif isinstance(node, Deliverable):
        # ... open DeliverableDialog ...
```

**Remove `_find_deliverable()`** — it's now handled by `find_by_id()`.

---

## Acceptance Criteria

1. `Profile.find_by_id()` exists and resolves P-NNN, T-NNN, D-NNN to the correct domain object
2. `find_by_id()` returns `None` for unknown IDs
3. `gantt_page.py` no longer has `_find_deliverable()` as a private method
4. ID prefix parsing (`item_id.split("-")[0]`) is minimized — only used where dispatch to different edit methods is needed
5. `pytest tests/` passes
6. `find_by_id()` has no UI, persistence, or schema dependencies (it only uses existing Profile methods)

---

## Constraints

- `find_by_id()` lives in `helpers/domain/profile.py` — pure domain layer
- Do NOT use `helpers/schema/ids.py::parse_id()` unless needed — a simple `split("-")[0]` is sufficient for routing
- The method does NOT need to be highly performant — it's called on user interactions (clicks, drags), not in loops
- Do NOT add `find_by_id()` to Project or Task — it's a Profile-level convenience method
- Some call sites still need the prefix for dispatch (e.g., `edit_task` vs `edit_deliverable`) — that's acceptable
