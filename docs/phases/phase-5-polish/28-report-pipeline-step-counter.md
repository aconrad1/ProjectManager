# Task 28: Add Step Counter to Report Pipeline Logging

**Audit ID**: M-10  
**Effort**: Tiny  
**Phase**: 5 — Polish

---

## Objective

Replace the manual `[1/9]`, `[2/9]`, etc. step numbering in the report pipeline with an auto-incrementing counter, so adding or removing steps doesn't require updating all subsequent numbers.

---

## Audit Reference

> **M-10: Report Pipeline Logging Uses Manual Step Numbering**
>
> ```python
> log("[1/9] Capturing previous snapshot...")
> log("[2/9] Detecting newly completed tasks...")
> ```
>
> If a step is added or removed, all subsequent numbers must be manually updated.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/commands/report_pipeline.py` | **MODIFY** — auto-increment step counter |

---

## Current Code (lines ~59–105)

```python
log("[1/9] Capturing previous snapshot for change history…")
# ...
log("[2/9] Processing completed tasks…")
# ...
log("[3/9] Syncing domain hierarchy…")
# ...
log("[4/9] Running daily scheduler…")
# ...
log("[5/9] Writing Overview tab…")
# ...
log("[6/9] Checking Timelines integrity & syncing derived sheets…")
# ...
log("[7/9] Saving workbook & domain.json…")
# ...
```

---

## Required Changes

Add a simple step counter class or closure:

```python
def generate_reports(log=None, today=None):
    # ...
    
    total_steps = 9
    _step = 0
    
    def step(msg: str) -> None:
        nonlocal _step
        _step += 1
        if log:
            log(f"[{_step}/{total_steps}] {msg}")
    
    step("Capturing previous snapshot for change history…")
    # ...
    step("Processing completed tasks…")
    # ...
    step("Syncing domain hierarchy…")
    # ...
```

Or alternatively, define steps as a list upfront:

```python
PIPELINE_STEPS = [
    "Capturing previous snapshot for change history…",
    "Processing completed tasks…",
    "Syncing domain hierarchy…",
    "Running daily scheduler…",
    "Writing Overview tab…",
    "Checking Timelines integrity & syncing derived sheets…",
    "Saving workbook & domain.json…",
    # ... etc.
]
```

Either approach eliminates manual numbering.

---

## Acceptance Criteria

1. Step numbers auto-increment — no hardcoded `[1/9]`, `[2/9]` etc.
2. The total count reflects the actual number of steps
3. Log output looks identical to before: `[1/9] Capturing previous snapshot…`
4. Adding or removing a step only requires changing one place (the step definition or increments)
5. `pytest tests/test_phase3_reporting.py` passes

---

## Constraints

- Keep the logging format identical: `[N/M] message`
- Do NOT change what the pipeline does — only how it logs progress
- The `log` callback signature stays the same: `log(message: str) -> None`
- Keep it simple — a closure or counter variable, not a pipeline framework
