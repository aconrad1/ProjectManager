# Task 15: Fix Generate Page Thread Safety

**Audit ID**: C-08  
**Effort**: Small  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

Fix the thread safety issue where `generate_page.py` directly assigns `self.app.wb` and `self.app.profile` from a worker thread. All state updates must be marshaled back to the main thread using `self.after()`.

---

## Audit Reference

> **C-08: Report Generation Writes to App State from Worker Thread**
>
> ```python
> def run():
>     result = generate_reports(...)
>     self.app.wb = result["wb"]           # Direct assignment from thread
>     self.app.profile = result["profile"] # Direct assignment from thread
> ```
>
> Meanwhile, the autosave timer can fire and call `self.wb.save()` at the same time. No locking.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/pages/generate_page.py` | **MODIFY** — marshal state updates to main thread |

---

## Current Code (lines ~87–109)

```python
def _generate_reports(self):
    if self._generating:
        return
    self._generating = True
    self._log_clear()
    self.log_write("Starting report generation…\n")

    def run():
        try:
            from helpers.commands.report_pipeline import generate_reports
            result = generate_reports(log=self._log_after, today=date.today())
            self.app.wb = result["wb"]           # ← UNSAFE: from worker thread
            if "profile" in result:
                self.app.profile = result["profile"]  # ← UNSAFE: from worker thread
            tasks_page = self.app.pages.get("tasks")
            if tasks_page:
                self.after(0, tasks_page.refresh)
            self.after(0, lambda: messagebox.showinfo(
                "Complete", "Reports generated successfully!"))
        except Exception as e:
            self._log_after(f"\nERROR: {e}")
            self.after(0, lambda: messagebox.showerror(
                "Generation Failed", str(e)))
        finally:
            self._generating = False  # ← UNSAFE: from worker thread

    threading.Thread(target=run, daemon=True).start()
```

---

## Required Changes

### Marshal all state updates to the main thread via `self.after()`

```python
def _generate_reports(self):
    if self._generating:
        return
    self._generating = True
    self._log_clear()
    self.log_write("Starting report generation…\n")

    def run():
        try:
            from helpers.commands.report_pipeline import generate_reports
            result = generate_reports(log=self._log_after, today=date.today())
            # Marshal ALL state updates to the main thread
            self.after(0, lambda: self._apply_generation_result(result))
        except Exception as e:
            self._log_after(f"\nERROR: {e}")
            self.after(0, lambda: self._on_generation_failed(str(e)))

    threading.Thread(target=run, daemon=True).start()


def _apply_generation_result(self, result: dict) -> None:
    """Apply generation results on the main thread."""
    self.app.wb = result["wb"]
    if "profile" in result:
        self.app.profile = result["profile"]
    tasks_page = self.app.pages.get("tasks")
    if tasks_page:
        tasks_page.refresh()
    self._generating = False
    messagebox.showinfo("Complete", "Reports generated successfully!")


def _on_generation_failed(self, error_msg: str) -> None:
    """Handle generation failure on the main thread."""
    self._generating = False
    messagebox.showerror("Generation Failed", error_msg)
```

Key changes:
1. `self.app.wb` and `self.app.profile` are set inside `_apply_generation_result()`, which runs on the main thread
2. `self._generating = False` is set on the main thread in both success and failure paths
3. `tasks_page.refresh()` is called directly (no `self.after()` needed since we're already on the main thread)
4. The worker thread only calls `self.after()` to schedule main-thread callbacks

---

## Acceptance Criteria

1. `self.app.wb` and `self.app.profile` are never assigned from a worker thread
2. `self._generating` is never set to `False` from a worker thread
3. All state mutations happen on the main thread via `self.after(0, ...)`
4. Report generation still works end-to-end
5. The success/error dialogs still appear correctly
6. `pytest tests/gui/test_generate_page.py` passes

---

## Constraints

- The `generate_reports()` call itself must remain in the worker thread (it's I/O-heavy)
- `self._log_after()` is already thread-safe (it uses `self.after()` internally) — do not change it
- Do NOT add `threading.Lock` in this task — that's Task 16
- Keep the pattern simple: worker thread → `self.after(0, callback)` → main thread
