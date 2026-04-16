# Architecture Audit Report

**Date**: April 15, 2026  
**Scope**: Full codebase — `helpers/`, `scripts/`, `tests/`  
**Purpose**: Identify legacy code architecture issues to work through incrementally before expanding features.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What's Working Well](#whats-working-well)
3. [Critical Issues](#critical-issues)
4. [Major Issues](#major-issues)
5. [Medium Issues](#medium-issues)
6. [Minor Issues](#minor-issues)
7. [Test Coverage Gaps](#test-coverage-gaps)
8. [Dependency Map Summary](#dependency-map-summary)
9. [Prioritized Fix List](#prioritized-fix-list)

---

## Executive Summary

The codebase has **strong architectural foundations**: clean domain model isolation, no import inversions (helpers never imports scripts), no circular dependencies, and a proper layered stack (domain → schema → persistence → commands → UI). The plugin-style page registry and command registry are well-designed.

However, **six categories of debt** undermine maintainability as the project scales:

| Category | Critical | Major | Medium | Total |
|----------|----------|-------|--------|-------|
| Global mutable state | 2 | 1 | 1 | 4 |
| Oversized functions | 4 | 2 | 3 | 9 |
| Code duplication | 2 | 3 | 2 | 7 |
| Error handling | 2 | 3 | 2 | 7 |
| Tight coupling / layer violations | 3 | 2 | 3 | 8 |
| Thread safety / UI blocking | 3 | 1 | 1 | 5 |
| **Total** | **16** | **12** | **12** | **40** |

---

## What's Working Well

These patterns should be **preserved and extended** as the codebase grows.

### Domain Model (helpers/domain/)
- Pure dataclasses with no UI or persistence dependencies.
- Zero internal imports beyond `base.py`. A true leaf module.
- `Profile → Project → Task → Deliverable` hierarchy is clean and well-defined.

### Schema Layer (helpers/schema/)
- Also a leaf module — no internal dependencies.
- All column definitions, sheet names, and ID patterns live here.
- One-way dependency: everything reads from schema, nothing writes to it.

### Plugin-Style Architecture
- **Page registry** (`page_registry.py`): Adding a page requires no changes to `app.py`.
- **Command registry** (`registry.py`): CLI commands are `@register`-decorated, decoupled from argparse.
- **DomainService as mutation authority**: All GUI mutations route through one service.

### JSON-First Data Layer
- `domain.json` is canonical. Workbook is a rendered artifact.
- `contract.py` orchestrates the dual-write pattern cleanly.
- Hash-based sync detection for external workbook edits.

### Import Architecture
- **No inversions**: `helpers/` never imports from `scripts/`.
- **No circular chains**: All dependencies are acyclic.
- **GUI pages are mostly clean**: Import from domain + attachments, not from persistence or schema directly.

---

## Critical Issues

### C-01: Profile Module Uses 11 Global Variables Mutated at Runtime

**Files**: `helpers/profile/profile.py` (lines 47–56, 82, 95–97)  
**Impact**: Every module importing these holds stale values until `reload()` is called. Tests cannot run in parallel. No thread safety.

```python
# 11 globals mutated by _apply_profile()
USER_NAME: str = ""
USER_ROLE: str = ""
USER_COMPANY: str = ""
USER_EMAIL: str = ""
USER_PHONE: str = ""
RECIPIENT_NAME: str = ""
RECIPIENT_EMAIL: str = ""
WORKBOOK_FILENAME: str = ""
DAILY_HOURS_BUDGET: float = 8.0
WEEKLY_HOURS_BUDGET: float = 40.0
```

**Consumers** (all hold potentially stale references):
- `helpers/commands/report_pipeline.py` — imports all 10+ USER_* globals
- `helpers/commands/utilities.py` — imports USER_NAME, RECIPIENT_NAME, RECIPIENT_EMAIL
- `helpers/profile/config.py` — wraps globals in functions but still couples to module state
- `scripts/gui/app.py` — accesses via `_prof.USER_COMPANY`
- `scripts/gui/pages/settings_page.py` — accesses via `_prof.USER_NAME`
- `scripts/cli/run.py` — imports all USER_* globals at top level

**Fix**: Replace with a `ProfileConfig` dataclass or frozen NamedTuple. Functions receive it via parameter injection rather than importing globals. A `get_active_config() → ProfileConfig` function returns the current snapshot.

---

### C-02: Profile Module Runs Code at Import Time

**File**: `helpers/profile/profile.py` (lines 95–97)

```python
# ── Initialise on import ──────────────────────────────────────────────────
_profiles, _active_index = _load_profiles()
_apply_profile(_active_index)
```

**Impact**: Any module that imports from `helpers.profile.profile` triggers file I/O (YAML read) and global mutation. If the YAML file is missing, the process calls `sys.exit(1)` — a hard exit with no recovery possible.

**Fix**: Defer initialization. Provide an explicit `init()` or `ensure_loaded()` function. Entry points (`cli.py`, `gui.py`) call it once at startup.

---

### C-03: Duplicate Project Auto-Completion Logic

**Location 1**: `helpers/commands/domain_service.py` (lines 342–363) — `_check_project_completion()`  
**Location 2**: `helpers/commands/task_ops.py` (lines 245–293) — `_check_project_completion_wb()`

Both implement the same business rule: "if all tasks under a project are Completed, auto-complete the parent project; if a task is reopened under a Completed project, revert the project to Ongoing."

The domain_service version operates on domain objects (22 lines). The task_ops version does the same thing by navigating workbook cells (49 lines).

**Fix**: Extract the pure business logic into a shared function:

```python
# helpers/domain/rules.py
def should_auto_complete_project(task_statuses: list[str]) -> bool:
    return all(s.strip().lower() == "completed" for s in task_statuses)
```

Both `domain_service` and `task_ops` call this function, then apply the result to their respective data stores.

---

### C-04: Gantt Page _render() Is 425 Lines

**File**: `scripts/gui/pages/gantt_page.py` (lines 155–580)

A single method that:
1. Computes date ranges from the profile
2. Builds row data (filtering by category)
3. Configures the canvas
4. Draws month labels, week ticks, today line
5. Draws row backgrounds and labels
6. Draws bars with progress overlays
7. Draws deadline markers and grid dividers

And it's bound to `<Configure>`, so it runs on **every window resize**.

**Fix**:
- Extract data preparation into `helpers/reporting/gantt.py`: `compute_gantt_rows(profile, category_filter)`, `compute_date_range(rows)`.
- Extract canvas drawing into helper methods: `_draw_header()`, `_draw_rows()`, `_draw_bars()`.
- Debounce the `<Configure>` binding with `after()` (e.g., 100ms delay).

---

### C-05: Dashboard refresh() Is 220 Lines of Stats + UI

**File**: `scripts/gui/pages/dashboard_page.py` (lines 65–285)

Computes priority breakdowns (`Counter`), site distributions, recently completed items, and top-priority tasks — then immediately renders widgets for each. Business logic and UI creation are interleaved.

**Fix**: Extract statistics computation into `helpers/data/dashboard.py`:

```python
def compute_priority_breakdown(tasks) -> dict[int, tuple[int, float]]: ...
def compute_site_distribution(tasks, top_n=8) -> list[tuple[str, int]]: ...
def compute_recently_completed(tasks, limit=5) -> list[Task]: ...
```

The page calls these functions and only handles widget creation.

---

### C-06: Tasks Page build() Creates 50+ Widgets in 145 Lines

**File**: `scripts/gui/pages/tasks_page.py` (lines 40–185)

Single function creates the header, filter bar, treeview with column configuration, styling, two button rows, a right-click context menu with 30+ items, drag-and-drop setup, and status bar.

**Fix**: Break into `_build_filters()`, `_build_treeview()`, `_build_buttons()`, `_build_context_menu()`.

---

### C-07: Tasks Page _populate_tree() Is 170 Lines

**File**: `scripts/gui/pages/tasks_page.py` (lines 264–440)

Nested loops (project → task → deliverable) with filtering, searching, tree building, indexing, and rendering mixed together.

**Fix**: Extract filtering into a helper (`filter_projects_and_tasks(profile, category, search_term)`) and keep only tree-widget insertion in the page.

---

### C-08: Thread Safety — Report Generation Writes to App State from Worker Thread

**File**: `scripts/gui/pages/generate_page.py` (lines 140–165)

```python
def run():
    result = generate_reports(...)
    self.app.wb = result["wb"]           # Direct assignment from thread
    self.app.profile = result["profile"] # Direct assignment from thread
```

Meanwhile, the autosave timer (`app.py` line 235) can fire and call `self.wb.save()` at the same time. No locking.

**Fix**: Use `self.after(0, lambda: self._apply_result(result))` to marshal all state updates back to the main thread. Add a `threading.Lock` around `self.wb` access in the autosave path.

---

### C-09: Batch Dialog Accesses Private `_service._profile`

**File**: `scripts/gui/dialogs/batch_dialog.py` (line 159)

```python
profile = self._service._profile  # DIRECT ACCESS TO PRIVATE MEMBER
```

**Fix**: Add a public property to DomainService: `@property def profile(self) -> Profile: return self._profile`. Or pass the profile as a parameter to the dialog.

---

### C-10: External Edit Detection Runs on Every Window Focus

**File**: `scripts/gui/app.py` (lines 485–510)

Every time the window regains focus:
1. Reads the workbook file from disk
2. Computes SHA-256 hash
3. Compares to stored hash
4. Shows a messagebox if changed

SHA-256 of a workbook can be expensive. The messagebox blocks the UI thread. Focus events fire frequently (alt-tabbing, clicking, etc.).

**Fix**: Debounce the check (e.g., at most once per 5 seconds). Move hash computation to a background thread. Use a non-blocking notification instead of `messagebox`.

---

### C-11: Autosave Silently Swallows Failures

**File**: `scripts/gui/app.py` (lines 235–248)

```python
def _autosave(self) -> None:
    if self.wb:
        try:
            self.wb.save(str(workbook_path()))
            self._update_save_indicator("Autosaved")
        except Exception:
            self._update_save_indicator("Autosave failed")  # User sees this briefly, then it's gone
```

**Fix**: Log the exception. If autosave fails repeatedly (e.g., 3 times), show a persistent warning. Consider writing to a temp file first, then renaming (atomic write).

---

### C-12: DomainService Mixes Validation, Mutation, Cascade, and File Cleanup

**File**: `helpers/commands/domain_service.py` (406 lines total)

The class handles:
- Input validation (via `_validate_or_raise`)
- Domain object creation (constructing Project/Task/Deliverable)
- Persistence triggering (`_persist()`)
- Cascade deletion (removing child tasks + deliverables)
- Auto-completion logic (parent project status changes)
- File cleanup (deleting notes, links, attachments)

**Fix**: This doesn't need to be split into many classes, but the auto-completion logic and file cleanup should be extracted into named helper functions/modules. The cascade rules are business logic that should be independently testable.

---

### C-13: task_ops Module Does Cell-Level Workbook Navigation (357 Lines)

**File**: `helpers/commands/task_ops.py`

Repeatedly uses `ws.cell(row=r, column=col_idx).value` with manual `column_index() + 1` calculations. No abstraction layer for reading/writing workbook cells.

**Fix**: Create a thin `WorkbookAccessor` or `RowReader` helper:

```python
class RowReader:
    def __init__(self, ws, columns):
        self.ws = ws
        self.col_map = {c.name: i+1 for i, c in enumerate(columns)}
    
    def get(self, row: int, field: str) -> Any:
        return self.ws.cell(row=row, column=self.col_map[field]).value
    
    def set(self, row: int, field: str, value: Any) -> None:
        self.ws.cell(row=row, column=self.col_map[field]).value = value
```

Both `task_ops.py` and `workbook_writer.py` can use this.

---

### C-14: Persistence Layer Hard-Imports Schema Definitions

**Files**: `helpers/persistence/workbook_reader.py` (lines 10–12), `helpers/persistence/workbook_writer.py` (lines 11–15)

```python
from helpers.schema.sheets import (SHEET_PROJECTS, SHEET_TASKS, SHEET_DELIVERABLES)
from helpers.schema.columns import (PROJECTS_COLUMNS, TASKS_COLUMNS, DELIVERABLES_COLUMNS, column_index)
```

Any change to column definitions, ordering, or sheet names requires updating persistence code.

**Fix**: This coupling is somewhat expected in the current architecture, but could be improved by passing schema definitions as parameters to reader/writer functions rather than importing them directly. This would make persistence functions more testable and reusable.

---

### C-15: Migration Runs Silently on Every Profile Load

**File**: `helpers/persistence/contract.py` (lines 185–187)

```python
from helpers.migration import migrate_to_id_keying
migrate_to_id_keying(profile)
```

Every call to `load_profile()` triggers migration, which loads/saves JSON files from disk. No logging, no confirmation.

**Fix**: Check a migration version flag in `domain.json` metadata. If already migrated (version >= 2.0), skip. Log when migration actually runs.

---

### C-16: File I/O Blocks the UI Thread in Multiple Places

**Files**:
- `scripts/gui/pages/tasks_page.py` (line 669) — `filedialog.askopenfilenames()` + `attach_files()`
- `scripts/gui/pages/tasks_page.py` (line 729) — `filedialog.askdirectory()` + `set_link()`
- `scripts/gui/pages/tasks_page.py` (line 775) — `_on_drop_files()` copies files synchronously
- `scripts/gui/pages/profile_page.py` (line 363) — `filedialog.askopenfilename()` for workbook import

The file dialog itself is fine (it's modal and expected to block), but the file operations after selection (copying, linking) happen on the main thread and can freeze the window for large files.

**Fix**: Run file copy operations in a background thread with a progress indicator. Use `self.after()` to update the UI when complete.

---

## Major Issues

### M-01: Post-Mutate Hook Uses a Module-Level Global

**File**: `helpers/commands/task_ops.py` (lines 35–48)

```python
_post_mutate = None

def set_post_mutate_hook(fn) -> None:
    global _post_mutate
    _post_mutate = fn
```

Called from 10+ mutation functions. Must be explicitly set by the CLI before using task_ops.

**Fix**: Accept the callback as a parameter to `task_ops` functions, or use a simple event bus pattern.

---

### M-02: Scheduler compute_schedule() Is 132 Lines with 3-Level Nested Loops

**File**: `helpers/scheduling/engine.py` (lines 115–246)

Tracks state across 4 dictionaries (`schedule`, `day_hours`, `week_hours`, `slot_count`) with a safety counter to prevent infinite loops — a sign that the loop termination condition is unclear.

**Fix**: Extract `_find_next_available_slot()` and `_allocate_hours_to_day()` as named functions. Document the invariants of the state machine.

---

### M-03: Dialog Helper Methods Duplicated Across 3 Files

**Files**: `scripts/gui/dialogs/task_dialog.py`, `project_dialog.py`, `deliverable_dialog.py`

All three independently implement:
- `_get(key)` — read value from entry/textbox/optionmenu widget
- `_parse_date(key)` — parse YYYY-MM-DD from entry widget
- Button frame layout (Save + Cancel buttons with identical styling)

**Fix**: Create a `BaseDialog` class in `scripts/gui/dialogs/` with these shared methods. All three dialogs inherit from it.

---

### M-04: Attachment Migration Logic Nearly Identical in 3 Files

**Files**: `helpers/attachments/notes.py` (~10 lines), `links.py` (~12 lines), `service.py` (~17 lines)

Each `migrate_*()` function: loads data → checks if keys match ID regex → remaps title keys to ID keys → saves.

**Fix**: Extract the common pattern into a generic `migrate_keyed_store(load_fn, save_fn, title_to_id)` function.

---

### M-05: pages/gantt_page.py — Direct ID Prefix Parsing

**File**: `scripts/gui/pages/gantt_page.py` (lines 567–580)

```python
prefix = item_id.split("-")[0] if "-" in item_id else ""
if prefix == "T":
    node = self.app.profile.find_task_global(item_id)
elif prefix == "D":
    node = self._find_deliverable(item_id)
```

The page is parsing the ID format directly, coupling it to the ID naming scheme.

**Fix**: Use a helper in `helpers/schema/ids.py` (or the domain model itself) to resolve an item by any ID type:

```python
# helpers/domain/profile.py
def find_by_id(self, item_id: str) -> Node | None:
    """Resolve P-NNN, T-NNN, or D-NNN to the corresponding domain object."""
```

---

### M-06: Bare Except Clauses Silently Swallow Errors in Batch Dialog

**File**: `scripts/gui/dialogs/batch_dialog.py` (lines 148–162)

```python
for tid in self._task_ids:
    try:
        self._service.set_status(tid, status)
        changes += 1
    except Exception:
        pass  # User has no idea which items failed or why
```

This pattern repeats 3 times in the same method (status, priority, date shifts).

**Fix**: Collect errors into a list. After the loop, show a summary: "Updated 8/10 tasks. 2 failed: T-003 (invalid status), T-007 (not found)."

---

### M-07: Bare Except in Config Loader Catches SystemExit, KeyboardInterrupt

**File**: `helpers/config/loader.py` (lines 59–76)

```python
except Exception:  # Catches all errors including systemic ones
    if log:
        log("   ⚠ Config 'deadlines.json' is invalid JSON. Using defaults...")
```

**Fix**: Catch `(json.JSONDecodeError, OSError)` specifically.

---

### M-08: PDF Generation Discards subprocess Output

**File**: `helpers/reporting/pdf.py` (lines 71–87)

```python
subprocess.run([chrome, "--headless", ...], check=True, capture_output=True, timeout=30)
```

`capture_output=True` captures stdout/stderr, but neither is logged or returned. If PDF generation fails, the user gets an unhelpful Python exception.

**Fix**: On failure, log `result.stderr.decode()` and include it in the error message.

---

### M-09: Typo in Error Message

**File**: `helpers/reporting/pdf.py` (line ~68)

```python
raise FileNotFoundError("No Chrome or Edge browser found. Install chromium or use the Markdown repoert instead.")
```

"repoert" → "report"

---

### M-10: Report Pipeline Logging Uses Manual Step Numbering

**File**: `helpers/commands/report_pipeline.py` (lines 30–110)

```python
log("[1/9] Capturing previous snapshot...")
log("[2/9] Detecting newly completed tasks...")
```

If a step is added or removed, all subsequent numbers must be manually updated.

**Fix**: Use an auto-incrementing step counter or a pipeline abstraction.

---

### M-11: Profile Page Calls Private App Methods

**File**: `scripts/gui/pages/profile_page.py` (lines 193, 216)

```python
self.app._build_sidebar()  # Private method
self.app.reload_data()
```

**Fix**: Add `rebuild_sidebar()` as a public method on the App class, or expose it through the `AppContext` protocol.

---

### M-12: Scheduler Page Imports Engine Functions Directly

**File**: `scripts/gui/pages/scheduler_page.py`

```python
from helpers.scheduling.engine import compute_schedule, daily_hours, week_start_date
```

The page calls scheduling engine functions directly and transforms the result into a grid in its render method.

**Fix**: The scheduling engine should provide a `grid_from_schedule()` helper and an `over_capacity_days()` helper so the page doesn't need to transform the data.

---

## Medium Issues

### N-01: Config Loader LRU Cache Never Invalidated

**File**: `helpers/config/loader.py` (lines 31–39)

`@lru_cache(maxsize=32)` on `load()` means config changes on disk are invisible until process restart (or manual `load.cache_clear()` call).

**Fix**: Either document this clearly or add a `reload_config()` function that clears the cache.

---

### N-02: _cleanup_task_files Has No Error Handling

**File**: `helpers/commands/domain_service.py` (lines 364–368)

```python
@staticmethod
def _cleanup_task_files(task_id: str) -> None:
    delete_notes(task_id)    # If this fails...
    delete_link(task_id)     # ...these still run, but caller doesn't know
    delete_attachments(task_id)
```

**Fix**: Wrap each in try/except, collect errors, log them. The overall delete should still succeed even if cleanup fails.

---

### N-03: Workbook Writer Uses Triple-Nested List Comprehension

**File**: `helpers/persistence/workbook_writer.py` (line 118)

```python
[d for p in profile.projects for t in p.tasks for d in t.deliverables]
```

Hard to read. Recalculated on every save.

**Fix**: Add an `all_deliverables` property to `Profile`.

---

### N-04: sync_timelines() Is 140 Lines of Repetitive Formula Building

**File**: `helpers/schema/timelines.py` (lines 43–182)

The same VLOOKUP pattern repeats 3 times (Projects, Tasks, Deliverables) with minor variations.

**Fix**: Extract into a loop or table-driven approach:

```python
SECTIONS = [
    ("Project", proj_ws, proj_range, PROJ_FIELD_MAP),
    ("Task", task_ws, task_range, TASK_FIELD_MAP),
    ("Deliverable", deliv_ws, deliv_range, DELIV_FIELD_MAP),
]
for label, ws, range_, fields in SECTIONS:
    _write_section(timeline_ws, row, label, ws, range_, fields)
```

---

### N-05: Workbook Writer Deletes All Rows Then Rewrites

**File**: `helpers/persistence/workbook_writer.py` (lines 119–121)

Every save clears all data rows and rewrites from scratch. Acceptable for now given the data size, but becomes a concern with larger datasets.

**Fix**: Not urgent. If performance becomes an issue, implement delta writes (identify changed rows, update in-place).

---

### N-06: AppContext Protocol Uses `Any` for Workbook

**File**: `scripts/gui/base_page.py` (lines 11–25)

```python
class AppContext(Protocol):
    wb: Any  # Should be Workbook | None
```

**Fix**: Type as `Workbook | None`. Document which methods are safe to call when `wb is None`.

---

### N-07: Status/Priority Color Mapping Duplicated Across Pages

**Files**: `gantt_page.py`, `dashboard_page.py`, `scheduler_page.py`

Each page independently maps priorities to colors or statuses to colors. Some use `ui_theme.py`, others hardcode values.

**Fix**: Centralize all color mappings in `ui_theme.py`. Pages should only read from there.

**Partial resolution**: Backend color consolidation is complete — `status.json`, `categories.json`, and the new `priorities.json` dimension tables now define all status colors, bg colors, gantt colors, and priority colors/labels. `ui_theme.py` reads from these dimension tables via `loader.py` accessor functions. The remaining work is replacing hardcoded hex values in the three GUI page files listed above with imports from `ui_theme.py`.

---

### N-08: Category Filtering Logic Duplicated Across 3 Pages

```python
# Appears in tasks_page.py, dashboard_page.py, gantt_page.py
if cat_filter != "All" and project.category != cat_filter:
    continue
```

**Fix**: Add `helpers/data/queries.py`:

```python
def filter_by_category(projects, category: str) -> list[Project]:
    if category == "All":
        return list(projects)
    return [p for p in projects if p.category == category]
```

---

### N-09: No Validation of daily_hours_budget Input

**File**: `scripts/gui/pages/profile_page.py` (lines 255–262)

```python
try:
    data[key] = float(val) if val else 8.0
except ValueError:
    data[key] = 8.0  # Silently defaults on invalid input
```

User types "abc", silently gets 8.0 hours.

**Fix**: Show a validation error instead of silently defaulting.

---

### N-10: File Drop Parsing Uses Fragile Regex

**File**: `scripts/gui/pages/tasks_page.py` (lines 775–797)

```python
if "{" in raw:
    files = re.findall(r"\{([^}]+)\}", raw)
    remainder = re.sub(r"\{[^}]+\}", "", raw).strip()
```

May misparse Windows UNC paths or paths with special characters.

**Fix**: Use `tkinterdnd2`'s built-in path parsing if available, or add robust path validation.

---

### N-11: generate_page Thread Sets `_generating` Flag Without Lock

**File**: `scripts/gui/pages/generate_page.py` (lines 140, 165)

```python
self._generating = True   # Set on main thread
# ...in worker thread:
self._generating = False  # Set from worker thread — race condition
```

**Fix**: Use `threading.Lock` or `threading.Event` for the generating flag.

---

### N-12: No Tests for portability.py, pdf.py, shell.py, utilities.py

These modules contain meaningful logic (file I/O, subprocess calls, REPL loop, Outlook integration) but have zero test coverage.

**Fix**: Add integration tests for at least `portability.py` (export/import round-trip) and `pdf.py` (subprocess mock). `shell.py` and `utilities.py` are lower priority.

---

## Test Coverage Gaps

### Current Coverage Summary

| Test Level | Files | Status |
|------------|-------|--------|
| Unit (helpers/) | 6 test files | Good — validation, migration, scheduling |
| Integration (helpers/) | 3 test files | Good — persistence, gantt/timeline, UX |
| GUI widget | 8 test files | Good — all major pages and dialogs covered |
| GUI integration | 1 test file | Adequate — app orchestrator tested |

### Untested Modules

| Module | Risk | Notes |
|--------|------|-------|
| `helpers/profile/portability.py` | Medium | Export/import profile — file I/O heavy |
| `helpers/reporting/pdf.py` | Low | Subprocess call to Chrome — hard to test without browser |
| `helpers/io/files.py` | Low | Cross-platform `open_path()` — OS-dependent |
| `helpers/commands/utilities.py` | Low | Outlook email draft — Windows-only |
| `scripts/cli/shell.py` | Low | Interactive REPL — hard to unit test |
| Profile switching (`reload_profile()`) | Medium | No test verifies globals update correctly |
| Cascade delete end-to-end | Medium | No test covers project delete → task cleanup → file cleanup |

### Test Isolation Concerns

- `tests/gui/test_app_integration.py` patches `_prof` module attributes but doesn't reset between tests.
- `tests/gui/conftest.py` creates a real `Tk()` instance at import time for display detection.
- Several tests use `sys.path` manipulation at module level.

---

## Dependency Map Summary

### Architecture Layers (Healthy — No Violations)

```
┌─────────────────────────────────────────────────────┐
│  scripts/gui/pages/* & dialogs/*  (UI)              │
│  scripts/cli/run.py               (CLI)             │
├─────────────────────────────────────────────────────┤
│  helpers/commands/                 (Mutation layer)  │
│  helpers/scheduling/              (Business logic)   │
├─────────────────────────────────────────────────────┤
│  helpers/persistence/             (Read/Write)       │
│  helpers/data/                    (Queries)           │
│  helpers/reporting/               (Output)            │
├─────────────────────────────────────────────────────┤
│  helpers/schema/                  (Metadata — leaf)  │
│  helpers/domain/                  (Entities — leaf)   │
└─────────────────────────────────────────────────────┘
```

### Key Metrics

| Metric | Count | Assessment |
|--------|-------|------------|
| Total Python files | 87 | — |
| helpers → helpers cross-package imports | 38 | Acceptable |
| scripts → helpers imports | 45 | Expected |
| helpers → scripts imports | **0** | Clean |
| Circular import chains | **0** | Clean |
| Highest outbound imports (single file) | 13 (report_pipeline.py) | Orchestrator — expected |

### Pages That Import Utility Modules Directly

These aren't blocking issues but represent minor layer violations:

| Page | Imports | Severity |
|------|---------|----------|
| generate_page.py | `helpers.profile.config`, `helpers.io.files` | Minor |
| dashboard_page.py | `helpers.profile.config`, `helpers.io.files` | Minor |
| settings_page.py | `helpers.profile.config`, `helpers.io.paths` | Minor |
| profile_page.py | `helpers.profile.profile`, `helpers.profile.portability` | Acceptable |

These could be routed through the `AppContext` protocol but are fine for now.

---

## Prioritized Fix List

Work through these in order. Each item is independently committable.

### Phase 1: Foundation (Unblocks Everything Else)

| # | Issue | ID | Effort | Files Affected |
|---|-------|----|--------|----------------|
| 1 | Extract shared dialog base class (`_get`, `_parse_date`, button frame) | M-03 | Small | 3 dialog files + 1 new file |
| 2 | Extract duplicate project completion logic into shared function | C-03 | Small | domain_service.py, task_ops.py, 1 new file |
| 3 | Add public `profile` property to DomainService | C-09 | Tiny | domain_service.py, batch_dialog.py |
| 4 | Add public `rebuild_sidebar()` to App | M-11 | Tiny | app.py, profile_page.py |
| 5 | Fix bare excepts → specific exception types | M-06, M-07 | Small | batch_dialog.py, loader.py |
| 6 | Fix typo in pdf.py error message | M-09 | Tiny | pdf.py |

### Phase 2: Separation of Concerns

| # | Issue | ID | Effort | Files Affected |
|---|-------|----|--------|----------------|
| 7 | Extract dashboard statistics into helpers/data/ | C-05 | Medium | dashboard_page.py, 1 new file |
| 8 | Extract category filtering into shared query helper | N-08 | Small | 3 page files, 1 new file |
| 9 | Extract Gantt data prep into helpers/reporting/ | C-04 | Medium | gantt_page.py, gantt.py |
| 10 | Create RowReader/WorkbookAccessor for cell navigation | C-13 | Medium | task_ops.py, workbook_writer.py, 1 new file |
| 11 | Break tasks_page build() into helper methods | C-06 | Medium | tasks_page.py |
| 12 | Break tasks_page _populate_tree() — extract filtering | C-07 | Medium | tasks_page.py |
| 13 | Centralize color mappings in ui_theme.py | N-07 | Small | 3 page files, ui_theme.py |
| 14 | Add `find_by_id()` to Profile for generic ID resolution | M-05 | Small | profile.py, gantt_page.py |

### Phase 3: Thread Safety & Error Handling

| # | Issue | ID | Effort | Files Affected |
|---|-------|----|--------|----------------|
| 15 | Fix thread safety in generate_page (use `after()` for state updates) | C-08 | Small | generate_page.py |
| 16 | Add threading.Lock or Event for `_generating` flag | N-11 | Tiny | generate_page.py |
| 17 | Debounce Gantt canvas `<Configure>` event | C-04 | Tiny | gantt_page.py |
| 18 | Debounce external edit detection on focus | C-10 | Small | app.py |
| 19 | Improve autosave error handling (log, persistent warning) | C-11 | Small | app.py |
| 20 | Add error handling to _cleanup_task_files | N-02 | Tiny | domain_service.py |
| 21 | Log subprocess output on PDF generation failure | M-08 | Tiny | pdf.py |
| 22 | Show validation error for invalid hours input | N-09 | Tiny | profile_page.py |

### Phase 4: Profile Globals Refactor (Larger Effort)

| # | Issue | ID | Effort | Files Affected |
|---|-------|----|--------|----------------|
| 23 | Replace profile globals with ProfileConfig dataclass | C-01 | Large | profile.py, config.py, all consumers (~10 files) |
| 24 | Defer profile initialization (no code at import time) | C-02 | Medium | profile.py, cli.py, gui.py |
| 25 | Add migration version check to skip redundant migration | C-15 | Small | contract.py, serializer.py |

### Phase 5: Polish

| # | Issue | ID | Effort | Files Affected |
|---|-------|----|--------|----------------|
| 26 | Extract attachment migration into generic helper | M-04 | Small | notes.py, links.py, service.py |
| 27 | Refactor sync_timelines() to table-driven approach | N-04 | Medium | timelines.py |
| 28 | Add step counter to report pipeline logging | M-10 | Tiny | report_pipeline.py |
| 29 | Add all_deliverables property to Profile | N-03 | Tiny | profile.py, workbook_writer.py |
| 30 | Add tests for portability.py and cascade delete | N-12 | Medium | 2 new test files |

---

## How to Use This Report

1. **Pick a phase.** Work through Phase 1 first — these are small, safe changes that unlock later work.
2. **One issue per commit.** Each item in the fix list is independently committable. Don't batch unrelated changes.
3. **Run tests after each change.** `pytest tests/` should pass after every commit.
4. **Update this report.** Cross off items as they're completed. Add new issues as they're discovered.
5. **Don't rush Phase 4.** The profile globals refactor touches ~10 files. Plan it as a dedicated session.
