# Task 17: Debounce Gantt Canvas Configure Event

**Audit ID**: C-04 (partial)  
**Effort**: Tiny  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

Add debouncing to the Gantt page's `<Configure>` event binding so `_render()` is not called on every single resize pixel change. Use `after()` with a 100ms delay.

---

## Audit Reference

> **C-04: Gantt Page _render() Is 425 Lines**
>
> It's bound to `<Configure>`, so it runs on **every window resize**.
>
> Fix: Debounce the `<Configure>` binding with `after()` (e.g., 100ms delay).

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/pages/gantt_page.py` | **MODIFY** — debounce configure event |

---

## Current Code (line ~100)

```python
self._canvas.bind("<Configure>", lambda _: self._render())
```

This calls `_render()` immediately on every `<Configure>` event. During a window resize drag, this fires dozens of times per second, each triggering a full canvas redraw.

---

## Required Changes

Add a debounce mechanism using `after()`:

```python
# In __init__ or build():
self._render_after_id = None

# Replace the binding:
self._canvas.bind("<Configure>", self._on_configure)

# Add debounce method:
def _on_configure(self, event=None) -> None:
    """Debounced handler for canvas resize — delays render by 100ms."""
    if self._render_after_id is not None:
        self.after_cancel(self._render_after_id)
    self._render_after_id = self.after(100, self._render)
```

The slider and filter handlers can continue to call `_render()` directly — they're one-time events, not continuous. Or optionally they can also use the debounce.

---

## Acceptance Criteria

1. `_render()` is not called directly from `<Configure>` event
2. A 100ms debounce delay is applied (cancels pending render if a new configure event arrives)
3. The Gantt chart still renders correctly after window resize
4. Slider and filter changes still trigger a render (either directly or debounced)
5. `pytest tests/gui/test_gantt_page.py` passes

---

## Constraints

- Do NOT change `_render()` itself — only the event binding
- 100ms is the target delay — adjust if testing reveals visual lag
- The `after_cancel` / `after` pattern is standard tkinter debouncing
- Do NOT use threading for this — `after()` is the correct tkinter mechanism
