# Phase 3: Thread Safety & Error Handling

**Purpose**: Fix thread safety issues, improve error handling, and add debouncing for expensive operations. These changes make the app more robust under real-world usage.

**Prerequisite**: Phase 1 (Foundation)

| # | Task | Audit ID | Effort | Files |
|---|------|----------|--------|-------|
| 15 | [Fix generate page thread safety](15-generate-page-thread-safety.md) | C-08 | Small | generate_page.py |
| 16 | [Add threading lock for generating flag](16-generating-flag-lock.md) | N-11 | Tiny | generate_page.py |
| 17 | [Debounce Gantt configure event](17-gantt-configure-debounce.md) | C-04 | Tiny | gantt_page.py |
| 18 | [Debounce external edit detection](18-external-edit-debounce.md) | C-10 | Small | app.py |
| 19 | [Improve autosave error handling](19-autosave-error-handling.md) | C-11 | Small | app.py |
| 20 | [Add error handling to cleanup task files](20-cleanup-task-files.md) | N-02 | Tiny | domain_service.py |
| 21 | [Log subprocess output on PDF failure](21-pdf-subprocess-logging.md) | M-08 | Tiny | pdf.py |
| 22 | [Show validation error for invalid hours](22-hours-input-validation.md) | N-09 | Tiny | profile_page.py |

## Ordering Notes

- Tasks 15 and 16 should be done together (both fix generate_page thread issues).
- Tasks 17–22 are fully independent.
- This phase can be worked in parallel with Phase 2.
