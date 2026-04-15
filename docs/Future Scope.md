# Future Scope

This document captures important future scope and strategic context as ProjectManager continues to evolve. **None of this is slated for immediate implementation** — these are ideas and constraints that must inform architectural decisions even at this early stage.

---

## 1. Distribution & Packaging

### The Problem

The end goal is to package this as an app that people at AltaGas can download and use. Not everyone is familiar with Python, Git, or command-line tools. The experience must be as close to "install and run" as possible.

### Options to Explore

| Approach | Pros | Cons | User Needs |
|----------|------|------|------------|
| **PyInstaller / cx_Freeze** | Single `.exe`, no Python install required, works offline | Large bundle size (~100–200 MB), OS-specific builds, harder to update | Nothing — just run the `.exe` |
| **MSIX / Windows Store** | Clean install/uninstall, auto-updates via Store, IT-friendly | Requires signing cert, Store review process, Microsoft packaging overhead | Windows Store access |
| **GitHub Releases + installer script** | Simple to publish, versioned, familiar to technical users | Requires Python pre-installed (or bundled), less polished UX | Python 3.12+, download from GitHub |
| **Microsoft Fabric / Power Platform** | Enterprise integration, SSO, centralized data, management-friendly | Major architectural pivot, likely rewrite of the UI layer, licensing costs | Microsoft 365 account |
| **Electron / Tauri wrapper** | Cross-platform desktop app feel, can embed Python backend | Added complexity (JS layer), larger bundle, two runtimes to maintain | Nothing — just run the app |
| **Web app (Flask/FastAPI + hosted)** | Zero install, centralized updates, accessible from anywhere | Needs hosting infrastructure, shifts from local-first to server-dependent | Browser + network access |

### Recommendations & Open Questions

- **Short term**: PyInstaller is the most pragmatic path. Bundle the app as a single `.exe` for Windows. Users double-click to run. No Python, no Git, no terminal.
- **Medium term**: GitHub Releases with an auto-updater. Each release publishes a new `.exe`, and the app checks for updates on launch.
- **Long term**: If demand planning integration (see §2) pushes toward centralized data, the architecture may eventually need a web backend — at which point a lightweight web UI or Electron wrapper becomes more appropriate.

**Questions to resolve:**
- What is AltaGas IT policy on installing unsigned executables? Do we need a code-signing certificate?
- Is there an internal software distribution channel (SCCM, Intune, internal portal)?
- Does the app need to work offline, or can we assume network access?
- What Python version can we lock to? PyInstaller works best with a pinned version.
- Do users need to share a single workbook (e.g., on OneDrive/SharePoint), or does each person have their own?

---

## 2. Demand Planning Integration

### What Is Demand Planning?

A company-wide initiative where employees predict how their hours will be distributed across projects for the **upcoming month**. This rolls up into team-level and company-level views that give management visibility into:

- Overall team priorities and project budgeting
- Where hours are being spent vs. where they should be spent
- Vertical alignment of priorities across teams

### Current Demand Planning Structure

Each demand planning project has these attributes:

| Field | Description | Example |
|-------|-------------|---------|
| **Facility** | The physical site or location | Harmattan, Gordondale |
| **Priority** | Importance ranking | High, Medium, Low |
| **Project** | The project name | "Unit 52 Compressor Overhaul" |
| **Group 1** (working name) | Category/type of work | MOC, Maintenance Capital Project, Asset Support, OMS, etc. |

> **Note**: "Group 1" is a placeholder column header. This should be renamed to something meaningful as the initiative matures — e.g., "Work Category" or "Initiative Type."

### How It Layers onto ProjectManager

The current system hierarchy is:

```
Profile → Projects → Tasks → Deliverables
         (personal)  (personal)  (personal)
```

With demand planning, there is a new conceptual layer:

```
Team Project List (centralized, shared)
    └── User's Projects (personal, may link to a team project or be standalone)
            └── Tasks (always personal)
                    └── Deliverables (always personal)
```

#### Key Design Principles

1. **Tasks and notes are always personal.** The demand planning system does not need to see individual tasks — it only cares about hours allocated to projects.

2. **Most projects are centralized.** A team maintains a known list of projects. Individual users link their work to these projects. This linkage is what feeds the demand planning rollup.

3. **Users can still create standalone projects.** Not everything fits neatly into the team list. Personal or ad-hoc projects must remain possible. These simply don't appear in the demand planning rollup (or appear under a generic "Other" bucket).

4. **Adding new demand planning projects requires approval.** The centralized project list is curated — users cannot unilaterally add to it. This keeps the rollup clean and comparable across team members.

5. **Users belong to a team, and teams have a defined project/category palette.** Profile configuration would need to expand to include team membership and the set of demand planning projects available to that team.

### Integration with the Weekly Planner

#### The Problem with the Current Scheduler

The current weekly planner (`scheduling/engine.py`) operates on a **daily hours budget** model: it distributes tasks across a 7-day × 5-priority grid, allocating hours per day per task. This is deterministic and neat, but it **does not reflect reality**. Day-to-day work is chaotic and unpredictable — you rarely work exactly 2.5 hours on Task A then exactly 1.5 hours on Task B.

#### Proposed Replacement: Monthly Forecast + Weekly Guidance

Instead of prescribing a rigid daily schedule, the system shifts to two layers:

**Layer 1 — Monthly Demand Plan Entry (new)**
- Once per month (or on-demand), the user inputs their predicted hours distribution across demand planning projects for the upcoming month.
- Example: "Next month I expect 40% Compressor Overhaul, 25% MOC Reviews, 20% Asset Support, 15% Other."
- This feeds into the centralized demand planning rollup.

**Layer 2 — Weekly Guidance View (replaces current scheduler)**
- Based on the monthly forecast, the system **recommends** a weekly hours distribution. It does not prescribe what to do on Monday vs. Tuesday.
- The weekly view becomes a **decision-support tool**, not a schedule:
  - Shows recommended hours per project for the week (derived from monthly forecast ÷ ~4.3 weeks)
  - Flags deadlines (past-due in red, upcoming in yellow)
  - Shows actual hours logged vs. forecast (if time tracking is added later)
  - Leaves the specific daily work assignments to the user

**Layer 3 — Daily View (simplified)**
- The current calendar grid could remain but shift to a **deadline-focused** view rather than a task-allocation view.
- Each day simply shows: deadlines due, any flagged items, and a summary of recommended focus areas.

#### How This Would Integrate Architecturally

The scheduling engine (`engine.py`) currently takes tasks + daily budget and produces a `Schedule` (date → priority → task list). The new model would need:

1. **A new data entity**: `DemandPlanEntry` — monthly hours forecast per project/category, stored alongside `domain.json`.
2. **A forecast-to-weekly converter**: Takes the monthly entry and produces weekly recommended distributions, accounting for the number of working days in the month.
3. **The existing scheduler could be retained as an optional "detailed mode"** for users who want granular daily planning, while the new demand plan view becomes the default.
4. **The weekly planner page** (`scheduler_page.py`) would need a redesign — shifting from a rigid grid to a more fluid recommendation + deadline view.

#### Additional Ideas for Improvement

- **Actuals vs. Forecast**: If users log actual hours (even roughly), the system could show drift between forecast and reality mid-month. This is valuable both for the individual and for management.
- **Rolling Forecast**: Instead of a single monthly snapshot, allow users to update their forecast mid-month. The demand planning rollup uses the latest entry.
- **Priority Suggestions**: If the system knows task deadlines and demand plan weights, it could suggest which tasks to focus on this week — not as a rigid schedule, but as a ranked recommendation.
- **Carry-Forward**: If a user doesn't submit a new monthly forecast, the system could carry forward the previous month's distribution as a default (with a warning).

### Data Centralization

This is the primary foreseeable challenge. Each user has their own local app and data, but demand planning requires a centralized rollup.

#### Options for Centralization

| Approach | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **Excel upload to SharePoint** | User exports a demand plan Excel sheet, uploads to a shared folder | Simple, familiar, no infrastructure | Manual, error-prone, no real-time rollup |
| **Shared JSON / OneDrive sync** | Demand plan entries sync via OneDrive to a shared team folder | Automatic, leverages existing infra | Merge conflicts, OneDrive sync latency, file locking issues |
| **Lightweight API (FastAPI)** | Small centralized service that accepts demand plan submissions | Clean, structured, queryable | Requires hosting, authentication, maintenance |
| **Power Automate + SharePoint List** | User clicks "Submit" → Power Automate flow pushes data to a SharePoint List | No custom hosting, IT-friendly, queryable via Power BI | Requires Power Platform licensing, flow maintenance |
| **Email-based submission** | App generates a structured email (or attachment) to a shared mailbox, parsed by a flow | Zero infrastructure on the receiving end | Fragile, hard to maintain, not scalable |

#### Recommendations

- **Start simple**: Excel export to a shared folder. The demand plan output is small (one row per project per user per month). Even at scale, this is manageable.
- **Evolve to Power Automate + SharePoint List** when automation is needed. This fits the AltaGas Microsoft ecosystem and gives management Power BI dashboards for free.
- **Only build a custom API if** the data volume or interaction complexity demands it (e.g., real-time dashboards, approval workflows for new projects).

#### Scale Considerations

The risk is in data accumulation as more teams adopt the system. Some mitigating design choices:

- **Partition by team and month.** Each submission is scoped to (user, team, month). Old months can be archived.
- **Keep the demand plan data separate from personal task data.** The centralized system should never need to see individual tasks, notes, or deliverables — only project-level hour allocations.
- **Design export formats now** even if centralization comes later. If the local app already produces a clean, standardized demand plan export, centralization becomes a matter of plumbing rather than redesign.

**Questions to resolve:**
- Who owns the centralized project list? Is it maintained per-team by a lead, or company-wide by a single admin?
- How often do demand planning projects change? Monthly? Quarterly? This affects how the local app syncs the project list.
- Is there an existing Power BI dashboard or reporting tool that the demand plan data needs to feed into?
- What is the approval workflow for adding new projects to the demand planning list?
- Should the system support retroactive edits to past months' forecasts, or are they locked once submitted?

---

## 3. Architectural Discipline (Immediate Priority)

### The Mandate

As this project expands from a simple legacy tool, **strict modularity and minimal coupling are the #1 priority.** Every piece of new functionality must be designed as an independent, testable module with clearly defined interfaces.

The next series of commits — before any feature expansion — will focus on enforcing this discipline in the existing codebase.

### Current Design Strengths (to preserve)

- **JSON-first data layer**: `domain.json` is the sole source of truth. The workbook is a rendered artifact.
- **Domain model isolation**: `helpers/domain/` contains pure dataclasses with no UI or persistence dependencies.
- **Plugin-style pages**: GUI pages are registered in `page_registry.py` and loaded dynamically. Adding a page requires no changes to `app.py`.
- **Command registry**: CLI commands are `@register`-decorated functions, decoupled from argparse.
- **DomainService as mutation authority**: All GUI mutations route through a single service layer.

### Principles Going Forward

1. **No cross-module side effects.** A function should do what its name says and nothing else. If `set_status()` needs to also update a parent project, that should be an explicit post-hook, not buried logic.

2. **Minimal import depth.** A module should import from its siblings or from `helpers/domain/`. Deep cross-package imports (e.g., a schema module importing from commands) are a code smell.

3. **Interfaces over implementations.** When demand planning or centralization features arrive, they should plug in via well-defined contracts — not by weaving new logic into existing functions.

4. **New pages and tools are self-contained.** A new GUI page should only need: (a) the domain model, (b) the DomainService, (c) its own UI code. It should not reach into other pages or directly call persistence functions.

5. **Test at the boundary.** Each module should be testable in isolation. If a test requires standing up the entire app, the module under test has too many dependencies.

### Specific Refactoring Targets

> These should be evaluated and addressed in the near-term commits:

- Audit `import` chains across all `helpers/` modules — map the dependency graph and identify cycles or unnecessary coupling.
- Ensure the scheduling engine is fully decoupled from the GUI — it should accept plain data and return plain data, with no tkinter references.
- Confirm that `contract.py` is the only module that touches both JSON and workbook files. No other module should perform I/O directly.
- Evaluate whether `task_ops.py` (CLI path) and `domain_service.py` (GUI path) could share more code without introducing coupling — or whether keeping them separate is the right tradeoff for now.

---

## Summary of Priority Order

| Priority | Item | Timeframe |
|----------|------|-----------|
| **1** | Architectural discipline — modular, decoupled, testable | Now (next commits) |
| **2** | Stabilize core features — fix bugs, harden existing functionality | Near term |
| **3** | Demand planning data model — design the `DemandPlanEntry` entity and export format | Medium term |
| **4** | Weekly planner redesign — shift from daily scheduler to monthly forecast + weekly guidance | Medium term |
| **5** | Distribution packaging — PyInstaller `.exe` for internal use | Medium term |
| **6** | Data centralization — SharePoint/Power Automate integration for demand plan rollup | Longer term |
| **7** | Web/cloud migration — only if centralization demands it | Future |