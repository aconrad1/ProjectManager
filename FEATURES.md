# ProjectManager — Features, Logic & Limitations

A complete reference for every capability, algorithm, and known constraint in the system.

---

## Table of Contents

- [1. Domain Model](#1-domain-model)
- [2. GUI Pages](#2-gui-pages)
- [3. GUI Dialogs](#3-gui-dialogs)
- [4. CLI & Interactive Shell](#4-cli--interactive-shell)
- [5. Report Pipeline](#5-report-pipeline)
- [6. Scheduling Engine](#6-scheduling-engine)
- [7. Completion Detection](#7-completion-detection)
- [8. Overview Builder](#8-overview-builder)
- [9. Persistence & Sync](#9-persistence--sync)
- [10. Workbook Schema](#10-workbook-schema)
- [11. Profile System](#11-profile-system)
- [12. Attachments, Notes & Links](#12-attachments-notes--links)
- [13. Configuration & Theming](#13-configuration--theming)
- [14. Keyboard Shortcuts](#14-keyboard-shortcuts)
- [15. Known Limitations](#15-known-limitations)

---

## 1. Domain Model

The system uses a strict four-level hierarchy. Every entity inherits from `Node` which provides common fields: `id`, `title`, `description`, `status`, `start`, `end`, `deadline`, and computed helpers like `is_overdue` and `resolve_root()`.

### Profile (Root)

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| company | str | — | Maps to a folder under `profiles/` |
| role | str | — | Display only (used in reports) |
| email | str | — | Display only |
| phone | str | — | Display only |
| recipient_name | str | — | Report recipient |
| recipient_email | str | — | For Outlook draft |
| workbook_filename | str | — | Excel file inside the company folder |
| daily_hours_budget | float | 8.0 | Caps how many task-hours can be scheduled per day |
| weekly_hours_budget | float | 40.0 | Caps total hours per week when `enforce_weekly_budget` is enabled |

**Query helpers:** `all_tasks` (flat list), `find_project(id)`, `find_task_global(id)`, `projects_for_category(cat)`, `tasks_for_category(cat)`, `search_projects(query)`, `search_tasks(query)`.

### Project

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| project_id | str | auto | `P-001`, `P-002`, … |
| category | str | "Ongoing" | `Weekly`, `Ongoing`, or `Completed` |
| supervisor | str | "" | |
| site | str | "" | |
| priority | int | 3 | 1–5 scale |
| notes | str | "" | |
| date_completed | date | None | Auto-stamped when all tasks complete |

**Owns:** `tasks: list[Task]`
**Computed:** `task_count`, `tasks_by_priority()`, `tasks_by_status(status)`, `time_allocated_total`, `time_spent_total`.

### Task

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| task_id | str | auto | `T-001`, `T-002`, … |
| project_id | str | — | FK → parent Project |
| supervisor | str | "" | |
| site | str | "" | |
| priority | int | 3 | 1–5 scale |
| commentary | str | "" | Free-text status update |
| scheduled_date | date | None | Written by the scheduler |
| date_completed | date | None | Auto-stamped on completion |

**Owns:** `deliverables: list[Deliverable]`
**Computed:** `priority_label`, `time_allocated_total` (sum of deliverables), `time_spent_total`.

### Deliverable

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| deliverable_id | str | auto | `D-001`, `D-002`, … |
| task_id | str | — | FK → parent Task |
| percent_complete | int | 0 | 0–100 |
| time_allocated | float | None | Hours budgeted |
| time_spent | float | None | Hours actually spent |

### Timeline (Value Object)

| Field | Type | Notes |
|-------|------|-------|
| start | date | None | Can be None |
| end | date | None | Can be None |

**Computed:** `duration_days`, `is_active`, `contains(date)`.

### Priority Scale

| Level | Label | Meaning |
|-------|-------|---------|
| 1 | P1 – Urgent | Drop everything — immediate attention |
| 2 | P2 – High | Active focus, primary workload |
| 3 | P3 – Medium | Complete alongside higher priorities |
| 4 | P4 – Low | Work on when higher-priority items pause |
| 5 | P5 – Background | Opportunistic, long-horizon |

### Status Values

| Status | Active? | Triggers Completion? |
|--------|---------|---------------------|
| Not Started | No | No |
| In Progress | Yes | No |
| On Track | Yes | No |
| Ongoing | Yes | No |
| Recurring | Yes | No |
| Complete/Pending | No | **No** — stays in Ongoing, gets its own report section |
| On Hold | No | No |
| Completed | No | **Yes** — auto-stamps `date_completed`, moves to Completed category |

---

## 2. GUI Pages

### Dashboard

Provides at-a-glance workload visibility. All data is read-only and auto-refreshed.

- **Stat cards:** Weekly task count, Ongoing project count, Completed count, Total active
- **Priority breakdown:** Horizontal bar charts for P1–P5 showing count and percentage
- **Recently completed:** Tasks completed in the last 7 days, plus a 30-day summary
- **Site distribution:** Top 8 sites by task count with color-coded bars
- **Priority spotlight:** Shows only P1 and P2 tasks for urgent focus

### Task Manager

The primary workspace for day-to-day task management.

- **Hierarchical treeview:** Project → Task → Deliverable (3-level nesting)
- **8 visible columns:** Title, Supervisor, Site, Status, Priority, Scheduled Date, Time (Allocated/Spent), Category
- **Search:** Real-time filtering by title, supervisor, or site
- **Category filter:** Dropdown: All / Weekly / Ongoing / Completed
- **Priority color-coding:** P1=red, P2=orange, P3=yellow, P4=blue, P5=gray
- **Right-click context menu:** Edit, Duplicate, Set Status (submenu with all 8 statuses), Set Priority (submenu P1–P5), Add Deliverable, Attach File, View Attachments, Link Folder, Open Linked Folder, Task Notes, Delete
- **Drag-and-drop:** Files dropped onto a task are attached; tasks can be reparented between projects
- **Double-click:** Opens the edit dialog for the selected item
- **Toolbar buttons:** Edit, Delete, Duplicate, Add Project, Batch Edit, Attach File, View Attachments, Link Folder, Open Folder, Task Notes, Refresh
- **Multi-select:** Extended selection mode (Ctrl+click, Shift+click) for batch operations
- **Batch operations:** "Batch Edit…" button opens a dialog to apply status changes, priority changes, or date shifts (±N days on start/end/deadline) to all selected tasks at once
- **Persistent state:** Filter selection, search text, and treeview expansion state are saved to `ui_state.json` and restored on next session
- **DnD resilience:** If `tkinterdnd2` is not installed, the status bar shows a warning instead of failing silently

### Add Task

A dedicated form for creating new tasks quickly.

- **Project selector:** Dropdown listing all projects (required)
- **10-field form:** Title, Supervisor, Site, Description, Commentary, Status, Priority, Start Date, End Date, Deadline
- **Conditional field:** Date Completed appears only when the selected project's category is "Completed"
- **Auto-focus:** Project selector is focused on page load
- **Post-submit:** Form resets all fields after successful save

### Generate Reports

Controls for the report pipeline with live output.

- **Save Workbook** — Saves the current workbook + creates a dated snapshot
- **Generate Reports** — Runs the full 9-step pipeline in a background thread with real-time log output
- **Save & Close** — Save then exit the application
- **Open Latest Report** — Opens the most recent PDF (falls back to Markdown)
- **Email Report** — Creates an Outlook draft with the latest PDF attached and a time-aware greeting
- **Output log:** Scrolling monospace text area showing pipeline progress

### Project Timeline (Gantt)

Canvas-based Gantt chart for long-term planning.

- **Rows:** Project headers (blue background) → Task bars → Deliverable sub-bars
- **"No Scheduled Start" section:** Tasks without a start date appear at the bottom under a distinct section header so they are never invisible
- **Category filter:** All / Weekly / Ongoing / Completed
- **Zoom slider:** Adjusts day width from 4px to 40px
- **Auto-scaled date range:** Computes from earliest start to latest end + padding
- **Task bars:** Color-coded by status (blue=active, green=done, red=on hold, gray=not started)
- **Deliverable progress overlay:** Green fill proportional to `percent_complete`
- **Deadline markers:** Red diamond at each deadline
- **Today line:** Red dashed vertical line
- **Month labels and week ticks:** In the header row
- **Right-click context menu:** Edit (opens dialog), Shift Start ±1 day, Shift End ±1 day — works on tasks and deliverables
- **Scrollable:** Both horizontal and vertical
- **Dark mode toggle:** Checkbox in the header switches the canvas to a dark palette (dark backgrounds, light text, muted grid lines, themed status colors) — all colors configurable via `gantt_colors_dark` in `theme.json`

### Weekly Planner

Grid-based schedule view showing the computed daily workload.

- **7-day × 5-priority grid:** Each cell shows the task assigned to that day/priority slot
- **Daily budget bars:** Green (under capacity) → Orange (approaching) → Red (over capacity)
- **Week navigation:** Previous Week / "This Week" / Next Week buttons
- **Status color-coding:** Blue wash (In Progress), Green wash (On Track), Gray (Not Started), Red (On Hold), Bright green (Completed)
- **Budget warnings:** Days exceeding `daily_hours_budget` are visually flagged

### Profile Management

Two-panel layout for managing user profiles.

- **Left panel:** Profile list with selection highlighting
- **Right panel:** 9-field editor — Name, Role, Company, Email, Phone, Recipient Name, Recipient Email, Workbook Filename, Daily Hours Budget
- **Actions:** Save Changes, Switch To, Import Workbook, Delete Profile
- **Import Workbook:** Reads an external Excel file, overwrites the current JSON domain store
- **Live switching:** Switching profiles reloads all data without restarting

### Settings

Application configuration and display.

- **Active profile summary:** Name, Company, Role (read-only)
- **Buttons:** Manage Profiles (jumps to Profiles page), Open YAML File (opens in default editor)
- **Application paths:** Read-only display of Profile Dir, Workbook, Reports, Exports, Data, Attachments
- **Appearance toggle:** Light / Dark / System (uses customtkinter appearance modes)

---

## 3. GUI Dialogs

### Project Dialog (Add / Edit)

- **12 fields:** Title (required), Category, Description (textbox), Status, Supervisor, Site, Priority (None / P1–P5), Notes (textbox), Start Date, End Date, Deadline, Date Completed
- **Window:** 540×750, resizable (min 420×560), modal
- **Pre-fill:** All fields populated when editing an existing project

### Task Dialog (Add / Edit)

- **12 fields:** Title (required), Supervisor, Site, Description (textbox), Commentary (textbox), Status, Priority (P1–P5), Start Date, End Date, Deadline, Date Completed, Scheduled Date
- **Window:** 620×780, resizable (min 500×640), modal
- **Pre-fill:** All fields populated when editing

### Deliverable Dialog (Add / Edit)

- **9 fields:** Title (required), Description, Status, % Complete (integer 0–100), Time Allocated (hours), Time Spent (hours), Start Date, End Date, Deadline
- **Window:** 520×560, modal
- **Validation:** % Complete must be integer, time fields must be numeric

### Task Notes Dialog

- **Note list:** Timestamped entries displayed newest-first
- **Add note:** Text entry + Save button (auto-timestamps with current datetime)
- **Storage:** JSON file at `profiles/<company>/data/task_notes.json`, keyed by task ID

### Batch Edit Dialog

- **Bulk operations:** Apply status, priority, or date shifts to multiple selected tasks at once
- **Selection:** Operates on all tasks currently selected in the Tasks page treeview (Ctrl+click, Shift+click)
- **Available changes:** Set Status (all 8 values), Set Priority (P1–P5), Shift dates (±N days on start/end/deadline)
- **Window:** Modal dialog, applies changes via DomainService

---

## 4. CLI & Interactive Shell

### Subcommands

| Command | Description |
|---------|-------------|
| `generate` | Full 8-step report pipeline with logging |
| `save` | Save workbook + create dated snapshot |
| `open` | Open the most recent PDF or Markdown report |
| `email` | Create an Outlook draft with the latest PDF |
| `list [--all]` | Show active tasks (Weekly + Ongoing); `--all` includes Completed |
| `profile [--switch N]` | List all profiles, or switch to index N |
| `init "Name" "Company" [--workbook "File.xlsx"]` | Create and scaffold a new profile |
| `shell` | Launch the interactive REPL |
| `project list` | List all projects |
| `task list [--project P-001]` | List tasks, optionally filtered by project |
| `task add --project P-001 --title "…"` | Add a new task |
| `task delete --task-id T-001` | Delete a task by ID |
| `deliverable list --task T-001` | List deliverables for a task |
| `deliverable add --task T-001 --title "…"` | Add a new deliverable |

### Interactive Shell

A REPL for quick operations. Commands:

- `list` — Show all registered command names
- `run <command> [args]` — Execute a command with arguments
- `help` or `?` — Show usage
- `quit` or `exit` — Exit the shell

### CLI Auto-Persist

After any CLI mutation (add/edit/delete), the workbook is saved and `domain.json` is re-synced automatically via a post-mutate hook.

---

## 5. Report Pipeline

`generate_reports()` executes 9 sequential steps, each logged to the callback logger:

| Step | Action | Details |
|------|--------|---------|
| 1 | **Capture Snapshot** | Loads the pre-mutation `domain.json` as the baseline for change history comparison |
| 2 | **Process Completions** | Scans Tasks sheet for `Status=Completed`. Stamps `Date Completed`. Auto-completes parent projects if all tasks are done. |
| 3 | **Sync Domain** | Loads workbook, syncs to JSON, reconstructs the in-memory Profile hierarchy. Computes snapshot diff against baseline. |
| 4 | **Schedule** | Runs `compute_schedule()` to assign tasks to days, counts task-slots |
| 5 | **Overview Tab** | Populates the branded Excel Overview sheet (5 sections: status summary, weekly grid, time overview, upcoming deadlines, change history) |
| 6 | **Timelines Integrity & Sync** | Runs 5 integrity checks (headers, VLOOKUP formulas, formula targets, duration formulas, missing/orphaned IDs), auto-repairs if needed by rebuilding both Timelines and Gantt sheets |
| 7 | **Save** | Dual-writes JSON + workbook, creates a dated Excel snapshot in `reports/` |
| 8 | **Reports** | Generates Markdown (with embedded CSS) and PDF (via headless Chrome/Edge), including change history section |
| 9 | **Complete** | Logs summary, returns result dict |

**Returns:** `{moved: [titles], wb: Workbook, md_path: Path, pdf_path: Path, profile: Profile, snapshot_diff: SnapshotDiff}`

### Report Sections (PDF / Markdown)

| Section | Content |
|---------|---------|
| Executive Summary | Auto-generated paragraph: workload mix, completion status |
| Priority Spotlight | Top 3 highest-priority items with full details |
| Weekly Recurring Tasks | Table of recurring work items |
| Background Work | P4–P5 items in a compact table |
| Complete / Pending | Phase-done items still in Ongoing |
| Recently Completed | Tasks completed within `recent_completed_days` window (configurable, default 7) |
| Extended Completed | Completion history within `extended_completed_days` window (configurable, default 30) |
| Site Support Distribution | Task counts by site |
| Priority Distribution | Breakdown by priority tier |
| Supervisor Distribution | Task count by supervisor |
| Change History | Added/removed/modified entities since previous snapshot (when diff available) |
| Looking Ahead | Top 3 focus items for next week |

### Output Files

```
<Name>_Weekly_Deliverables_Report_YYYY-MM-DD.xlsx   → profiles/<company>/reports/
<Name>_Weekly_Deliverables_Report_YYYY-MM-DD.md     → profiles/<company>/exports/markdown/
<Name>_Weekly_Deliverables_Report_YYYY-MM-DD.pdf    → profiles/<company>/exports/pdf/
```

---

## 6. Scheduling Engine

### Algorithm: `compute_schedule(profile, reference_date)`

The scheduler assigns tasks to days using partial allocation, multi-task slots,
and optional weekly budget enforcement.

**Step 1 — Gather active tasks:**
- Include tasks from Weekly and Ongoing projects only
- Exclude tasks with status `Completed` or `On Hold` (case-insensitive)

**Step 2 — Group by priority:**
- 5 buckets (P1 through P5)

**Step 3 — Sort within each priority group:**
1. Rollover flag — tasks with `scheduled_date` before `reference_date` come first (overdue rollover)
2. Deadline — earliest first; `None` pushed to 2999-12-31
3. Start date — earliest first; `None` pushed to 2999-12-31
4. Title — alphabetical tie-break

**Step 4 — Assign to days (partial allocation):**
- For each task, determine total hours via `_task_hours()` (sum of deliverable `time_allocated`, fallback: `default_time_allocated_hours` from config)
- Allocate `min(remaining_task_hours, remaining_day_capacity)` to the current day
- If the task has remaining hours, continue allocation on subsequent days (partial-day splitting)
- Each `(day, priority)` slot can hold up to `max_tasks_per_priority_slot` tasks (default 3)
- `daily_hours_budget` caps total hours per day
- When `enforce_weekly_budget` is enabled, `weekly_hours_budget` caps total hours per week; when a week's cap is reached the scheduler skips to the next week
- Week boundaries are determined by `week_start_day` config (default Monday)
- `scheduled_date` is set to the **first** day a task appears on
- Safety limit: `_MAX_SCHEDULE_DAYS = 365` prevents infinite loops

**Step 5 — Return:**
- `Schedule = dict[date, dict[int, list[tuple[Task, float]]]]` — nested mapping of dates → priorities → `(task, hours_assigned)` entries

### Type Aliases

```python
ScheduleEntry = tuple[Task, float]           # (task, hours_assigned)
Schedule = dict[date, dict[int, list[ScheduleEntry]]]
```

### Helper Functions

- `flatten_schedule(schedule)` → `dict[date, list[tuple[int, Task]]]` — converts new nested format to legacy flat format for backward compatibility
- `daily_hours(schedule)` → `dict[date, float]` — total hours per day
- `over_capacity_days(schedule, daily_cap)` → `dict[date, float]` — days exceeding the cap, with their totals
- `weekly_hours_totals(schedule, week_start_day)` → `dict[date, float]` — total hours per week keyed by week-start date
- `week_start_date(d, start_day)` → `date` — start of the week containing *d* (configurable start day)
- `_task_hours(task)` → `float` — total allocated hours for a task, with configurable fallback

---

## 7. Completion Detection

`process_completions(wb, today)` runs during report generation:

1. Scans the Tasks sheet for rows where Status = "Completed" (case-insensitive, whitespace-trimmed)
2. For each newly completed task (no `Date Completed` yet): stamps `today` into the Date Completed cell
3. Returns a list of task titles that were moved
4. **Project auto-complete:** If every task under a project now has Status = "Completed", the project itself is marked:
   - `status = "Completed"`
   - `category = "Completed"`
   - `date_completed = today`

### Logic Details

- `Complete/Pending` is **not** treated as Completed — tasks with this status remain active in Ongoing
- Completion detection only runs during `generate_reports()` — it does not fire on every save
- The `DomainService.set_status()` method also stamps `date_completed` when setting status to "Completed" via the GUI, but does not auto-complete parent projects

---

## 8. Overview Builder

`write_overview(wb, profile, moved_titles, today, author, role, company, snapshot_diff=None)` populates the Excel Overview sheet with up to 5 branded sections:

### Section 1 — Project Status Summary

Per-project row with columns: Title, Category, Status, Priority (highest task), Active Task Count, % Complete (completed deliverables / total), Allocated Hours, Spent Hours. Alternating row colors.

### Section 2 — Weekly Schedule Grid

7 columns (days starting from today, configurable week start) × 5 rows (P1–P5). Each cell contains one or more task titles scheduled for that day/priority slot (newline-joined when multiple tasks share a slot). Color-filled by the first task's status.

### Section 3 — Time Overview

Per-project row: Allocated, Spent, Remaining (max 0), Utilization % (Spent/Allocated × 100). Includes a TOTAL row.

### Section 4 — Upcoming Deadlines

Items with deadlines within the configurable `upcoming_deadline_days` window (from `deadlines.json`, default 14 days), sorted by date. Shows Deadline, Item, Status, Parent.

### Section 5 — Change History

When a `SnapshotDiff` is provided, displays a table of all added/removed/modified entities with columns: Change, Type, ID, Title, Details. Only appears when there are actual changes.

### Styling

- AltaGas brand colors: `#003DA5` (dark), `#336BBF` (mid), `#B3CDE3` (light), `#E6EFF8` (wash)
- Frozen header row, auto-widened columns, merged title cells

---

## 9. Persistence & Sync

### Architecture

`domain.json` is the **sole source of truth**. The Excel workbook is a rendered downstream artifact that is kept in sync.

### Data Flow

```
Load:    domain.json  ──→  Profile hierarchy (in memory)
Mutate:  DomainService / task_ops  ──→  modify Profile tree
Save:    contract.save()  ──→  domain.json (canonical) + workbook.xlsx (rendered)
Import:  contract.import_from_workbook()  ──→  Excel overrides JSON (explicit, user-triggered)
```

### Hash-Based External Edit Detection

On startup, `contract.sync()` performs reconciliation:

1. If `domain.json` exists: load it, compute SHA-256 of the current workbook
2. Compare the hash against `domain.json._meta.workbook_hash`
3. If hashes differ → the user edited the Excel externally → import from workbook (overwrites JSON)
4. If hashes match → no external changes → render JSON → workbook (refresh the rendered view)
5. If only workbook exists (no JSON) → bootstrap: read workbook, create initial `domain.json`

The SHA-256 approach is **immune to OneDrive/cloud sync mtime bumps** that cause false positives with timestamp-based detection.

#### Mid-Session External Edit Detection

`contract.detect_external_edits(company, wb_path)` performs the same hash comparison but is designed to be called frequently during a session. The GUI hooks it into four trigger points:

| Trigger | Location | Behaviour |
|---------|----------|-----------|
| **Window focus** | `<FocusIn>` event on the root `App` window | Only fires for the root widget, not every child |
| **Tab / page change** | `App.show_page()` | Checked before rendering the new page |
| **Manual save** | `App.save_state()` | Checked before overwriting the workbook on disk |
| **Report generation** | Via the generate page flow | Implicitly through `save_state()` |

When an external edit is detected the user is prompted to either **reload** (import the external changes) or **keep** (overwrite the external changes on the next save).

### Atomic Dual-Write

Every `contract.save()` call uses a temp-file-then-rename strategy for crash safety:

1. Serializes the Profile to JSON and writes to `domain.json.tmp`
2. Backs up the existing `domain.json` to `domain.json.bak`
3. Atomically renames `domain.json.tmp` → `domain.json` (via `os.replace`)
4. Renders the Profile tree into the workbook (in-memory)
5. If the workbook render fails, rolls back JSON from the `.bak` copy
6. On success, removes the `.bak` file

This ensures that `domain.json` is never left in a truncated or corrupt state, even if the process crashes mid-write or the workbook render throws an exception.

---

## 10. Workbook Schema

### 6-Sheet Design

| Sheet | Type | Purpose |
|-------|------|---------|
| **Overview** | Derived | Formatted branded report (auto-populated by `write_overview`) |
| **Projects** | Data | One row per project (13 columns) |
| **Tasks** | Data | One row per task (12 columns), FK → Projects via Project ID |
| **Deliverables** | Data | One row per deliverable (11 columns), FK → Tasks via Task ID |
| **Timelines** | Derived | VLOOKUP-driven unified timeline of all items (14 columns) |
| **Gantt Chart** | Derived | Conditional-formatted date grid with status colors |

### ID System

- Projects: `P-001`, `P-002`, … (auto-incremented)
- Tasks: `T-001`, `T-002`, …
- Deliverables: `D-001`, `D-002`, …

IDs are never reused within a profile's lifetime. Foreign keys link Tasks → Projects and Deliverables → Tasks.

### Timelines Sheet (VLOOKUP-Driven)

14 auto-synced columns: Item ID, Item Type, Title, Parent ID, Start, Duration (formula), End, Deadline, Status, % Complete, Time Allocated, Time Spent, Scheduled Date, Milestones.

### Gantt Chart (Conditional Formatting)

- Fixed columns: ID, Title, Start, End, Status
- Dynamic columns: One per date in the range
- **3 conditional rules:** Green (completed + in-range), Red (overdue + in-range), Blue (active + in-range)
- **"No Scheduled Start" section:** Items without a start date in source data sheets are grouped under a section header row at the bottom of the sheet (styled with light-gray background)
- Data pulled via VLOOKUP from Timelines
- `_classify_items(wb, tl_ws)` cross-references source sheets (Projects/Tasks/Deliverables) to determine which items have start dates, since VLOOKUP formulas cannot be evaluated by openpyxl

### Template Creation

`create_template(path)` generates a blank 6-sheet workbook with:
- All headers pre-set
- Frozen panes on each sheet
- Tab colors (AltaGas brand)
- Column widths auto-sized
- Data validation dropdowns for Category, Status fields

---

## 11. Profile System

### YAML Configuration

```yaml
active_profile: 0
profiles:
  - name: "Your Name"
    company: "Your Company"
    workbook_filename: "Your Workbook.xlsx"
    daily_hours_budget: 8.0
    weekly_hours_budget: 40.0
    # ...

  # Dev / Test profile (committed with sample data)
  - name: "Dev Tester"
    company: "_TestCompany"
    workbook_filename: "TestProjects.xlsx"
    daily_hours_budget: 8.0
```

### Test Profile (`_TestCompany`)

A committed test profile at profile index 1 provides sample data for development and CI:

- **4 projects** across all categories (Weekly, Ongoing, Completed)
- **10 tasks** with varied priorities (P1–P4), statuses, supervisors, and sites
- **10 deliverables** with time allocations and progress percentages
- Sample `task_notes.json` and `task_links.json` for realism
- Protected from `reset_for_distribution.py` via `_KEEP_DIRS`

Switch to it: `python scripts/cli.py profile --switch 1`

### Capabilities

| Function | Description |
|----------|-------------|
| `get_profiles()` | Return all profile dicts from YAML |
| `get_active_profile()` | Return the currently active profile |
| `switch_profile(index)` | Change active, re-apply globals, save YAML |
| `save_profile(index, data)` | Update a single profile's fields |
| `init_profile(data)` | Create a new profile + scaffold directory structure |
| `delete_profile(index)` | Remove profile (auto-creates fallback if this is the last one) |
| `scaffold_profile()` | Create company directories: data/, reports/, exports/, attachments/ |

### Profile Export / Import

Profiles can be packaged as `.pmprofile` bundles (ZIP archives) for transfer between installations.

| Function | Description |
|----------|-------------|
| `export_profile(index, dest)` | Package a profile's directory + YAML manifest into a `.pmprofile` ZIP |
| `import_profile(path)` | Extract a `.pmprofile` bundle, register the profile in YAML |

**Archive contents:**
- `_profile.yaml` — the profile's YAML dict (name, company, role, etc.)
- `<company>/` — the full profile directory tree (data, attachments, exports, reports)

**Security:** Path traversal attacks in archive member names are rejected on import.

### Module-Level Globals

After `_apply_profile()` or `reload_profile()`, these globals are set and can be imported anywhere:

`USER_NAME`, `USER_ROLE`, `USER_COMPANY`, `USER_EMAIL`, `USER_PHONE`, `RECIPIENT_NAME`, `RECIPIENT_EMAIL`, `WORKBOOK_FILENAME`, `DAILY_HOURS_BUDGET`, `WEEKLY_HOURS_BUDGET`

### Directory Isolation

Each profile gets its own folder tree:

```
profiles/<Company>/
  <workbook>.xlsx          # Master workbook
  data/
    domain.json            # Source of truth
    task_notes.json        # Activity logs
    task_links.json        # Linked folder paths
  attachments/             # Per-task file storage
  reports/                 # Dated Excel snapshots
  exports/
    markdown/              # Dated .md reports
    pdf/                   # Dated .pdf reports
```

---

## 12. Attachments, Notes & Links

All attachment, note, and link storage is **keyed by task ID** (e.g. `T-001`)
rather than task title.  This eliminates data loss from title collisions and
removes the need for rename cascades on title change.

Legacy data keyed by task title is **migrated automatically** on profile load
via `helpers.migration.migrate_to_id_keying()`.

### File Attachments

- **Attach:** Copy files into `attachments/<task_id>/`
- **List:** Return all files in a task's attachment folder
- **Open folder:** Launch OS file explorer at the task's attachment directory
- **Delete cascade:** When a task is deleted, its attachment folder is recursively removed
- **Migration:** Legacy `attachments/<safe_task_title>/` directories are renamed to `<task_id>/`
- **GUI:** Drag-and-drop onto the treeview, or right-click → Attach File

### Task Notes (Activity Log)

- **Storage:** `task_notes.json` — dict keyed by task ID, each value is a list of `{timestamp, text}`
- **Add note:** Appends with `datetime.now()` timestamp
- **List notes:** Returns newest-first
- **Delete cascade:** Removes all notes when task is deleted
- **Migration:** Legacy title-keyed entries are re-keyed to task IDs on load

### Linked Folders

- **Storage:** `task_links.json` — dict keyed by task ID, each value is a folder path string
- **Set link:** Opens a directory picker, stores the chosen path
- **Open link:** Launches the linked folder in Windows Explorer
- **Delete cascade:** Removes the link (not the actual folder)
- **Migration:** Legacy title-keyed entries are re-keyed to task IDs on load

---

## 13. Configuration & Theming

### Config Files (`helpers/config/`)

| File | Purpose |
|------|---------|
| `categories.json` | `["Weekly", "Ongoing", "Completed"]` |
| `status.json` | All 8 status values + `completed_statuses` and `active_statuses` lists |
| `fields.json` | GUI label ↔ domain attribute mappings for project, task, deliverable |
| `deadlines.json` | Deadline window config (default 14 days for Overview section) |
| `theme.json` | Brand colors, priority labels/colors, gantt colors (light + dark palettes), status colors, treeview tag colors |
| `deadlines.json` | Rolling window config: `recent_completed_days`, `extended_completed_days`, `upcoming_deadline_days`, `snapshot_lookback_days` |
| `defaults.json` | Scheduler defaults: `default_time_allocated_hours`, `max_tasks_per_priority_slot`, `week_start_day`, `enforce_weekly_budget` |

### Config Loader

- `load(name)` — Parse a JSON file by name, LRU-cached (32 entries)
- `load_field_map(entity)` — Returns `{gui_label: domain_attr}` for an entity type
- `load_reverse_field_map(entity)` — Returns `{domain_attr: gui_label}`

### Brand Colors

| Name | Hex | Usage |
|------|-----|-------|
| AG_DARK | `#003DA5` | Headers, primary buttons, sidebar |
| AG_MID | `#336BBF` | Hover states, secondary buttons |
| AG_LIGHT | `#B3CDE3` | Accents, borders |
| AG_WASH | `#E6EFF8` | Backgrounds, alternating rows |

### Priority Colors

| Priority | Color |
|----------|-------|
| P1 – Urgent | `#c0392b` (red) |
| P2 – High | `#e67e22` (orange) |
| P3 – Medium | `#f1c40f` (yellow) |
| P4 – Low | `#3498db` (blue) |
| P5 – Background | `#95a5a6` (gray) |

---

### Domain Validation (`helpers/validation.py`)

All mutations through `DomainService` are validated before persisting. Invalid
data raises `ValidationError` with a list of human-readable error strings.

| Validator | Checks |
|-----------|--------|
| `validate_project(data)` | Title required, category in {Weekly, Ongoing, Completed}, priority 1–5, date range consistency |
| `validate_task(data)` | Title required, status in valid set, priority 1–5, date range consistency |
| `validate_deliverable(data)` | Title required, percent_complete 0–100, time_allocated/time_spent non-negative, date range |
| `validate_schedule_config(config)` | `default_time_allocated_hours` > 0, `max_tasks_per_priority_slot` positive int, `week_start_day` valid day name |
| `validate_budget(daily, weekly)` | Both > 0, daily ≤ weekly |

Edit operations use `partial=True` to skip the title-required check when only
updating other fields.

---

## 14. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save workbook |
| `Ctrl+G` | Generate reports |
| `Ctrl+Q` | Quit application |
| `Ctrl+Tab` | Next page |
| `Ctrl+Shift+Tab` | Previous page |
| `F1`–`F8` | Jump to page by index |
| `Delete` | Delete selected item (cascade-deletes children, notes, links, attachments) |

### App Behavior

- **Autosave:** Tracks a dirty flag; saves automatically every 30 seconds when changes are pending
- **Status bar:** Bottom bar showing the last save timestamp and "Saving…" indicator
- **Page registry:** Pages are loaded from `page_registry.py` — adding a page requires only one line there

---

## 15. Known Limitations

### Scheduling

| Limitation | Details |
|------------|---------|
| **Configurable time fallback** | If a task has no deliverables with `time_allocated`, the scheduler uses `default_time_allocated_hours` from `helpers/config/defaults.json` (default 1.0 hr) |
| **Safety limit** | The scheduler caps allocation at `_MAX_SCHEDULE_DAYS = 365` days into the future to prevent infinite loops in edge cases |
| **Weekly budget opt-in** | `enforce_weekly_budget` must be set to `true` in `defaults.json` to activate weekly hour caps; it defaults to `false` |

### Persistence

| Limitation | Details |
|------------|---------|
| **ID monotonic only** | Deleted IDs are not recycled. Gaps in ID sequences are permanent. |

### Completion Detection

| Limitation | Details |
|------------|---------|
| **Only fires during report generation** | Completion detection runs in the `generate_reports()` pipeline. Tasks marked Completed in the GUI get `date_completed` immediately via `DomainService.set_status()`, but parent project auto-completion only triggers during report generation. |
| **Complete/Pending is not terminal** | Tasks with `Complete/Pending` status remain in Ongoing and are not moved to Completed. This is by design. |
| **No undo** | Once a project is auto-completed, there is no one-click undo. The user must manually change the status and category back. |

### Gantt & Timelines

| Limitation | Details |
|------------|---------|
| **Integrity auto-repair is best-effort** | The `check_and_repair()` function runs 5 integrity checks (headers, VLOOKUPs, formula targets, duration formulas, missing IDs), then rebuilds both Timelines and Gantt sheets. However, orphaned rows (IDs in Timelines but not in source sheets) produce only warnings and are cleaned up on the next rebuild. |
| **Right-click shift is ±1 day only** | The Gantt right-click menu shifts start/end by exactly 1 day. Larger adjustments require the edit dialog. |
| **Unscheduled section has no bars** | Tasks in the "No Scheduled Start" section are shown as label-only rows — date bars cannot be drawn until a start date is assigned. |

### Reporting

| Limitation | Details |
|------------|---------|
| **Snapshot diff requires previous domain.json** | Change History is only available if `domain.json` existed before the current pipeline run. First-time runs produce no diff. |
| **Rolling windows need deadlines.json** | If `deadlines.json` is missing, the report falls back to defaults (7 / 30 / 14 days). No error is raised. |

### GUI

| Limitation | Details |
|------------|---------|
| **Drag-and-drop requires tkinterdnd2** | If the package is missing, drag-and-drop is disabled and the status bar displays a warning: "⚠ Drag-and-drop unavailable (install tkinterdnd2)" |
| **PDF generation requires Chrome or Chromium** | The headless PDF converter searches OS-appropriate paths (Windows: Chrome/Edge, Linux: `google-chrome`/`chromium`/`chromium-browser`, macOS: `Applications/` bundles) and falls back to `$PATH` lookup via `shutil.which()`. If no browser is found, PDF generation is skipped and only Markdown is produced. |
| **Outlook integration is Windows-only** | Email drafting uses `pywin32` COM automation with Microsoft Outlook. Not available on macOS/Linux. |
| **`open_path()` requires a desktop** | File/folder opening uses `os.startfile` (Windows), `open` (macOS), or `xdg-open` (Linux). Returns `False` gracefully on headless systems. |
| **No concurrent editing** | The application assumes a single user. Multiple instances editing the same workbook will cause data loss. |
| **Gantt dark mode is manual** | The Gantt canvas has its own "Dark Mode" checkbox (Tk Canvas doesn't inherit CTk themes). Colors are configured in `theme.json` under `gantt_colors_dark`. |

### Profile System

| Limitation | Details |
|------------|---------|
| **Last-profile deletion creates fallback** | Deleting the only profile auto-generates a "Default" fallback — the app always has at least one entry |
| **Company folder name must be unique** | Two profiles with the same `company` will share data directories |
| **Profile bundles are ZIP-based** | `.pmprofile` is a standard ZIP archive containing the profile directory + a `_profile.yaml` manifest |

### Platform Compatibility

| Feature | Windows | Linux / Codespace | macOS |
|---------|---------|-------------------|-------|
| GUI (customtkinter) | Full | Full (needs X11/Xvfb) | Full |
| Drag-and-drop (`tkinterdnd2`) | Yes | No (package is Windows-only) | No |
| PDF generation | Chrome / Edge | Chromium / google-chrome | Chrome |
| Email draft (Outlook COM) | Yes | No | No |
| `open_path()` | `os.startfile` | `xdg-open` | `open` |
| Excel workbook I/O | Full | Full | Full |

### Report Generation

| Limitation | Details |
|------------|---------|
| **Weekly lookback is Monday-anchored** | "Recently Completed" always looks back to the previous Monday, not a rolling 7-day window |
| **Deliverable history is 30 days** | The "Last 30 Days" section has a fixed window, not configurable |
| **Overview formulas assume current schema** | If the workbook is hand-modified such that sheet names or column positions change, the Overview formulas will break |
