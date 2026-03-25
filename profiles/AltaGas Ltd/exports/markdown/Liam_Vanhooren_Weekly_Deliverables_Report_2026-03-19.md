<style>
:root {
  --ag-dark: #003DA5;
  --ag-mid: #336BBF;
  --ag-light: #B3CDE3;
  --ag-wash: #E6EFF8;
}
body {
  font-family: 'Segoe UI', Calibri, Arial, sans-serif;
  color: #222;
  max-width: 850px;
  margin: auto;
  padding: 20px 30px;
  font-size: 11pt;
}
h1 {
  color: var(--ag-dark);
  border-bottom: 3px solid var(--ag-dark);
  padding-bottom: 6px;
  font-size: 1.6em;
}
h2 {
  color: var(--ag-dark);
  border-bottom: 1px solid var(--ag-light);
  padding-bottom: 4px;
  margin-top: 1.2em;
  font-size: 1.25em;
}
h3 {
  color: var(--ag-mid);
  margin-top: 1em;
  font-size: 1.05em;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0 14px 0;
  font-size: 0.9em;
}
th {
  background-color: var(--ag-dark);
  color: #fff;
  padding: 6px 8px;
  text-align: left;
}
td {
  padding: 5px 8px;
  border-bottom: 1px solid var(--ag-light);
  vertical-align: top;
}
tr:nth-child(even) {
  background-color: var(--ag-wash);
}
blockquote {
  border-left: 4px solid var(--ag-mid);
  margin: 8px 0;
  padding: 6px 14px;
  background: var(--ag-wash);
  color: #333;
  font-style: italic;
  white-space: pre-wrap;
}
.badge-critical { background:#c0392b; color:#fff; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:0.85em; }
.badge-high     { background:#e67e22; color:#fff; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:0.85em; }
.badge-medium   { background:#f39c12; color:#fff; padding:2px 8px; border-radius:4px; font-size:0.85em; }
.badge-low      { background:#7f8c8d; color:#fff; padding:2px 8px; border-radius:4px; font-size:0.85em; }
.badge-bg       { background:#bdc3c7; color:#333; padding:2px 8px; border-radius:4px; font-size:0.85em; }
hr { border: none; border-top: 2px solid var(--ag-light); margin: 18px 0; }
.page-break { page-break-before: always; }
@media print {
  .page-break { page-break-before: always; }
  body { padding: 0; }
}
</style>

# Weekly Deliverables Report — March 19, 2026
**Liam Vanhooren** | Engineering Co-op Student | AltaGas Ltd.

---

## Executive Summary

> This reporting period, the active workload includes **2** high-priority project(s) actively progressing across AFS, Griffith; **1** medium-priority project(s) being completed with available time; **3** recurring weekly task(s); **4** background item(s) progressed opportunistically. No projects were closed this reporting period — current deliverables are multi-week efforts progressing through their respective milestones. **1** item(s) are in a Complete/Pending state awaiting further direction.

## Site Support Distribution

| Site | Active Tasks | % of Active | Completed (Historical) | % of Completed |
| --- | --- | --- | --- | --- |
| AFS | 2 | 18% | 1 | 50% |
| All | 2 | 18% | 0 | 0% |
| Griffith | 1 | 9% | 1 | 50% |
| Harmattan | 1 | 9% | 0 | 0% |
| NP (North Pine) | 1 | 9% | 0 | 0% |
| Pipestone II | 2 | 18% | 0 | 0% |
| RIPET | 1 | 9% | 0 | 0% |
| Unassigned / Internal | 1 | 9% | 0 | 0% |

## Workload Priority Distribution

| Priority | Count | % of Workload |
| --- | --- | --- |
| <span class="badge-high">P2 High</span> | 2 | 20% |
| <span class="badge-medium">P3 Medium</span> | 4 | 40% |
| <span class="badge-low">P4 Low</span> | 1 | 10% |
| <span class="badge-bg">P5 Background</span> | 3 | 30% |


<div class="page-break"></div>

## Priority Spotlight — Top Active Work

### <span class="badge-high">P2 High</span>  AFS PSV 7001 Replacement

**Supervisor:** Cameron Cooper &nbsp;|&nbsp; **Site:** AFS &nbsp;|&nbsp; **Status:** Ongoing

> I have managed a series of bids and found an appropriate PSV to replace PSV 7001. Kenneth and team ordered this Friday March 13. The PSV in question was not traditional and vendors could not provide a true replcement in kind on the timeline that operations required. Cameron approved the replacement, however he has also asked that moving forward I also attempt to complete PSV sizing for the valve.

With a solution now in place, priority is moved from level 1 to level 2 as the operations constraint is resolved

### <span class="badge-high">P2 High</span>  Griffith Butane Emissions Tracker – Scrubber & Well Shaft Additions

**Supervisor:** Cameron Cooper/Farzin Shokoohi &nbsp;|&nbsp; **Site:** Griffith &nbsp;|&nbsp; **Status:** Ongoing

> Well shaft blowdown calculations are complete — volume references extracted from existing vessel/pipe data and integrated successfully.
Progress temporarily delayed while awaiting LSHH (High-High Level) height measurement for the compressor scrubber to finalize its blowdown volume.
Followed up with operations, and LSHH height was provided today, allowing scrubber blowdown calculation to proceed.
Next steps: finalize scrubber volume calculation, add it to the Volume Calcs tab, and create new line items on all monthly tabs.

### <span class="badge-medium">P3 Medium</span>  Create PSV Tags for Boiler PSVs (WO2057188)

**Supervisor:** Cameron Cooper &nbsp;|&nbsp; **Site:** AFS &nbsp;|&nbsp; **Status:** Ongoing

> Preparing to book a meeting with maintenance/engineering support (likely N. Luft or facility engineering contact) to confirm required tag format and scope.


<div class="page-break"></div>

## Weekly Recurring Tasks

| Title | Site | Status | Priority |
| --- | --- | --- | --- |
| RIPET / NP ESV Trial – Data Tracking & Reporting Setup | RIPET & NP (North Pine) | Not Started | <span class="badge-medium">P3 Medium</span> |
| Pipestone II – Sample Point Tag Mapping & Weekly TDE Data Refresh | Pipestone II | Ongoing | <span class="badge-medium">P3 Medium</span> |
| Weekly & Monthly MOC Reporting – Power BI, Excel, and PowerPoint Generation | All | Ongoing | <span class="badge-medium">P3 Medium</span> |

## Background & Lower Priority Work

| Title | Supervisor | Site | Status | Priority |
| --- | --- | --- | --- | --- |
| RFI Review & NCR Investigation Support | Mark Mcleod | Pipestone II | Ongoing | <span class="badge-low">P4 Low</span> |
| Harmattan C3 Booster Study – Report Update & Follow-Up Discussion | Jordy Flemming | Harmattan | Ongoing | <span class="badge-bg">P5 Background</span> |
| PI Vision Screen Cleanup – Units, Tag Configuration, and Navigation Links | Dustin MacDonald | All | Ongoing | <span class="badge-bg">P5 Background</span> |
| AI & Python Applications for Workflow Automation and Operational Optimization | Self‑Directed (Personal Development Initiative) | N/A | Ongoing | <span class="badge-bg">P5 Background</span> |

## Complete / Pending — Awaiting Further Direction

*These items have reached a deliverable milestone but remain open pending follow-up scope or re-activation.*

| Title | Supervisor | Site | Commentary | Priority |
| --- | --- | --- | --- | --- |
| PSM Roadmap Upcoming Continuation and Support | Charles Vincent | RIPET (with possible expansion to other facilities) | Received email indicating potential next steps: supporting MOC close‑out tracking across additional facilities.

Current deliverables are completed. 

Pending further direction and anticipated involve | <span class="badge-bg">P5 Background</span> |


<div class="page-break"></div>

## Recently Completed Projects (Past Week)

*No projects were completed since last Monday. Current project timelines extend beyond a single reporting period.*

## Deliverables Completed — Last 30 Days

*No projects have been formally completed in the last 30 days. Active work items are longer-duration efforts with deliverables expected in upcoming reporting periods.*

## Work Assigned by Supervisor

| Supervisor | Active Assignments | % of Workload |
| --- | --- | --- |
| Cameron Cooper | 2 | 20% |
| Dustin MacDonald | 2 | 20% |
| Cameron Cooper/Farzin Shokoohi | 1 | 10% |
| Jordy Flemming | 1 | 10% |
| Mark Mcleod | 1 | 10% |
| Self‑Directed (Personal Development Initiative) | 1 | 10% |
| Steve Kingdom | 1 | 10% |
| Loni Van der lee | 1 | 10% |

---

## Looking Ahead

> Heading into next week, primary focus will remain on **AFS PSV 7001 Replacement**, **Griffith Butane Emissions Tracker – Scrubber & Well Shaft Additions**, **Create PSV Tags for Boiler PSVs (WO2057188)**. Lower-priority items will be advanced as capacity allows.
