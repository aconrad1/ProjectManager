# Phase 2: Separation of Concerns

**Purpose**: Extract business logic from UI pages into testable helper modules. These changes decouple data computation from widget rendering.

**Prerequisite**: Phase 1 (Foundation)

| # | Task | Audit ID | Effort | Files |
|---|------|----------|--------|-------|
| 7 | [Extract dashboard statistics](07-dashboard-statistics.md) | C-05 | Medium | dashboard_page.py, 1 new |
| 8 | [Extract category filtering helper](08-category-filtering.md) | N-08 | Small | 3 pages, 1 new |
| 9 | [Extract Gantt data preparation](09-gantt-data-prep.md) | C-04 | Medium | gantt_page.py, gantt.py |
| 10 | [Create RowReader for workbook cell access](10-row-reader-accessor.md) | C-13 | Medium | task_ops.py, 1 new |
| 11 | [Break tasks_page build() into methods](11-tasks-page-build.md) | C-06 | Medium | tasks_page.py |
| 12 | [Extract tasks_page filtering logic](12-tasks-page-populate-tree.md) | C-07 | Medium | tasks_page.py, 1 new |
| 13 | [Centralize color mappings](13-centralize-colors.md) | N-07 | Small | 3–4 pages, ui_theme.py |
| 14 | [Add find_by_id() to Profile](14-find-by-id.md) | M-05 | Small | profile.py, gantt_page.py |

## Ordering Notes

- Tasks 7–14 are largely independent and can be done in any order.
- Task 8 (category filtering) and Task 12 (tasks_page filtering) are related — do 8 first, then use it in 12.
- Task 13 (colors) is cosmetic — can be deferred if needed.
- Task 10 (RowReader) is foundational for future workbook refactors.
