# ProjectManager — Agent Guide

## System Overview

This is a desktop Python application for managing projects, tasks, and deliverables across multiple user profiles. The data layer is JSON-first: `domain.json` is the **sole source of truth**, and the Excel workbook is a rendered downstream artifact. Runs on Windows locally or in a GitHub Codespace.

```
Profile → Projects → Tasks → Deliverables
```

Each level has a prefixed ID: `P-001` (Project), `T-001` (Task), `D-001` (Deliverable). The workbook has 6 sheets: Overview, Projects, Tasks, Deliverables, Timelines, and Gantt Chart. Timelines and Gantt are auto-derived — never edit them directly.

### Data Flow

```
domain.json  ─── source of truth ───→  load_profile()
     ↑                                        │
     │                              DomainService mutations
     │                                        │
contract.save()  ←── dual-write ←─────────────┘
     │
     ├──→ domain.json  (canonical)
     └──→ workbook.xlsx (rendered view)
```

- **Load**: `contract.load_profile()` reads JSON. If no JSON exists but a workbook is provided, the workbook bootstraps JSON once.
- **Mutate**: All mutations go through `DomainService` (GUI) or `task_ops` → registry (CLI), both calling `contract.save()`.
- **Save**: `contract.save()` writes JSON first, then renders the workbook.
- **Import from Excel**: `contract.import_from_workbook()` is explicit and user-triggered for when someone edits the Excel directly.
- **Sync Detection**: Hash-based (SHA-256) comparison detects external workbook edits, immune to OneDrive mtime false positives.

---

## Profile System

Profiles are defined in `profiles/user_profile.yaml`. Each profile maps to a company folder under `profiles/<Company>/`.

### Active Profile

```yaml
active_profile: 0
profiles:
  - name: Your Name
    company: Your Company
    workbook_filename: Your Workbook.xlsx
    daily_hours_budget: 8.0
    weekly_hours_budget: 40.0
    # ...

  # Dev / Test profile (committed with sample data)
  - name: "Dev Tester"
    company: "_TestCompany"
    workbook_filename: "TestProjects.xlsx"
    daily_hours_budget: 8.0
```

### Switching Profiles

```bash
python scripts/cli.py profile           # list all profiles
python scripts/cli.py profile --switch 1 # switch to index 1
```

In the GUI, use the sidebar dropdown — switching is live (no restart needed). `reload_profile()` re-reads YAML and refreshes all module globals.

---

## Reading Data (Querying)

### CLI

```bash
python scripts/cli.py project list
python scripts/cli.py task list                    # all tasks
python scripts/cli.py task list --project P-001    # tasks under a specific project
python scripts/cli.py list                         # active tasks (Weekly + Ongoing)
python scripts/cli.py list --all                   # include Completed
python scripts/cli.py deliverable list --task T-001
```

### Programmatic Access (Python)

```python
from helpers.persistence.contract import load_profile
import helpers.profile.profile as pp

profile = load_profile(
    pp.USER_COMPANY,
    profile_name=pp.USER_NAME,
    role=pp.USER_ROLE,
    email=pp.USER_EMAIL,
    phone=pp.USER_PHONE,
    recipient_name=pp.RECIPIENT_NAME,
    recipient_email=pp.RECIPIENT_EMAIL,
    workbook_filename=pp.WORKBOOK_FILENAME,
)

# Query the hierarchy
profile.projects                              # all projects
profile.find_project("P-001")                 # by ID
profile.projects_for_category("Weekly")       # by category
profile.all_tasks                             # flat list of every task
profile.find_task_global("T-005")             # find task across all projects
profile.tasks_for_category("Ongoing")         # all tasks in Ongoing projects
project.tasks_by_priority()                   # sorted by priority
project.tasks_by_status("In Progress")        # filtered by status
task.deliverables                             # deliverables under a task
task.find_deliverable("D-003")                # by ID
```

---

## Mutation Layer — DomainService

**All mutations** should go through `DomainService` (preferred) or `task_ops` via the command registry. Both paths call `contract.save()` which dual-writes JSON + workbook.

### DomainService (GUI path — domain attribute names)

```python
from helpers.commands.domain_service import DomainService

service = DomainService(profile, wb, on_persist=app.mark_dirty)

# Add project (all 12 fields supported)
service.add_project({
    "title": "Site Electrical Audit",
    "category": "Ongoing",
    "supervisor": "Kurt MacKay",
    "site": "Harmattan",
    "priority": 2,
    "notes": "Safety review required first",
    "start": date(2026, 3, 23),
})

# Add task
service.add_task("P-001", {
    "title": "Review wiring diagrams",
    "supervisor": "Kurt MacKay",
    "priority": 2,
    "description": "Review all site wiring diagrams",
    "commentary": "Waiting on drawings",
})

# Add deliverable (time fields preserved)
service.add_deliverable("T-001", {
    "title": "Draft compliance report",
    "status": "Not Started",
    "percent_complete": 0,
    "time_allocated": 4.0,
    "time_spent": 0.0,
})

# Quick setters
service.set_status("T-003", "Completed")    # works on P-/T-/D- IDs
service.set_priority("T-003", 1)

# Move task
service.move_task("T-005", "P-002")

# Reschedule
service.reschedule()                         # recompute daily schedule and persist

# Delete (cascading)
service.delete_task("T-003")
service.delete_project("P-001")
```

### task_ops via Registry (CLI path — Excel field names)

```python
from helpers.commands.registry import invoke

invoke("add_task", wb=wb, project_id="P-001", data={
    "Title": "Review wiring diagrams",
    "Status": "Not Started",
    "Priority": 2,
})
invoke("delete_task", wb=wb, task_id="T-003")
invoke("set_status", wb=wb, item_id="T-003", status="Completed")
```

---

## Task Notes (Activity Log)

```python
from helpers.attachments.notes import add_note, list_notes

add_note("Review wiring diagrams", "Sent drawings to vendor for markup")
notes = list_notes("Review wiring diagrams")  # newest first
```

---

## Linked Folders

```python
from helpers.attachments.links import set_link, get_link

set_link("Review wiring diagrams", r"\\server\projects\electrical-audit")
folder = get_link("Review wiring diagrams")  # returns the path or None
```

---

## Report Generation

Pipeline (`generate_reports()`) executes 9 sequential steps:
1. Captures previous snapshot for change history comparison
2. Detects newly completed tasks → stamps `date_completed`, auto-completes parent projects
3. Syncs domain hierarchy (loads workbook, reconstructs Profile tree, computes snapshot diff)
4. Runs the capacity-aware daily scheduler (respects `daily_hours_budget`)
5. Writes/refreshes the formula-based Overview sheet (with change history if available)
6. Checks Timelines integrity & syncs derived sheets (Timelines + Gantt)
7. Saves the workbook + a dated snapshot to `reports/`
8. Generates Markdown and PDF reports to `exports/`
9. Logs completion summary, returns result dict

---

## Adding a New Field (Schema Extension Checklist)

When adding a new field to a domain entity, update these files in order:

1. **`helpers/schema/columns.py`** — add a `Column(name, type, ...)` entry
2. **`helpers/domain/<entity>.py`** — add the field to the dataclass + `to_dict()`
3. **`helpers/persistence/workbook_reader.py`** — read the new column
4. **`helpers/persistence/workbook_writer.py`** — write the field
5. **`helpers/persistence/serializer.py`** — ensure JSON round-trip
6. **`helpers/config/fields.json`** — add the GUI label → domain attribute mapping
7. **`helpers/persistence/field_map.py`** — add to translation maps
8. **`helpers/commands/domain_service.py`** — add to the `_*_ATTRS` whitelist

---

## Adding a New GUI Page

1. Create `scripts/gui/pages/<name>_page.py` with a `BasePage` subclass
2. Set `KEY`, `TITLE`, and optionally `OPTIONAL = True`
3. Add to `PAGE_REGISTRY` in `scripts/gui/page_registry.py`

No changes to `app.py` needed — pages are loaded dynamically from the registry.

Current pages (8): Tasks, Add Task, Generate, Project Timeline, Weekly Planner, Dashboard, Profile Management, Settings.

---

## Adding a New CLI Command

1. Create a `@register("command_name")` function in `helpers/commands/`
2. Add an argparse subparser in `scripts/cli/run.py`
3. Create a `cmd_<name>` handler in `run.py` that calls `registry_invoke("command_name", ...)`
4. Add the handler to the `dispatch` dict in `main()`

---

## File Layout

```
.devcontainer/
  devcontainer.json            # Codespace setup (Python 3.12, desktop-lite, auto-install)

.gitignore                     # Excludes profiles/*/ (except _TestCompany), caches, secrets

assets/
  icon.ico                     # App icon (Windows shortcut)
  icon_proper.ico              # Alternative icon
  icon_original.png            # Original source image

docs/
  Overview.md                  # quick-reference card
  FEATURES.md                  # exhaustive technical reference
  Future Scope.md              # strategic roadmap (distribution, demand planning)
  ARCHITECTURE_AUDIT.md        # technical debt inventory & fix plan
  GITHUB_GUIDE.md              # plain-language GitHub/Codespace tutorial
  REVIEW_CHECKLIST.md          # three-gate review checklist (Safety/GitHub-ready/Distribution)

setup/
  install.py                   # one-time dependency installer
  create_shortcut.ps1          # Windows desktop shortcut creator
  reset_for_distribution.py    # clean repo for fresh user (preserves _TestCompany)

profiles/
  user_profile.yaml            # all profile definitions
  _TestCompany/                # ★ committed test profile (4 projects, 10 tasks, 10 deliverables)
    data/domain.json           # sample domain data
    data/task_notes.json       # sample activity log
    data/task_links.json       # sample linked folders
  <Company>/                   # real user profiles (gitignored)
    <workbook>.xlsx            # rendered Excel workbook
    data/
      domain.json              # ★ source of truth — serialized domain hierarchy
      task_notes.json          # activity log per task
      task_links.json          # linked folder paths per task
    attachments/               # file attachments by task
    exports/
      markdown/                # generated .md reports
      pdf/                     # generated .pdf reports
    reports/                   # dated workbook snapshots

helpers/
  domain/                      # dataclasses: Profile, Project, Task, Deliverable
  persistence/
    contract.py                # load/save orchestration (JSON-first, hash-based sync)
    serializer.py              # JSON ↔ domain round-trip (schema v2.0 + content hash)
    workbook_reader.py         # Excel → domain (bootstrap / import / schema detection)
    workbook_writer.py         # domain → Excel (render)
    field_map.py               # field name ↔ attr name translation
  commands/
    domain_service.py          # single mutation authority (GUI path)
    task_ops.py                # workbook-level CRUD (CLI path, @register'd)
    registry.py                # @register decorator + invoke()
    report_pipeline.py         # report generation pipeline
  schema/                      # column defs, sheet names, template, timelines, gantt
  scheduling/
    engine.py                  # capacity-aware daily scheduler with hours-budget cap
  profile/
    profile.py                 # YAML management + module globals + reload_profile()
    config.py                  # dynamic path helpers

scripts/
  cli.py                       # CLI entry point (shim)
  gui.py                       # GUI entry point (shim)
  cli/run.py                   # argparse + cmd_* handlers + registry_invoke
  cli/shell.py                 # interactive REPL
  gui/app.py                   # App orchestrator, sidebar, dirty flag, autosave
  gui/base_page.py             # BasePage contract (KEY, TITLE, OPTIONAL)
  gui/page_registry.py         # declarative page config (8 pages)
  gui/pages/*.py               # page modules
  gui/dialogs/*.py             # modal dialogs (5 dialogs)
```

---

## Key Constraints

- **JSON is the source of truth** — `domain.json` is canonical. The workbook is a rendered view.
- **IDs are auto-generated** — never manually assign `P-NNN`, `T-NNN`, or `D-NNN` values.
- **All mutations route through `contract.save()`** — which dual-writes JSON then workbook.
- **Timelines and Gantt auto-sync** — every save rebuilds these sheets. Never edit them directly.
- **Notes and links are keyed by task ID** — legacy title-based keys are auto-migrated on profile load via `helpers.migration`.
- **Status = "Completed" triggers auto-complete** — setting a task to Completed immediately stamps `date_completed` and auto-completes the parent project if all sibling tasks are done. Reopening a task under a Completed project automatically reverts the project to Ongoing. This works across GUI (`DomainService`), CLI (`task_ops`), and the report pipeline reconciliation pass.
- **Profile constants use module attribute access** — after `reload_profile()`, access fresh values via `_profile_mod.USER_COMPANY`.
- **Hash-based sync** — SHA-256 of workbook content for detecting external edits (immune to OneDrive mtime false positives).
- **Personal data is gitignored** — `profiles/*/` is excluded from Git. Only `_TestCompany` (fake data) is committed.
- **Cross-platform** — Windows-only packages (`pywin32`, `tkinterdnd2`) use platform markers in `requirements.txt`. Runtime imports are try/except guarded. `open_path()` and `_find_chrome()` search OS-appropriate locations.
- **Review all changes against the three-gate checklist** — see `docs/REVIEW_CHECKLIST.md` (Safety, GitHub-ready, Distribution-ready).

---

## Future Scope — Awareness for Development

Three planned initiatives will shape this codebase. While none are in progress yet, **all new code must be written with these in mind**. See [Future Scope.md](docs/Future%20Scope.md) for full detail and [docs/ARCHITECTURE_AUDIT.md](docs/ARCHITECTURE_AUDIT.md) for the current technical debt inventory.

### 1. Distribution & Packaging

The app will eventually be distributed as a standalone `.exe` (via PyInstaller) to non-technical users at AltaGas. This means:
- **No hardcoded dev paths.** All file paths must be relative or resolved at runtime via `helpers/profile/config.py`.
- **No assumptions about the Python environment.** Avoid importing packages not in `requirements.txt`.
- **Fail gracefully.** Optional features (Outlook COM, tkinterdnd2, Chrome for PDF) must degrade without crashing.
- **Keep the entry point thin.** `scripts/gui.py` and `scripts/cli.py` are shims — they must stay lightweight so PyInstaller can bundle them easily.

### 2. Demand Planning Integration

Management wants to merge this tool with a team-level demand planning initiative. Key architectural impacts:
- **The Profile model will grow.** Expect new fields: `team`, and a link to a shared/centralized project list. Design new Profile fields to be optional and backward-compatible.
- **Projects may have a `source` flag** (e.g., `"personal"` vs `"demand_plan"`) to distinguish user-created projects from centralized team projects. Do not assume all projects are user-owned.
- **A new entity may appear** — `DemandPlanEntry` (monthly hours forecast per project). This will live alongside `domain.json`, not inside it. Keep the serializer extensible.
- **The weekly planner / scheduling engine will likely be redesigned** to shift from rigid daily hour allocation to monthly forecast → weekly guidance. New scheduling code should be in a separate module, not patched into `engine.py`.
- **Data export matters.** The demand plan data must eventually be exportable (to Excel/SharePoint) for centralized rollup. Design any new data structures with clean `to_dict()` / `from_dict()` round-trips.

### 3. Architectural Discipline (Active Priority)

The immediate development focus before any feature expansion. All new code must:
- **Be modular and self-contained.** New pages, tools, and helpers should have minimal cross-module dependencies.
- **Never bypass the mutation layer.** All writes go through `DomainService` (GUI) or `task_ops` → registry (CLI).
- **Keep business logic out of GUI pages.** Pages should only handle widget creation and event binding. Data computation, filtering, and statistics belong in `helpers/`.
- **Use specific exception handling.** No bare `except Exception: pass`.
- **Be independently testable.** If a function can't be tested without standing up the full app, it has too many dependencies.

See `docs/ARCHITECTURE_AUDIT.md` for the full list of current issues and the prioritized fix plan.

---

## Module Reference

### `helpers/domain/` — Hierarchical Domain Model
| Module | Role |
|--------|------|
| `base.py` | `Node` abstract base — id, title, parent, description, deadline, start/end, status, is_overdue, to_dict/from_dict |
| `profile.py` | `Profile` (root) — owns projects, user metadata, daily_hours_budget, weekly_hours_budget |
| `project.py` | `Project` — project_id (P-NNN), category, supervisor, site, priority, notes, date_completed |
| `task.py` | `Task` — task_id (T-NNN), project_id (FK), priority 1–5, supervisor, site, commentary, scheduled_date, date_completed |
| `deliverable.py` | `Deliverable` — deliverable_id (D-NNN), task_id (FK), percent_complete, time_allocated, time_spent |
| `timeline.py` | `Timeline` frozen value object — duration_days, is_active, contains(date) |

### `helpers/persistence/` — Read/Write Adapters
| Module | Role |
|--------|------|
| `contract.py` | Load/save orchestration — JSON-first with hash-based external edit detection |
| `workbook_reader.py` | Reads 6-sheet schema → hydrated `Profile` tree |
| `workbook_writer.py` | Add/update/delete rows by ID, auto-syncs derived sheets |
| `serializer.py` | JSON ↔ Profile round-trip with `_meta` envelope |
| `field_map.py` | Bidirectional field name ↔ attribute name translation |

### `helpers/commands/` — Command Registry & Operations
| Module | Role |
|--------|------|
| `registry.py` | `@register(name)` decorator, `invoke()`, `list_commands()` |
| `domain_service.py` | GUI mutation service — all 12 project fields, date_completed stamping, reschedule() |
| `task_ops.py` | CRUD with normalization, post-mutate hooks, time field passthrough |
| `report_pipeline.py` | Multi-step report generation pipeline |
| `utilities.py` | Save/snapshot, open latest, Outlook email draft |

### `helpers/scheduling/` — Workload Scheduling
| Module | Role |
|--------|------|
| `engine.py` | Capacity-aware daily scheduler — respects daily_hours_budget, prevents overbooking, daily_hours() and over_capacity_days() helpers |

> **Note:** The scheduling engine will likely be supplemented (not replaced) by a demand-plan-based forecasting module in the future. New scheduling code should be added as a separate module under `helpers/scheduling/`, not patched into `engine.py`. See [Future Scope.md](docs/Future%20Scope.md) §2.
