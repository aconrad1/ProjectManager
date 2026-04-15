# Task 6: Fix Typo in PDF Error Message

**Audit ID**: M-09  
**Effort**: Tiny  
**Phase**: 1 — Foundation

---

## Objective

Verify and fix the reported typo "repoert" → "report" in `helpers/reporting/pdf.py`. If the typo has already been fixed, mark this task as complete with no changes needed.

---

## Audit Reference

> **M-09: Typo in Error Message**
>
> File: `helpers/reporting/pdf.py` (line ~68)
>
> ```python
> raise FileNotFoundError("No Chrome or Edge browser found. Install chromium or use the Markdown repoert instead.")
> ```
>
> "repoert" → "report"

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/reporting/pdf.py` | **VERIFY** — check if typo exists; fix if present |

---

## Current Status

Recent exploration suggests the typo may have already been fixed. The current code reads:

```python
raise FileNotFoundError(
    "No Chrome or Edge browser found. Install chromium or use the Markdown report instead."
)
```

---

## Required Changes

1. Open `helpers/reporting/pdf.py`
2. Search for "repoert" — if found, replace with "report"
3. If not found, confirm the text reads "report" correctly and close with no changes

---

## Acceptance Criteria

1. The error message in `pdf.py` contains "report" (not "repoert")
2. No other changes to the file
3. `pytest tests/` passes

---

## Constraints

- This is a string-only fix — no logic changes
- If the typo is already fixed, this task requires zero file modifications
