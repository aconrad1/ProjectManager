# Task 5: Replace Bare Excepts with Specific Exception Types

**Audit ID**: M-06, M-07  
**Effort**: Small  
**Phase**: 1 — Foundation

---

## Objective

Replace broad `except Exception: pass` blocks with specific exception types and error collection. In the batch dialog, collect errors and show a summary. In the config loader, catch specific JSON/IO exceptions only.

---

## Audit Reference

> **M-06: Bare Except Clauses Silently Swallow Errors in Batch Dialog**
>
> File: `scripts/gui/dialogs/batch_dialog.py` — three bare `except Exception: pass` blocks
> This pattern repeats 3 times (status, priority, date shifts). User has no idea which items failed or why.
>
> **M-07: Bare Except in Config Loader Catches SystemExit, KeyboardInterrupt**
>
> File: `helpers/config/loader.py` — `except Exception:` catches all errors including systemic ones.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/dialogs/batch_dialog.py` | **MODIFY** — collect errors, show summary |
| `helpers/config/loader.py` | **MODIFY** — catch `(json.JSONDecodeError, OSError)` specifically |

---

## Current Code

### batch_dialog.py — Three bare except blocks

**Block 1: Status update (line ~135)**
```python
for tid in self._task_ids:
    try:
        self._service.set_status(tid, status)
        changes += 1
    except Exception:
        pass
```

**Block 2: Priority update (line ~147)**
```python
for tid in self._task_ids:
    try:
        self._service.set_priority(tid, prio_int)
        changes += 1
    except Exception:
        pass
```

**Block 3: Date shift (line ~168)**
```python
for tid in self._task_ids:
    try:
        profile = self._service._profile
        task = profile.find_task_global(tid)
        # ... date shifting logic ...
        self._service.edit_task(tid, edits)
        changes += 1
    except Exception:
        pass
```

### loader.py — Broad except (line ~38)

```python
try:
    raw = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    if log:
        log("   ⚠ Config 'deadlines.json' is invalid JSON. Using defaults...")
    if auto_repair:
        path.write_text(json.dumps(DEFAULT_DEADLINE_WINDOWS, indent=4) + "\n", encoding="utf-8")
        load.cache_clear()
    return dict(DEFAULT_DEADLINE_WINDOWS)
```

---

## Required Changes

### Step 1: Fix batch_dialog.py — Collect errors and show summary

For each of the three loop blocks, replace `except Exception: pass` with error collection:

```python
errors: list[str] = []

# Status updates
if status:
    for tid in self._task_ids:
        try:
            self._service.set_status(tid, status)
            changes += 1
        except (ValueError, KeyError, AttributeError) as e:
            errors.append(f"{tid}: {e}")

# Priority updates
if prio_int is not None:
    for tid in self._task_ids:
        try:
            self._service.set_priority(tid, prio_int)
            changes += 1
        except (ValueError, KeyError, AttributeError) as e:
            errors.append(f"{tid}: {e}")

# Date shifts
if shift_start or shift_end or shift_deadline:
    profile = self._service.profile                  # Use public property (Task 3)
    for tid in self._task_ids:
        try:
            task = profile.find_task_global(tid)
            if not task:
                errors.append(f"{tid}: not found")
                continue
            # ... date shifting logic unchanged ...
            self._service.edit_task(tid, edits)
            changes += 1
        except (ValueError, KeyError, AttributeError) as e:
            errors.append(f"{tid}: {e}")
```

After all loops, show a summary if there were errors:

```python
if errors:
    error_summary = "\n".join(errors[:10])  # Cap at 10 to avoid huge dialogs
    if len(errors) > 10:
        error_summary += f"\n... and {len(errors) - 10} more"
    messagebox.showwarning(
        "Batch Edit Warnings",
        f"Updated {changes}/{len(self._task_ids)} items.\n\nFailed:\n{error_summary}",
        parent=self,
    )
```

### Step 2: Fix loader.py — Use specific exception types

Replace:
```python
except Exception:
```

With:
```python
except (json.JSONDecodeError, OSError):
```

This catches:
- `json.JSONDecodeError` — malformed JSON content
- `OSError` — file read failures (permissions, missing file, disk errors)

It does NOT catch `SystemExit`, `KeyboardInterrupt`, `MemoryError`, or other systemic exceptions that should propagate.

---

## Acceptance Criteria

1. No `except Exception: pass` blocks remain in `batch_dialog.py`
2. Each loop catches `(ValueError, KeyError, AttributeError)` — the specific exceptions that DomainService methods can raise
3. Errors are collected into a list and shown in a summary dialog after all operations complete
4. `loader.py` catches `(json.JSONDecodeError, OSError)` instead of `Exception`
5. `pytest tests/` passes — specifically `tests/gui/test_batch_dialog.py`
6. Successful batch operations still show the success count

---

## Constraints

- Do NOT change the batch edit behavior — items that succeed should still be applied even if others fail
- The error collection must not prevent remaining items from being processed (continue on failure)
- The exception types chosen must cover the realistic failure modes of DomainService methods (not found, invalid value, missing attribute)
- Do NOT introduce logging in batch_dialog.py — it's a UI component, the messagebox is sufficient
- The config loader's recovery behavior (auto-repair, defaults) stays unchanged — only the exception type changes
