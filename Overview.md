# ProjectManager — Overview

Desktop Python app for managing projects, tasks, and deliverables across multiple user profiles. JSON (`domain.json`) is the sole source of truth; the Excel workbook is a rendered downstream artifact. Runs locally on Windows or in a GitHub Codespace.

## Quick Start

```bash
python install.py                  # install dependencies (Codespace does this automatically)
python scripts/gui.py              # launch GUI (needs display — use noVNC desktop in Codespace)
python scripts/cli.py list --all   # list all tasks (works everywhere)
python scripts/cli.py generate     # generate reports (headless)
python scripts/cli.py --help       # all CLI commands
```

### Test Profile (for development)

A committed `_TestCompany` profile with 4 projects, 10 tasks, and 10 deliverables is included for development and testing:

```bash
python scripts/cli.py profile --switch 1   # switch to test profile
python scripts/cli.py list --all           # see sample tasks
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
- **Personal data is gitignored** — `profiles/*/` is excluded except the `_TestCompany` test profile

## Platform Compatibility

| Feature | Windows | Codespace (Linux) | Notes |
|---|---|---|---|
| CLI (all commands) | ✅ | ✅ | Fully cross-platform |
| GUI | ✅ | ✅ via noVNC (port 6080) | Needs display server |
| PDF generation | ✅ | ✅ (with Chromium) | Searches OS-appropriate paths |
| Outlook email | ✅ | ❌ (falls back to mailto:) | Windows COM only |
| Drag-and-drop | ✅ | ❌ (warning shown) | Requires tkinterdnd2 |
| Desktop shortcut | ✅ | N/A | `create_shortcut.ps1` |

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Getting started, features overview, project structure, dependencies |
| [AGENTS.md](AGENTS.md) | AI agent guide — APIs, mutation examples, extension checklists |
| [FEATURES.md](FEATURES.md) | Exhaustive technical reference — domain model, algorithms, configs, limitations |
| [docs/GITHUB_GUIDE.md](docs/GITHUB_GUIDE.md) | Plain-language GitHub & Codespace tutorial |
| [docs/REVIEW_CHECKLIST.md](docs/REVIEW_CHECKLIST.md) | Three-gate review checklist (Safety / GitHub-ready / Distribution-ready) |
