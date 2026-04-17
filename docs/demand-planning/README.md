# Demand Planning Integration Plan

This folder captures the implementation plan for Demand Planning, with Power Automate + SharePoint List as the target integration direction.

## Why this exists

ProjectManager is currently personal and local-first:

Profile -> Projects -> Tasks -> Deliverables

Demand planning adds a team-facing layer where only project-level forecast data is shared. Personal tasks, notes, and deliverables remain private and local.

## Confirmed Strategy

Primary integration target:
- SharePoint List as the central store for demand-plan submissions
- Power Automate as the ingestion/validation automation layer
- ProjectManager as the local planner and export producer

Given current constraints, the app should be prepared for export-ready data first. Direct authenticated submission can be added later without changing the domain model.

## Architecture Guardrails

1. Keep demand planning separate from personal execution data
- `domain.json` remains personal execution hierarchy (projects/tasks/deliverables)
- demand-plan artifacts live in a sibling file under profile data
- no personal task detail is exported to central demand-planning systems

2. Keep central project governance external
- central project catalog is admin/management owned
- local app does not create or modify central project definitions
- users only select from catalog entries when creating demand-plan rows

3. Keep app behavior resilient and local-first
- planning continues if SharePoint/Power Automate is unavailable
- submission is retriable and auditable
- payload generation is deterministic for easy troubleshooting

4. Keep code modular and testable
- business logic in `helpers/` modules
- GUI pages are thin view/controller layers
- serializers and validators are unit-testable without GUI startup

5. Personal data isolation invariant (CRITICAL)
- changes to the central demand-plan catalog must NEVER delete, modify, or hide personal projects, tasks, notes, or deliverables
- personal projects are independent entities associated with central entries by reference, not owned by them
- if a central catalog entry is removed, the personal project remains intact — the link becomes a stale reference, never a cascade delete
- this rule is non-negotiable and must be enforced at every layer: catalog refresh, team switch, and project lifecycle

6. Association model between personal and central projects
- personal projects may hold a `catalog_ref` field linking to a central project key
- this link is informational — it enables suggestions, reporting, and UX convenience
- it does NOT create lifecycle coupling
- stale references (catalog entry removed) are visually indicated but never auto-resolved destructively

## Proposed Domain Boundary

Demand planning should be represented as an adjacent bounded context, not a patch inside existing scheduler internals.

Suggested module layout:
- `helpers/demand_plan/models.py`
- `helpers/demand_plan/service.py`
- `helpers/demand_plan/validation.py`
- `helpers/demand_plan/export.py`
- `helpers/demand_plan/catalog.py`

Suggested profile data files:
- `profiles/<Company>/data/demand_plan.json`
- `profiles/<Company>/data/demand_plan_actuals.json` (future-facing, optional at first)
- `profiles/<Company>/data/team_project_catalog.json` (cached central catalog)

## Data Model Direction

### 1. Forecast entries (editable only for future periods)

Core fields (the three essentials for demand planning):
- `month` (`YYYY-MM`) — the planning period
- `project_key` (must exist in team catalog) — the central project being forecasted
- `forecast_hours` (decimal, 2-digit precision) — projected hours

Supporting fields (stored but not user-burden for submission):
- `entry_id` (UUID)
- `team_id` (flexible string for now)
- `project_title` (snapshot for readability, carried from catalog)
- `priority_tier` (central-facing, High/Medium/Low — carried from catalog)
- `aux_columns` (dict of additional catalog metadata like category, facility — schema-flexible)
- `submission_status` (`draft`, `ready`, `submitted`, `failed`)
- `updated_at` (ISO timestamp)

### 2. Actuals reflection entries (retroactive, separate track)

Minimum fields:
- `actual_id` (UUID)
- `team_id`
- `month` (`YYYY-MM`)
- `project_key`
- `actual_hours`
- `updated_at`
- `source_note` (optional, manual/system/import)

Actuals are local-only for MVP. Storage and serialization must be export-ready so central integration can be enabled later without schema changes.

This supports comparing intended versus actual distribution without reopening locked forecast months.

### 3. Personal project association (optional field on existing Project entity)

- `catalog_ref` (string, nullable) — reference to a central project key
- informational link only — no lifecycle coupling
- stale references are preserved and visually flagged, never auto-deleted

## Lifecycle Rules

Forecast lifecycle:
- current and future months can be edited freely
- lock occurs at the start of the target month (day 1) — not at the due date
- if the configurable due date has passed but the month has not started, show a warning — do not block
- latest submission overwrites previous for same natural key

Actuals lifecycle:
- prior months can receive actuals updates at any time
- actuals are versioned by timestamp for auditability

Natural key for upsert:
- `UserEmail + TeamId + Month + ProjectKey`

## Monthly Budget Calculation

Formula: `daily_hours_budget * working_days_in_month`

- `daily_hours_budget` comes from the existing profile configuration
- working days = weekdays (Mon–Fri) in the target month
- no holiday calendar in MVP — can be extended later
- the resulting target is a soft guideline, not a hard cap
- show advisory warning if total forecast hours diverge significantly from target
- tolerance range should be configurable, defaulted generously to accommodate personal schedules

## Catalog and Recommendation Logic

Catalog behavior:
- central catalog is periodically refreshed from SharePoint-owned source
- local cache stored as `team_project_catalog.json` — read-only from app perspective
- MVP supports manual refresh button; automatic refresh is architecturally supported but frequency TBD
- stale-catalog threshold is configurable (default suggestion: 30 days since last refresh)
- stale warning is advisory only — no hard block on using stale catalog data

Catalog refresh on team switch:
- when a user changes teams, refresh catalog for the new team immediately
- do NOT purge previously cached catalog entries — they may still be referenced by existing personal projects
- next-month forecast defaults to the new team's catalog

Recommendation behavior (assistant features inside app):
- suggest central projects from prior demand-plan submissions for the same month pattern
- suggest central projects that match active local work (personal projects with `catalog_ref`)
- never create net-new central projects from local app

Local project completion note:
- local completion remains personal and independent from central lifecycle
- completing all local tasks under a central-linked project completes the project locally only
- the central project may still be active — local and central completion semantics are fully decoupled

## SharePoint and Power Automate Contract

Suggested SharePoint list:
- `DemandPlanSubmissions`

Core mandatory rollup columns (the essentials):
- `Team`
- `Month`
- `ProjectKey`
- `ForecastHours`

Supporting columns (carried from catalog, not user-entered):
- `ProjectTitle`
- `PriorityTier`
- additional catalog metadata columns (schema-flexible, mapped from `aux_columns`)

Flow behavior target:
1. Receive export payload (manual upload first)
2. Validate schema version and required fields
3. Resolve submission destination from project key alone — no user burden for auxiliary columns
4. Upsert rows using natural key
5. Return machine-readable result summary (success/errors)
6. Preserve row timestamps for historical trace

## Configurability Requirements

Keep these values configurable (in JSON config), not hardcoded:
- forecast due day (default: day 15 of current month for next-month forecast)
- forecast lock boundary (default: day 1 of target month)
- team id format and validation rules
- catalog column naming and mappings (formerly Group 1 — final name TBD)
- catalog staleness warning threshold (default: 30 days)
- catalog refresh mode flags (manual enabled, auto enabled, auto interval)
- monthly budget formula source (`daily_hours_budget * working_days`)
- budget tolerance range for advisory warnings

## Validation Rules (MVP)

- month must match `YYYY-MM`
- forecast hours must be >= 0 and rounded to 2 decimals
- total monthly forecast hours checked against `daily_hours_budget * working_days` — advisory warning only, no hard rejection
- project key must exist in local team catalog cache
- duplicate entries in one payload collapse deterministically by latest edit time
- edits to months that have already started are rejected with clear error message
- edits after due date but before month start show a warning but are allowed

## Phased Delivery Plan

Phase A - Data foundation
- add demand-plan models (`ForecastEntry`, `ActualEntry`) and JSON storage contract
- add `catalog_ref` optional field to Project entity (informational link, no lifecycle coupling)
- add validators: month format, lock rules, budget advisory
- add migration/version envelope for `demand_plan.json`
- add unit tests for round-trip, lock enforcement, and stale-reference handling

Phase B - Catalog foundation
- add team project catalog cache model and `team_project_catalog.json` storage
- add manual refresh action and staleness check
- add catalog-aware project key validation
- add tests for cache read/write, refresh, and stale-warning rules
- ensure catalog refresh on team switch does NOT purge existing references

Phase C - Forecast UX and commands
- add CLI commands for create/list/export demand-plan entries
- add GUI page for monthly demand-plan editing
- add recommendation hooks: suggest from prior history and active `catalog_ref` links
- add budget target display and advisory warning when hours diverge
- add due-date warning indicator

Phase D - Export and flow contract
- add deterministic CSV/JSON exporters keyed on project key only
- include metadata header (profile, team, month, generated_at, app_version)
- add submission package manifest and result parser
- support retry after partial failures

Phase E - Actuals and insight loop
- add actuals reflection data track (local-only, export-ready schema)
- add forecast vs actual local comparison summaries
- add stale-reference indicators for removed catalog entries
- prepare shape for future Power BI integration

## Risks and Mitigations

Risk: schema drift between app and SharePoint
- Mitigation: versioned payloads, explicit mapping table, preflight checks

Risk: unclear central auth/permissions during early rollout
- Mitigation: keep export-first pattern and delay direct submission dependency

Risk: user confusion between local and central concepts
- Mitigation: explicit labels in UI (Local Project vs Central Demand Project), separate pages/sections

Risk: accidental hardcoding of evolving business vocabularies
- Mitigation: move vocabularies/mappings to config tables via `helpers/config/` pattern, make adapters explicit

Risk: catalog removal triggers personal data loss
- Mitigation: association-by-reference model with stale-reference handling — never cascade-delete personal data from catalog changes

Risk: team switch causes data loss
- Mitigation: catalog refresh is additive; prior team references are preserved; personal projects are never auto-deleted on team change

## Next Implementation Outputs

1. `demand_plan.json` schema v1 draft with examples
2. central catalog cache schema draft
3. Power Automate I/O contract examples (request/response)
4. validation and lock-rule test matrix
5. MVP backlog for Phases A and B
