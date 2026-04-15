# Task 20: Add Error Handling to `_cleanup_task_files()`

**Audit ID**: N-02  
**Effort**: Tiny  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

Add error handling to `_cleanup_task_files()` so that a failure to delete one attachment type (notes, links, or files) doesn't prevent the others from being cleaned up. Log any errors.

---

## Audit Reference

> **N-02: _cleanup_task_files Has No Error Handling**
>
> ```python
> @staticmethod
> def _cleanup_task_files(task_id: str) -> None:
>     delete_notes(task_id)    # If this fails...
>     delete_link(task_id)     # ...these still run, but caller doesn't know
>     delete_attachments(task_id)
> ```

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/commands/domain_service.py` | **MODIFY** — wrap each cleanup call in try/except |

---

## Current Code (lines ~376–380)

```python
@staticmethod
def _cleanup_task_files(task_id: str) -> None:
    """Remove notes, links, and attachments associated with a task ID."""
    delete_notes(task_id)
    delete_link(task_id)
    delete_attachments(task_id)
```

---

## Required Changes

```python
import logging

_log = logging.getLogger(__name__)

@staticmethod
def _cleanup_task_files(task_id: str) -> None:
    """Remove notes, links, and attachments associated with a task ID."""
    for label, fn in [
        ("notes", delete_notes),
        ("link", delete_link),
        ("attachments", delete_attachments),
    ]:
        try:
            fn(task_id)
        except OSError as e:
            _log.warning("Failed to clean up %s for %s: %s", label, task_id, e)
```

Key changes:
1. Each cleanup call is independently wrapped in try/except
2. A failure in one doesn't prevent the others from running
3. Errors are logged with a descriptive message
4. Only `OSError` is caught (file I/O errors) — not broad `Exception`

---

## Acceptance Criteria

1. Each of the three cleanup calls runs independently
2. A failure in `delete_notes()` doesn't prevent `delete_link()` or `delete_attachments()`
3. Errors are logged via `logging.warning`
4. The overall task/project deletion succeeds even if cleanup fails
5. `pytest tests/` passes

---

## Constraints

- Catch `OSError` specifically (not `Exception`)
- Do NOT raise or re-raise — cleanup failures are non-fatal
- Do NOT show a UI dialog — this runs in the helpers layer
- The `_log` logger should already exist in domain_service.py; if not, add it
