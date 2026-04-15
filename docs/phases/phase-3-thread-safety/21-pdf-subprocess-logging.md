# Task 21: Log Subprocess Output on PDF Generation Failure

**Audit ID**: M-08  
**Effort**: Tiny  
**Phase**: 3 — Thread Safety & Error Handling

---

## Objective

When Chrome/headless PDF generation fails, log the captured stderr output so users and developers can diagnose the failure. Currently, `capture_output=True` captures output but it's never inspected.

---

## Audit Reference

> **M-08: PDF Generation Discards subprocess Output**
>
> ```python
> subprocess.run([chrome, "--headless", ...], check=True, capture_output=True, timeout=30)
> ```
>
> `capture_output=True` captures stdout/stderr, but neither is logged or returned.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/reporting/pdf.py` | **MODIFY** — catch CalledProcessError, log stderr |

---

## Current Code (lines ~69–79)

```python
subprocess.run(
    [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={dest}",
        "--print-to-pdf-no-header",
        tmp_html,
    ],
    check=True,
    capture_output=True,
    timeout=30,
)
```

---

## Required Changes

```python
import logging
import subprocess

_log = logging.getLogger(__name__)

try:
    result = subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={dest}",
            "--print-to-pdf-no-header",
            tmp_html,
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
except subprocess.CalledProcessError as e:
    stderr = e.stderr.decode(errors="replace") if e.stderr else "(no output)"
    _log.error("PDF generation failed (exit code %d): %s", e.returncode, stderr)
    raise RuntimeError(
        f"PDF generation failed (Chrome exit code {e.returncode}).\n{stderr}"
    ) from e
except subprocess.TimeoutExpired:
    _log.error("PDF generation timed out after 30 seconds")
    raise RuntimeError("PDF generation timed out after 30 seconds.")
```

Key changes:
1. Assign the result to a variable (for potential future logging of warnings)
2. Catch `subprocess.CalledProcessError` — decode and log stderr
3. Catch `subprocess.TimeoutExpired` — log a clear timeout message
4. Re-raise as `RuntimeError` with the stderr content for the caller to display

---

## Acceptance Criteria

1. On failure, Chrome's stderr output is logged via `logging.error`
2. The re-raised exception includes the stderr content in its message
3. Timeout failures get a clear, descriptive error message
4. Successful PDF generation is unaffected
5. `pytest tests/` passes

---

## Constraints

- Do NOT change the subprocess arguments
- Use `errors="replace"` when decoding stderr (Chrome may output non-UTF-8 bytes)
- Re-raise as `RuntimeError` so the caller's generic error handling can display it
- Do NOT add Chrome installation logic or fallback browsers
