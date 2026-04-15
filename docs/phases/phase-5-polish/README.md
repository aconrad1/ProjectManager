# Phase 5: Polish

**Purpose**: Cleanup, deduplication, and test coverage improvements. These are lower-priority items that improve maintainability without changing core behavior.

**Prerequisite**: Phases 1–3 (foundation, separation, and safety work)

| # | Task | Audit ID | Effort | Files |
|---|------|----------|--------|-------|
| 26 | [Extract attachment migration helper](26-attachment-migration-helper.md) | M-04 | Small | notes.py, links.py, service.py |
| 27 | [Refactor sync_timelines to table-driven](27-sync-timelines-refactor.md) | N-04 | Medium | timelines.py |
| 28 | [Add step counter to report pipeline](28-report-pipeline-step-counter.md) | M-10 | Tiny | report_pipeline.py |
| 29 | [Add all_deliverables property to Profile](29-all-deliverables-property.md) | N-03 | Tiny | profile.py, workbook_writer.py |
| 30 | [Add tests for portability and cascade delete](30-portability-cascade-tests.md) | N-12 | Medium | 2 new test files |

## Ordering Notes

- All tasks are independent — work in any order.
- Task 29 is the simplest (tiny property addition).
- Task 30 (tests) is best done after Phases 1–3 stabilize the codebase.
