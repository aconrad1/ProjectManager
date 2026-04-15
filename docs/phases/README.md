# Architecture Audit — Agent Deployment Phases

This directory contains detailed, self-contained task briefs designed for AI agent deployment. Each phase is a subdirectory containing individual task files that can be fed directly to an agent.

## Phase Overview

| Phase | Focus | Items | Effort | Prerequisite |
|-------|-------|-------|--------|--------------|
| [Phase 1](phase-1-foundation/) | Foundation — unblocks everything else | 6 tasks | Small | None |
| [Phase 2](phase-2-separation-of-concerns/) | Separation of concerns — extract business logic from UI | 8 tasks | Medium | Phase 1 |
| [Phase 3](phase-3-thread-safety/) | Thread safety & error handling | 8 tasks | Small–Medium | Phase 1 |
| [Phase 4](phase-4-profile-globals/) | Profile globals refactor — largest structural change | 3 tasks | Large | Phases 1–3 |
| [Phase 5](phase-5-polish/) | Polish — cleanup, tests, table-driven refactors | 5 tasks | Medium | Phases 1–3 |

## Execution Order

- **Phase 1** must be completed first — these are small, safe changes that unlock later work.
- **Phases 2 and 3** can be worked in parallel — they are independent of each other.
- **Phase 4** should be tackled after Phases 1–3 — it touches ~10 files and benefits from a stable codebase.
- **Phase 5** can be interleaved with Phases 2–4 as capacity allows.

## Agent Brief Format

Each task file follows a standard structure:

1. **Objective** — What the agent must accomplish
2. **Audit References** — Links back to the Architecture Audit issue IDs
3. **Affected Files** — Exact file paths and line numbers
4. **Current Code** — The actual code that needs to change (with context)
5. **Required Changes** — Step-by-step implementation instructions
6. **Acceptance Criteria** — How to verify the change is correct
7. **Constraints** — Architectural rules the agent must follow

## Key Constraints (All Phases)

These rules apply to every task and must not be violated:

- **JSON is the source of truth** — `domain.json` is canonical. The workbook is a rendered view.
- **IDs are auto-generated** — never manually assign `P-NNN`, `T-NNN`, or `D-NNN` values.
- **All mutations route through `contract.save()`** — which dual-writes JSON then workbook.
- **No import inversions** — `helpers/` never imports from `scripts/`.
- **No circular dependencies** — all dependencies are acyclic.
- **One issue per commit** — each task file is independently committable.
- **Run tests after each change** — `pytest tests/` must pass after every commit.
- **No bare `except Exception: pass`** — use specific exception types.
- **Business logic belongs in `helpers/`** — GUI pages handle only widgets and event binding.

## Architecture Layers

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

## Data Flow

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
