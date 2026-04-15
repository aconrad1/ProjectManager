# Task 16: Add Threading Lock for Generating Flag

**Audit ID**: N-11  
**Effort**: Tiny  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

Replace the bare `self._generating` boolean flag with a `threading.Event` (or protect it with a `threading.Lock`) to eliminate the race condition between the main thread and the worker thread.

---

## Audit Reference

> **N-11: generate_page Thread Sets `_generating` Flag Without Lock**
>
> ```python
> self._generating = True   # Set on main thread
> # ...in worker thread:
> self._generating = False  # Set from worker thread — race condition
> ```

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/pages/generate_page.py` | **MODIFY** — use `threading.Event` for generating state |

---

## Current Code

```python
# In __init__ or build():
self._generating = False

# In _generate_reports():
if self._generating:
    return
self._generating = True

# In worker thread (or after Task 15, in _apply_generation_result):
self._generating = False
```

---

## Required Changes

Replace `self._generating` with `threading.Event`:

```python
import threading

# In __init__ or build():
self._gen_event = threading.Event()  # Not set = not generating

# In _generate_reports():
if self._gen_event.is_set():
    return
self._gen_event.set()

# In _apply_generation_result() (main thread, after Task 15):
self._gen_event.clear()

# In _on_generation_failed() (main thread, after Task 15):
self._gen_event.clear()
```

`threading.Event` is thread-safe by design — `set()`, `clear()`, and `is_set()` are all atomic.

Update any other references to `self._generating` to use `self._gen_event.is_set()`.

---

## Acceptance Criteria

1. No bare `self._generating` boolean access remains
2. `threading.Event` (or `threading.Lock`) protects the generating state
3. Double-clicking "Generate" while generation is running is prevented
4. `pytest tests/gui/test_generate_page.py` passes

---

## Constraints

- If Task 15 has been completed, the flag is already set on the main thread — the Event is still cleaner
- If Task 15 has NOT been completed, this change provides additional safety for the cross-thread access
- `threading.Event` is preferred over `threading.Lock` because the semantics match: "is generation in progress?"
- Do NOT use `asyncio` — the app uses threading, not async/await
