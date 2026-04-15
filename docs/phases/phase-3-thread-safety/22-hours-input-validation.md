# Task 22: Show Validation Error for Invalid Hours Input

**Audit ID**: N-09  
**Effort**: Tiny  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

When a user enters an invalid value for `daily_hours_budget` (e.g., "abc"), show a validation error instead of silently defaulting to 8.0.

---

## Audit Reference

> **N-09: No Validation of daily_hours_budget Input**
>
> ```python
> try:
>     data[key] = float(val) if val else 8.0
> except ValueError:
>     data[key] = 8.0  # Silently defaults on invalid input
> ```
>
> User types "abc", silently gets 8.0 hours.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/pages/profile_page.py` | **MODIFY** — show validation error on invalid float input |

---

## Current Code

This pattern appears twice in profile_page.py:

**Profile save (line ~281–285):**
```python
if key == "daily_hours_budget":
    try:
        data[key] = float(val) if val else 8.0
    except ValueError:
        data[key] = 8.0
```

**Create dialog (line ~498–502):**
```python
if key == "daily_hours_budget":
    try:
        data[key] = float(val) if val else 8.0
    except ValueError:
        data[key] = 8.0
```

The same likely applies to `weekly_hours_budget`.

---

## Required Changes

Replace the silent default with a validation message:

```python
if key in ("daily_hours_budget", "weekly_hours_budget"):
    if not val:
        data[key] = 8.0 if key == "daily_hours_budget" else 40.0
    else:
        try:
            parsed = float(val)
            if parsed <= 0:
                raise ValueError("must be positive")
            data[key] = parsed
        except ValueError:
            default = 8.0 if key == "daily_hours_budget" else 40.0
            messagebox.showwarning(
                "Invalid Input",
                f"'{val}' is not a valid number for {key.replace('_', ' ')}.\n"
                f"Using default: {default}",
                parent=self,
            )
            data[key] = default
```

Apply this fix to both locations where the pattern appears.

Key changes:
1. Show a `messagebox.showwarning` when the value is invalid
2. Validate that the value is positive (0 or negative hours don't make sense)
3. Still fall back to the default — but the user knows their input was rejected
4. Handle both `daily_hours_budget` and `weekly_hours_budget`

---

## Acceptance Criteria

1. Entering "abc" for daily_hours_budget shows a warning dialog with the invalid value and the default
2. Entering a valid number (e.g., "6.5") works as before
3. Entering an empty string defaults silently (empty = use default is reasonable)
4. Entering 0 or negative numbers shows a warning
5. Both occurrences of the pattern are fixed
6. `pytest tests/` passes

---

## Constraints

- The default values (8.0 daily, 40.0 weekly) remain unchanged
- Empty input still defaults silently — only invalid non-empty input shows a warning
- Use `messagebox.showwarning` (not `showerror`) — it's a correctable input issue, not a crash
- Do NOT prevent the save from completing — apply the default and continue
