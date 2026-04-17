# Demand Planning Clarifications and Decisions

This document tracks open questions, assumptions, and confirmed decisions for the demand planning rollout.

## Confirmed Direction

- Integration target: Power Automate + SharePoint List
- Personal task-level data remains local and private
- Demand-plan dataset is separate from domain.json
- Architecture discipline rules from the restructuring effort remain mandatory

## Ratified Decisions (from latest review)

### Governance

1. Central project list ownership
- Owner: admin/management controlled list in SharePoint
- App rule: local app does not add/edit central project definitions
- User access assumption: users may have visibility and possible edit rights in central tools, but the app will treat catalog as externally governed

2. Project approval workflow
- Out of scope for app MVP
- App requirement: consume periodic central catalog refresh and cache locally by team

3. Personal vs central overlap
- Personal projects cannot modify or extend central demand-plan catalog
- Demand-plan submissions are always against central catalog entries (including broad items like asset support)

### Planning Cadence

4. Forecast editability
- Forecasts are editable while still future-looking
- Users can revise upcoming month allocations as priorities change

5. Forecast due timing
- Due date should be configurable
- Current working assumption: due by day 15 of current month for next-month forecast

6. Past month forecast lock
- Previous months are not editable in forecast mode
- Retroactive reflection is captured in a separate actuals track

7. Actuals reflection
- Keep scope open for month-end actual hours entry
- Primary purpose: compare planned vs actual and improve planning quality over time

### Data Contract

8. Team identifier
- Keep flexible for now (central team id model not finalized)
- Working assumption: team maps to a SharePoint folder/list scope

9. Group 1 replacement
- Final naming is not decided
- Keep schema adaptable and avoid hardcoded column semantics

10. Project suggestion behavior
- App should suggest central projects from:
	- prior demand-plan history
	- active local work patterns
- Suggestions never create central records

11. Local vs central completion semantics
- Local completion remains personal
- Central project lifecycle remains independent

12. Priority handling
- Central demand-plan priority is expected as High/Medium/Low
- Personal task priorities remain user-controlled and independent

13. Source control behavior
- Demand-plan source values are controlled
- Personal planning remains flexible locally

14. Forecast units
- Forecast input unit is hours only
- Monthly target should use budget-based guidance

### Integration and Ops

15. Submission conflict behavior
- Latest submission overwrites prior values for same user/month/project key

16. Data plumbing timing
- Auth and permissions details are unknown for now
- MVP should be export-ready and integration-friendly

17. Failure handling
- Desired: clear user-visible safeguards/notifications on failures
- Detailed operational workflow still pending

### Reporting

18. Reporting maturity
- Current state is early/new
- Expected direction is eventual Power BI integration

19. Mandatory rollup dimensions
- Required: Team, Month, Project, Hours
- Supporting: Category and Facility for discovery/filtering

20. Submission completeness visibility
- Management likely needs this view centrally
- Local app can remain focused on clean submission output

## Overlap and Conflict Resolution

The following proposed decisions remain valid and consistent with your responses:

1. Use month string format `YYYY-MM` everywhere.
2. Use composite natural key, expanded to reduce collisions: `UserEmail + TeamId + Month + ProjectKey`.
3. Treat `ForecastHours` as decimal with 2-digit precision.
4. Preserve historical submission timestamps for auditability.
5. Keep local demand-plan data in `profiles/<Company>/data/demand_plan.json`.
6. Keep demand-planning logic in dedicated `helpers` modules, not GUI pages.
7. Keep scheduler redesign as separate module track; do not patch `engine.py` for MVP.

Notes on adjustments:
- Natural key was expanded with `TeamId` to avoid ambiguity when a user changes teams or works across team scopes.
- Historical record handling is split logically: forecast months lock after period passes, while actuals remain the retroactive channel.

## Ratified Decisions (round 2 — April 2026)

### Forecast Locking and Due Date

21. Forecast lock boundary
- Lock occurs at month start (day 1 of the target month)
- A late submitter can still edit up until the month rolls over
- If the configurable due date has passed but month has not started, show a warning only — do not block edits

22. Monthly budget formula
- Default formula: `daily_hours_budget * working_days_in_month`
- This derives from the existing profile field `daily_hours_budget`
- Working days = weekdays (Mon–Fri) in target month unless a holiday calendar is added later

### Actuals Track

23. Actuals data destination
- Actuals are local-only for MVP
- Design storage and serialization so export can be enabled later without schema changes

### Catalog Refresh

24. Catalog refresh mode
- Support both manual refresh button and automatic refresh
- Automatic refresh frequency is TBD — candidates: on app start, monthly, or on-change detection
- MVP must support at minimum a manual refresh action

25. Catalog staleness policy
- Staleness threshold is tied to refresh frequency and should be configurable
- Default suggestion: warn after 30 days since last refresh
- No hard block on stale catalog — warning only

### Submission Simplicity

26. Core demand-plan payload
- **Only three fields are essential for demand planning: Hours, Project, and Date (month)**
- Category, facility, and priority tier are auxiliary metadata carried from the catalog for search/filtering convenience
- The submission export must resolve the destination from project key alone — no user burden to supply auxiliary columns

### Budget Tolerance

27. Hours tolerance policy
- Soft guidance only — no hard enforcement threshold
- Show an advisory warning if total forecast hours are significantly above or below the monthly budget target
- Account for personal schedules (vacation, overtime, compressed weeks)
- Tolerance range should be configurable but defaulted generously

### Team Changes and Data Isolation (CRITICAL)

28. Team reassignment behavior
- On team switch, update the user's team id and refresh the catalog for the new team
- Do NOT delete previously enrolled personal projects, tasks, or deliverables
- User retains freedom to close out prior work at their own pace
- Next-month forecast should default to the new team's project catalog

29. Personal data isolation invariant
- **Changes to the central demand-plan catalog (including project removal) must NEVER delete, modify, or hide personal projects, tasks, notes, or deliverables**
- Personal projects are independent entities that may be *associated* with a central catalog entry but are not owned by it
- If a central catalog entry is removed, the personal project remains intact — the association becomes a stale reference, not a cascade delete
- The relationship is association-by-reference, not parent-child ownership

30. Association model
- Personal projects can hold a `catalog_ref` field linking them to a central project key
- This link is informational — it enables suggestions and reporting connections
- The link does not create lifecycle coupling: central removal does not trigger local mutation
- Stale references should be visually indicated but never auto-resolved destructively

## Additional Clarifications Needed (round 3)

### Association Model Details

1. How should `catalog_ref` be set on personal projects?
- Option A: user explicitly links a personal project to a catalog entry via a dropdown/search in the project editor
- Option B: system suggests a link during project creation if the title closely matches a catalog entry, user confirms
- Option C: both — manual linking anytime, plus suggestion on create
- This determines UX flow in the Add Project and Edit Project pages

2. How should stale `catalog_ref` values be displayed?
- When a catalog entry is removed but personal projects still reference it:
  - Option A: show a small "unlinked" badge on the project — purely informational
  - Option B: show a warning dialog on next app load listing affected projects
  - Option C: both badge and one-time notification
- The link is never auto-removed regardless of display choice

### Catalog Schema

3. What fields does a catalog entry carry?
- Minimum assumed: `project_key`, `project_title`, `priority_tier`
- Are there additional fixed columns the central catalog will always have (facility, category, etc.)?
- Or should the catalog cache store a flexible `metadata` dict per entry to adapt to future column additions?
- This affects the `team_project_catalog.json` schema design

4. Does the catalog carry any hierarchy (sub-projects, program groupings)?
- Example: "Harmattan" as a facility with multiple sub-projects underneath
- If yes, should the local catalog cache preserve that tree, or flatten to a searchable list?

### Actuals Entry UX

5. When should the system prompt for actuals entry?
- Option A: passive — actuals page is always accessible, user enters when ready
- Option B: active reminder after month end (e.g., first app load in a new month)
- This affects whether we add a notification/reminder hook

6. Should actuals allow unallocated hours?
- Example: 8 hours in a month that don't map to any specific project (admin, training, etc.)
- If yes, should there be a reserved "General/Unallocated" pseudo-project in the actuals schema?

### Budget and Schedule Integration

7. Should the demand-plan forecast feed into the existing weekly planner during MVP?
- Example: if a user forecasts 40 hours on Project X next month, should the weekly planner show a guidance banner?
- Or should the two remain fully independent until the scheduler redesign track?

8. Working days assumption
- For MVP, assume Mon–Fri only (no holiday calendar)?
- If a holiday calendar is desired later, should the config infrastructure be stubbed now (empty list in config JSON)?

### Export and Submission

9. What file format should the initial manual export produce?
- CSV (simplest for Power Automate file trigger)
- JSON (richer, supports nested metadata)
- Both (user selects on export)

10. Should the export include actuals alongside forecasts, or always as separate exports?
- Keeping them separate aligns with the split data model and avoids confusion about what a submission represents

## Implementation Readiness Checklist

- Centralized project list owner identified
- Final SharePoint schema approved
- Flow trigger and auth model approved
- Required vocabularies frozen (team, category, priority tiers)
- Data retention policy defined
- Error handling and support process defined
- MVP acceptance criteria approved

## Next Decision Log Entry Template

When a clarification is resolved, add an entry like:

- Date: YYYY-MM-DD
- Decision: <short title>
- Outcome: <what was decided>
- Impacted modules/config: <paths or logical components>
- Follow-up actions: <tasks to implement>

## Notes

Use this file as a living decision log. Once a clarification is resolved, convert it into a dated decision entry and remove it from open questions.
