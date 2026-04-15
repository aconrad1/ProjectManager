# Phase 1: Foundation

**Purpose**: Small, safe changes that unblock all subsequent phases. Complete these first.

| # | Task | Audit ID | Effort | Files |
|---|------|----------|--------|-------|
| 1 | [Extract shared dialog base class](01-shared-dialog-base.md) | M-03 | Small | 3 dialogs + 1 new |
| 2 | [Extract duplicate project completion logic](02-project-completion-logic.md) | C-03 | Small | domain_service.py, task_ops.py, 1 new |
| 3 | [Fix batch dialog private member access](03-batch-dialog-private-access.md) | C-09 | Tiny | batch_dialog.py |
| 4 | [Add public rebuild_sidebar() to App](04-app-rebuild-sidebar.md) | M-11 | Tiny | app.py, profile_page.py |
| 5 | [Replace bare excepts with specific types](05-specific-exception-types.md) | M-06, M-07 | Small | batch_dialog.py, loader.py |
| 6 | [Fix typo in pdf.py error message](06-pdf-typo-fix.md) | M-09 | Tiny | pdf.py |

## Ordering Notes

- Tasks 1–6 are independent and can be completed in any order.
- Each task is independently committable.
- Run `pytest tests/` after each change.
