# ProjectManager — Overview

Desktop Python app for managing projects, tasks, and deliverables across multiple user profiles. JSON (`domain.json`) is the sole source of truth; the Excel workbook is a rendered downstream artifact.

## Quick Start

```bash
python install.py                  # install dependencies
python scripts/gui.py              # launch GUI
python scripts/cli.py generate     # generate reports (headless)
python scripts/cli.py --help       # all CLI commands
```

## Data Flow

```
domain.json  ── load ──→  Profile → Projects → Tasks → Deliverables
     ↑                                        │
     │                              DomainService / task_ops
     │                                        │
contract.save()  ←── dual-write ──────────────┘
     ├──→ domain.json  (canonical)
     └──→ workbook.xlsx (rendered view)
```

## Key Constraints

- **JSON is the source of truth** — the workbook is always regenerated from `domain.json`
- **IDs are auto-generated** — `P-001`, `T-001`, `D-001`; never assign manually
- **All mutations dual-write** — `contract.save()` writes JSON then renders the workbook
- **Timelines and Gantt auto-sync** — rebuilt on every save; never edit them directly
- **Hash-based sync** — SHA-256 detects external workbook edits (immune to OneDrive mtime issues)

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Getting started, features overview, project structure, dependencies |
| [AGENTS.md](AGENTS.md) | AI agent guide — APIs, mutation examples, extension checklists |
| [FEATURES.md](FEATURES.md) | Exhaustive technical reference — domain model, algorithms, configs, limitations |
