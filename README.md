# ProjectManager

A desktop Python application for managing engineering deliverables, tracking projects, and auto-generating branded weekly reports. The data layer is JSON-first (`domain.json` is the source of truth) with the Excel workbook as a rendered downstream artifact.

Built for managing tasks across multiple sites, supervisors, and priority levels, then producing polished PDF and Markdown reports for management.

---

## Table of Contents

- [Core Goals](#core-goals)
- [Features at a Glance](#features-at-a-glance)
- [Getting Started](#getting-started)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [GUI Features](#gui-features)
- [CLI Features](#cli-features)
- [Dependencies](#dependencies)
- [Further Reading](#further-reading)

---

## Core Goals

- **Eliminate manual report writing** — auto-generate branded PDF/Markdown/Excel reports from live task data
- **Single place for all tasks** — manage priorities, statuses, and updates in one workbook
- **At-a-glance workload visibility** — live Dashboard with stat cards, priority breakdowns, and site distribution
- **Organized project files** — per-task attachments, linked folder locations, and timestamped activity logs
- **Multi-profile support** — switch between work contexts (e.g. AltaGas, Personal, UA FSAE) without separate installs
- **Capacity-aware scheduling** — daily hours budget prevents overbooking, with over-capacity warnings

---

## Features at a Glance

| Feature | Description |
|---|---|
| **Hierarchical Task Management** | Projects → Tasks → Deliverables with full CRUD |
| **Auto-Completion Detection** | Tasks marked "Completed" automatically get a date stamp; parent projects update when all tasks are done |
| **Report Pipeline** | One-click generation: completions → overview → Timelines/Gantt sync → Excel snapshot → Markdown → PDF |
| **Live Dashboard** | Stat cards, priority breakdown bars, recently completed list, site distribution, priority spotlight |
| **Email Integration** | Opens an Outlook draft with the latest PDF attached and a time-aware greeting |
| **Drag-and-Drop Attachments** | Drag files onto the task treeview to attach them (via `tkinterdnd2`) |
| **Linked Folders** | Associate a network/local folder with each task; open it in Explorer with one click |
| **Task Notes / Activity Log** | Timestamped notes per task stored in JSON — quick status updates without editing the workbook |
| **Task Duplication** | Clone a task pre-filled with its data for recurring work |
| **Gantt Chart** | Auto-generated sheet with conditional formatting (status-based cell fills, daily/weekly granularity) |
| **Timelines Sheet** | VLOOKUP-driven sheet that stays in sync with Projects/Tasks/Deliverables automatically |
| **Capacity-Aware Scheduling** | Daily hours budget cap with over-capacity day warnings |
| **Interactive CLI** | Full subcommand set plus an interactive REPL shell |
| **Multi-Profile** | YAML-driven profile switching; each profile gets isolated data, exports, and attachments |
| **Brand Theming** | AltaGas blue palette across GUI, Excel formatting, and PDF reports |

---

## Getting Started

### Prerequisites

- **Python 3.12+** (global install)
- **Google Chrome or Microsoft Edge** (for headless PDF generation)
- **Microsoft Outlook** (optional — for email draft integration, Windows only)

### Installation

1. **Clone or download** the project to a local folder.

2. **Install dependencies:**
   ```
   python install.py
   ```
   This runs `pip install -r requirements.txt` and installs all required packages.

3. **Configure your profile** — edit `profiles/user_profile.yaml`:
   ```yaml
   active_profile: 0
   profiles:
     - name: Your Name
       role: Your Role
       company: Your Company
       email: you@company.com
       workbook_filename: "Your Workbook.xlsx"
       recipient_name: Manager Name
       recipient_email: manager@company.com
   ```

4. **Place your Excel workbook** in `profiles/<Your Company>/` with the filename matching `workbook_filename` in the YAML.
   Or use the template generator to create a blank one:
   ```
   python -m helpers.schema.template "profiles/Your Company/Your Workbook.xlsx"
   ```

---

## How to Run

### GUI (primary)

```
python scripts/gui.py
```

Opens the desktop application with sidebar navigation: Tasks, Add Task, Generate, Project Timeline, Weekly Planner, Dashboard, Profile Management, and Settings.

### CLI (headless)

```
python scripts/cli.py --help        # All subcommands
```

See [CLI Features](#cli-features) below for the full command reference.

---

## Project Structure

```
ProjectManager/
├── README.md                        ← This file
├── AGENTS.md                        ← Agent guide for AI assistants
├── Overview.md                      ← Quick-reference card
├── install.py                       ← One-time dependency installer
├── requirements.txt                 ← Python package list
├── create_shortcut.ps1              ← Windows desktop shortcut creator
│
├── profiles/                        ← Multi-profile data root
│   ├── user_profile.yaml            ← Profile config (names, roles, workbook filenames)
│   ├── AltaGas Ltd/                 ← Per-company isolation
│   │   ├── <workbook>.xlsx          ← Master workbook (source of truth)
│   │   ├── attachments/             ← Per-task file attachments
│   │   ├── data/                    ← JSON side-car files
│   │   │   ├── domain.json          ← Serialized domain snapshot
│   │   │   ├── task_notes.json      ← Timestamped activity logs
│   │   │   └── task_links.json      ← Linked folder paths
│   │   ├── reports/                 ← Dated Excel snapshots
│   │   └── exports/
│   │       ├── markdown/            ← Dated Markdown reports
│   │       └── pdf/                 ← Dated PDF reports
│   ├── Personal/                    ← Another profile
│   └── UA FSAE/                     ← Another profile
│
├── helpers/                         ← Core library (business logic)
│   ├── domain/                      ← Hierarchical domain model
│   │   ├── base.py                  ← Node base class
│   │   ├── profile.py               ← Profile (root node)
│   │   ├── project.py               ← Project (category, supervisor, site, priority, notes)
│   │   ├── task.py                  ← Task (priority, commentary, scheduled_date)
│   │   ├── deliverable.py           ← Deliverable (percent_complete, time_allocated/spent)
│   │   └── timeline.py              ← Timeline value object
│   ├── schema/                      ← Workbook schema definitions
│   │   ├── sheets.py                ← Sheet names, metadata, categories
│   │   ├── columns.py               ← Column descriptors per sheet
│   │   ├── ids.py                   ← ID generation (P-001, T-001, D-001)
│   │   ├── contracts.py             ← Foreign-key validation
│   │   ├── template.py              ← Blank workbook creator
│   │   ├── integrity.py             ← Timelines/Gantt integrity checks + auto-repair
│   │   ├── timelines.py             ← Timelines sheet sync (VLOOKUP)
│   │   └── gantt.py                 ← Gantt chart builder
│   ├── persistence/                 ← Excel ↔ Domain mapping
│   │   ├── contract.py              ← Load/save orchestration (JSON-first, hash-based sync)
│   │   ├── workbook_reader.py       ← Excel → Domain hierarchy
│   │   ├── workbook_writer.py       ← Domain → Excel (add/update/delete by ID)
│   │   ├── serializer.py            ← Domain ↔ JSON round-trip
│   │   └── field_map.py             ← Bidirectional field name ↔ attribute translation
│   ├── commands/                    ← Business operations
│   │   ├── registry.py              ← @register decorator, invoke(), list_commands()
│   │   ├── domain_service.py        ← GUI mutation service (all 12 project fields)
│   │   ├── task_ops.py              ← CRUD for projects/tasks/deliverables
│   │   ├── report_pipeline.py       ← 9-step report generation pipeline
│   │   └── utilities.py             ← Save, open, email helpers
│   ├── attachments/                 ← Per-task metadata (keyed by task ID)
│   │   ├── service.py               ← File attach/list/open/delete
│   │   ├── links.py                 ← Linked folder CRUD (JSON)
│   │   └── notes.py                 ← Activity log CRUD (JSON)
│   ├── data/                        ← Workbook I/O & parsing
│   │   ├── workbook.py              ← Load workbook, read sheets
│   │   ├── tasks.py                 ← Legacy Task dataclass + cell parsers
│   │   ├── completions.py           ← Completion detection & auto-move
│   │   └── overview.py              ← Excel Overview tab writer
│   ├── reporting/                   ← Report output
│   │   ├── markdown.py              ← Markdown + CSS report builder
│   │   ├── pdf.py                   ← Headless Chrome/Edge PDF conversion
│   │   └── snapshot_diff.py         ← Change tracking between domain snapshots
│   ├── scheduling/                  ← Workload scheduling
│   │   └── engine.py                ← Capacity-aware daily scheduler
│   ├── profile/                     ← Profile & config
│   │   ├── profile.py               ← YAML read/write, profile switching
│   │   ├── config.py                ← Dynamic path getters
│   │   └── portability.py           ← .pmprofile export/import (ZIP bundles)
│   ├── config/                      ← JSON configuration files
│   │   ├── categories.json, status.json, fields.json
│   │   ├── deadlines.json, defaults.json, theme.json
│   │   └── loader.py                ← Cached config loader
│   ├── io/                          ← File & JSON utilities
│   │   ├── files.py                 ← Safe filenames, copy, open, find latest
│   │   ├── json_store.py            ← JSON load/save
│   │   └── paths.py                 ← Centralized path definitions
│   ├── ui/state.py                  ← Persistent UI state (filters, search, treeview)
│   ├── validation.py                ← Input validation for all entity types
│   ├── migration.py                 ← Auto-migrate title-based keys to task IDs
│   └── util/                        ← Shared helpers
│       ├── dates.py                 ← Date formatting, report filenames
│       └── logging.py               ← Callback-based logger
│
└── scripts/                         ← Entry points
    ├── gui.py                       ← GUI launcher shim
    ├── cli.py                       ← CLI launcher shim
    ├── cli/
    │   ├── run.py                   ← CLI orchestrator (argparse subcommands)
    │   └── shell.py                 ← Interactive REPL
    └── gui/
        ├── app.py                   ← App class (shared state, sidebar, pages)
        ├── base_page.py             ← BasePage abstract class
        ├── page_registry.py         ← Declarative page configuration
        ├── ui_theme.py              ← Colors, status/priority constants
        ├── pages/
        │   ├── tasks_page.py        ← Hierarchical task treeview
        │   ├── add_task_page.py     ← New task form
        │   ├── generate_page.py     ← Report generation controls
        │   ├── gantt_page.py        ← Project timeline Gantt view
        │   ├── scheduler_page.py    ← Weekly planner with budget warnings
        │   ├── dashboard_page.py    ← Live summary dashboard
        │   ├── profile_page.py      ← Profile management & workbook import
        │   └── settings_page.py     ← Profile editor & app info
        └── dialogs/
            ├── project_dialog.py    ← Project add/edit modal (12 fields)
            ├── task_dialog.py       ← Task add/edit modal (12 fields)
            ├── deliverable_dialog.py← Deliverable add/edit modal
            ├── task_notes_dialog.py ← Activity log viewer/editor
            └── batch_dialog.py      ← Bulk status/priority/date changes
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  USER INTERFACE                                             │
│  GUI (customtkinter)  ·  CLI (argparse)  ·  REPL (shell)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  COMMAND LAYER  (helpers/commands/)                          │
│  DomainService (GUI) · task_ops (CLI) · registry            │
│  report_pipeline · utilities                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  PERSISTENCE  (helpers/persistence/)                        │
│  contract.py — JSON-first, hash-based sync                  │
│  workbook_reader (Excel → Domain)                           │
│  workbook_writer (Domain → Excel, ID-based CRUD)            │
│  serializer (Domain ↔ JSON) · field_map (name translation)  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  DOMAIN MODEL  (helpers/domain/)                            │
│  Profile → Project → Task → Deliverable                     │
│  Node base class: id, title, parent, status, dates          │
└────────┬─────────────────────────────────┬──────────────────┘
         │                                 │
┌────────▼──────────┐            ┌─────────▼─────────┐
│  SCHEMA            │            │  DATA LAYER       │
│  (helpers/schema/) │            │  (helpers/data/)  │
│  sheets · columns  │            │  workbook I/O     │
│  IDs · FK rules    │            │  completions      │
│  template          │            │  overview writer   │
│  timelines · gantt │            │  cell parsers     │
└────────────────────┘            └───────────────────┘

SUPPORTING LAYERS:
  helpers/attachments/  ── File attach, linked folders, activity notes
  helpers/reporting/    ── Markdown + CSS builder, headless PDF
  helpers/scheduling/   ── Capacity-aware daily scheduler
  helpers/profile/      ── YAML config, profile switching, dynamic paths
  helpers/io/           ── Safe filenames, JSON store, centralized paths
  helpers/util/         ── Date helpers, callback logger
```

### Key Design Patterns

| Pattern | Where | Why |
|---|---|---|
| **Composite Model** | `helpers/domain/` | Profile → Project → Task → Deliverable with parent-chain traversal |
| **Command Registry** | `helpers/commands/registry.py` | GUI buttons and CLI subcommands invoke the same business logic |
| **JSON-First Persistence** | `helpers/persistence/contract.py` | `domain.json` is canonical; workbook is rendered view |
| **Hash-Based Sync** | `helpers/persistence/contract.py` | SHA-256 for external edit detection (immune to OneDrive mtime issues) |
| **Derived Sheets** | `helpers/schema/timelines.py`, `gantt.py` | VLOOKUP formulas auto-sync with data sheets |
| **Late-Binding Paths** | `helpers/profile/config.py` | Paths recomputed at runtime so profile switching works without restart |
| **Field Name Translation** | `helpers/persistence/field_map.py` | Bidirectional mapping between Excel labels and domain attributes |
| **Capacity-Aware Scheduling** | `helpers/scheduling/engine.py` | Respects daily_hours_budget, prevents overbooking |
| **Callback Logging** | `helpers/util/logging.py` | GUI redirects logs to a text widget; CLI uses stdout |
| **Modal Callbacks** | `scripts/gui/dialogs/` | Dialogs accept `on_save` callback — parent stays decoupled |

---

## GUI Features

### Pages (8)

| Page | Description |
|---|---|
| **Tasks** | Hierarchical treeview (Project → Task → Deliverable). Search, filter, priority colour-coding, context menu, drag-and-drop, batch edit. |
| **Add Task** | Form with project selector, status/priority dropdowns, date fields. |
| **Generate** | Buttons: Save Workbook, Generate Reports, Save & Close, Open Latest, Email Report. Live output log. |
| **Project Timeline** | Canvas-based Gantt chart grouped by project with zoom, dark mode, right-click editing. |
| **Weekly Planner** | 7-day × 5-priority grid showing scheduled tasks with daily budget warnings. |
| **Dashboard** | Stat cards, priority breakdown bars, recently completed, site distribution, priority spotlight. |
| **Profile Management** | Two-panel profile editor with import/export (.pmprofile bundles) and live switching. |
| **Settings** | Active profile summary, application paths, appearance toggle (Light / Dark / System). |

### Dialogs (5)

- **Project Dialog** — 12-field add/edit (title, category, description, status, supervisor, site, priority, notes, start, end, deadline, date completed)
- **Task Dialog** — 12-field add/edit (title, supervisor, site, description, commentary, status, priority, start, end, deadline, date completed, scheduled date)
- **Deliverable Dialog** — 9-field add/edit (title, description, status, % complete, time allocated, time spent, start, end, deadline)
- **Task Notes Dialog** — View timestamped activity log and add new entries
- **Batch Edit Dialog** — Apply status, priority, or date shifts to multiple selected tasks at once

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | Switch to Add Task |
| `Ctrl+F` | Focus search box |
| `Ctrl+G` | Generate reports |
| `Ctrl+S` | Save workbook |
| `Ctrl+D` | Switch to Dashboard |
| `Delete` | Delete selected item (cascade) |

---

## CLI Features

```
python scripts/cli.py generate                          # Full 9-step report pipeline
python scripts/cli.py save                              # Save workbook + snapshot
python scripts/cli.py open                              # Open latest report
python scripts/cli.py email                             # Draft Outlook email with PDF
python scripts/cli.py list [--all]                      # Active tasks (--all includes Completed)
python scripts/cli.py shell                             # Interactive REPL
python scripts/cli.py profile [--switch N]              # List or switch profiles
python scripts/cli.py init "Name" "Company"             # Create new profile
python scripts/cli.py project list                      # List all projects
python scripts/cli.py task list [--project P-001]       # List tasks
python scripts/cli.py task add --project P-001 --title "…"
python scripts/cli.py task delete --task-id T-001
python scripts/cli.py deliverable list --task T-001
python scripts/cli.py deliverable add --task T-001 --title "…"
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `openpyxl` | Excel workbook I/O |
| `markdown` | Markdown report rendering |
| `pyyaml` | YAML profile configuration |
| `customtkinter` | Modern Tk GUI toolkit |
| `pywin32` | Outlook COM integration (Windows) |
| `tkinterdnd2` | Drag-and-drop file attachments |

Install via `python install.py` or `pip install -r requirements.txt`.

---

## Further Reading

| Document | Purpose |
|---|---|
| [FEATURES.md](FEATURES.md) | Exhaustive technical reference — domain model, algorithms, GUI details, configs, limitations |
| [AGENTS.md](AGENTS.md) | AI agent guide — mutation APIs, code examples, extension checklists, file layout |
| [Overview.md](Overview.md) | Quick-reference card — data flow, key constraints |
