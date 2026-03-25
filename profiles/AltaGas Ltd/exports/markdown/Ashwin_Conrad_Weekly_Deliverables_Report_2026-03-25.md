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

# Weekly Deliverables Report — March 25, 2026
**Ashwin Conrad** | Engineering Co-op Student | AltaGas Ltd.

---

## Executive Summary

> This reporting period, the active workload includes **3** high-priority project(s) actively progressing across All, N/A; **2** medium-priority project(s) being completed with available time; **10** recurring weekly task(s); **2** background item(s) progressed opportunistically. No projects were closed this reporting period — current deliverables are multi-week efforts progressing through their respective milestones.

## Site Support Distribution

| Site | Active Tasks | % of Active | Completed (Historical) | % of Completed |
| --- | --- | --- | --- | --- |
| All | 4 | 24% | 0 | — |
| Harmattan / EEEP | 1 | 6% | 0 | — |
| Multiple | 3 | 18% | 0 | — |
| PSGP-1 Dimsdale / Townsend | 1 | 6% | 0 | — |
| Unassigned / Internal | 8 | 47% | 0 | — |

## Workload Priority Distribution

| Priority | Count | % of Workload |
| --- | --- | --- |
| <span class="badge-critical">P1 Urgent</span> | 4 | 24% |
| <span class="badge-high">P2 High</span> | 7 | 41% |
| <span class="badge-medium">P3 Medium</span> | 3 | 18% |
| <span class="badge-low">P4 Low</span> | 1 | 6% |
| <span class="badge-bg">P5 Background</span> | 2 | 12% |


<div class="page-break"></div>

## Priority Spotlight — Top Active Work

### <span class="badge-high">P2 High</span>  Dashboard Development & Deployment

**Supervisor:** Kurt MacKay &nbsp;|&nbsp; **Site:** All &nbsp;|&nbsp; **Status:** Completed

> Dashboard built, deployed, and in use. Historical data loaded.

### <span class="badge-high">P2 High</span>  Auto-Triggered Email Data Pipeline

**Supervisor:** Kurt MacKay &nbsp;|&nbsp; **Site:** N/A &nbsp;|&nbsp; **Status:** Not Started

> 

### <span class="badge-high">P2 High</span>  Inspection Scope Tool - Development

**Supervisor:** Kurt MacKay &nbsp;|&nbsp; **Site:** N/A &nbsp;|&nbsp; **Status:** Completed

> Tool is complete and currently in active use.


<div class="page-break"></div>

## Deliverable Breakdown

### SCE Identification - Completed Facilities

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Collect SDKs and P&IDs for all facilities | Completed | 100% | Gather Safety Data Knowledge packages and P&ID drawings for every facility in scope. |
| Define SCE identification methodology and criteria | Completed | 100% | Establish the criteria for classifying an element as safety-critical based on industry standards and AltaGas policies. |
| Complete SCE identification for well-documented facilities | Completed | 100% | Walk through P&IDs, identify all SCEs, and log each element per facility. |
| Build SCE master register for completed facilities | Completed | 100% | Compile all identified SCEs into a structured register with tag numbers, descriptions, and facility assignments. |

### SCE Identification - Harmattan & EEEP

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Assess Harmattan SDK gaps - identify missing P&ID references | Completed | 100% | Catalog which tags in the Harmattan SDK lack P&ID cross-references and determine scope of the gap. |
| Assess EEEP SDK gaps - identify missing P&ID references | Completed | 100% | Catalog which tags in the EEEP SDK lack P&ID cross-references and determine scope of the gap. |
| Develop alternative mapping approach for tag-to-SCE identification | In Progress | 60% | Create a methodology to identify SCEs at sites where SDKs do not map tags to P&IDs directly. |
| Complete SCE identification for Harmattan | In Progress | 30% | Apply alternative mapping and complete the SCE register for Harmattan. |
| Complete SCE identification for EEEP | In Progress | 20% | Apply alternative mapping and complete the SCE register for EEEP. |

### BAHX Technical Analysis

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Collect BAHX operating data and inspection records | Completed | 100% | Gather design datasheets, operating parameters, and historical inspection reports for all BAHX units. |
| Identify failure modes and risk factors | Completed | 100% | Evaluate common BAHX failure mechanisms (mercury embrittlement, thermal shock, fouling, corrosion) and apply to each uni |
| Complete risk ranking of all BAHX units | Completed | 100% | Rank each BAHX unit by risk based on operating conditions, age, inspection findings, and failure mode applicability. |
| Finalize analysis conclusions and recommendations | Completed | 100% | Summarize findings and develop recommended actions for each unit. |

### BAHX Final Report

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Draft report - methodology, scope, and background | Completed | 100% | Write introductory sections covering the study scope, BAHX background, and methodology. |
| Draft report - analysis results and risk rankings | Completed | 100% | Write the core technical sections presenting per-unit findings and risk rankings. |
| Draft report - recommendations and action plan | In Progress | 60% | Write the recommendations section with proposed inspection, monitoring, and replacement actions. |
| Incorporate vendor cost and lead-time data (post Apr 1 meeting) | Not Started | 0% | After the April 1st vendor meeting, add replacement unit cost and lead-time info to the report. |
| Final review, formatting, and report submission | Not Started | 0% | Proofread, format per AltaGas standards, and submit the final BAHX report. |

### Dashboard Development & Deployment

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Gather historical corrosion coupon data for all facilities | Completed | 100% | Collect and clean all available historical corrosion coupon measurement data. |
| Design and build Power BI data model | Completed | 100% | Create the data model, relationships, and DAX measures for corrosion tracking. |
| Build dashboard visuals and report pages | Completed | 100% | Create all report pages: facility overview, trend charts, coupon comparison, and alerts. |
| Deploy to Power BI Service and validate with stakeholders | Completed | 100% | Publish to the workspace, share with stakeholders, and incorporate feedback. |

### Auto-Triggered Email Data Pipeline

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Define email ingestion requirements and data format | Not Started | 0% | Document the email source, attachment format, field mapping, and expected cadence. |
| Build email-triggered Power Automate / Logic App flow | Not Started | 0% | Create the automated flow that monitors the mailbox and triggers data extraction on new messages. |
| Build data transformation and loading step | Not Started | 0% | Parse emailed data, clean and transform to match the Power BI data model, and load into the dataset. |
| End-to-end pipeline testing and error handling | Not Started | 0% | Test the full pipeline with sample and live emails; add error notifications and retry logic. |
| Deploy pipeline to production | Not Started | 0% | Promote the pipeline to production and confirm automatic data refresh is working. |

### Inspection Scope Tool - Development

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Define inspection scope requirements and inputs | Completed | 100% | Identify all required inputs, logic, and output formats for generating inspection scopes. |
| Develop inspection scope generation logic | Completed | 100% | Implement the core logic to produce inspection scopes from input data. |
| Test and validate with real inspection data | Completed | 100% | Run the tool against real-world data and confirm output accuracy with engineering. |
| Deploy tool for active use | Completed | 100% | Package and deploy the tool so the team can use it in daily workflows. |

### Maximo Tag Matching

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Export Maximo asset database for all facilities | Completed | 100% | Pull full asset lists from Maximo for every facility in scope. |
| Build tag matching logic and automated comparison | Completed | 100% | Create matching script/process to compare SCE tag numbers against Maximo records. |
| Run initial match - resolve easy hits (~45% matched) | Completed | 100% | Execute first matching pass; resolve tags with direct exact matches. |
| Investigate and resolve unmatched tags (~55% remaining) | In Progress | 20% | Manually review remaining unmatched tags - naming discrepancies, missing Maximo entries, decommissioned equipment. |
| Produce final Maximo match report with gap summary | Not Started | 0% | Document match rate, root causes of mismatches, and recommended Maximo updates. |

### SCE Site Review Meetings

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Prepare site-specific SCE summary packages | Not Started | 0% | Create a per-facility SCE summary with tag lists, Maximo match rates, and gap analysis. |
| Schedule and conduct site review meetings | Not Started | 0% | Coordinate with site leads to schedule and hold review meetings for all completed facilities. |
| Document action items and findings from site meetings | Not Started | 0% | Capture feedback, corrective actions, and follow-up items from each site review. |

### BAHX Presentation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Outline presentation structure and key messages | In Progress | 50% | Define slide flow: background, methodology, key findings, risk rankings, recommendations. |
| Draft presentation slides | Not Started | 0% | Build all slides with data, charts, and summary tables from the report. |
| Add vendor cost and lead-time slides (post Apr 1 meeting) | Not Started | 0% | After the vendor meeting, add replacement cost and timeline slides. |
| Finalize and review presentation | Not Started | 0% | Polish visuals, review with supervisor, and finalize for delivery. |

### BAHX Vendor Meeting - April 1

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Prepare BAHX unit specs and questions for vendor | In Progress | 30% | Compile the specs of current BAHX units and prepare a list of questions about cost, lead time, and replacement options. |
| Attend vendor meeting and capture notes | Not Started | 0% | Attend the April 1st meeting; record cost quotes, lead times, and configuration options. |
| Summarize vendor data into cost/lead-time table | Not Started | 0% | Organize vendor quotes into a structured table for inclusion in the report and presentation. |

### Corrosion Dashboard Handoff Documentation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Document data model, DAX measures, and data sources | Not Started | 0% | Write technical docs covering the Power BI data model, all DAX formulas, and data source connections. |
| Document automated pipeline architecture and configuration | Not Started | 0% | Write a guide covering the email pipeline: flow triggers, data transformations, error handling, and monitoring. |
| Create user guide for dashboard consumers | Not Started | 0% | Write a guide for end-users explaining how to navigate the dashboard, interpret the visuals, and export data. |
| Conduct handoff walkthrough with successor | Not Started | 0% | Walk through all documentation and systems live with the person taking over the dashboard. |

### Inspection Scope Tool - Handoff Documentation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Write technical documentation - code architecture and logic | Not Started | 0% | Document the tool's code structure, key modules, and generation logic for future developers. |
| Write user guide - how to run the tool and interpret outputs | Not Started | 0% | Create a step-by-step user guide covering inputs, execution, and output interpretation. |
| Document known limitations and future improvement ideas | Not Started | 0% | List any known edge cases, limitations, and potential enhancements. |
| Conduct handoff walkthrough | Not Started | 0% | Walk through the tool, documentation, and codebase with the designated successor. |

### BAHX SOP Review

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Request SOPs for all BAHX-equipped facilities | Completed | 100% | Contact operations/document control to obtain current SOPs covering BAHX units. |
| Review SOPs for BAHX-related comments and restrictions | Not Started | 0% | Read through received SOPs and extract any operational notes, startup/shutdown cautions, or maintenance remarks about BA |
| Incorporate SOP findings into BAHX report | Not Started | 0% | Add any relevant SOP observations to the final report and recommendations. |

### SCE - On-Hold Facilities (PSGP-1 Dimsdale & Townsend)

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Monitor PSGP-1 Dimsdale SDK validation progress | On Hold | 0% | Track SDK validation status; confirm when validated SDK is available for SCE work. |
| Monitor Townsend SDK validation progress | On Hold | 0% | Track SDK validation status for Townsend; confirm when validated SDK is ready. |
| Complete SCE identification for PSGP-1 Dimsdale | Not Started | 0% | Once SDK is validated, perform full SCE identification using the confirmed P&IDs. |
| Complete SCE identification for Townsend | Not Started | 0% | Once SDK is validated, perform full SCE identification using the confirmed P&IDs. |

### PI Vision Screen Cleanup - Units, Tags, and Navigation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Units cleanup - remove manual overrides, pull from PI tags | Ongoing | 5% | Remove manually typed display units and update each data link to pull units directly from the live PI tag configuration. |
| Tag configuration review - flag misconfigured tags | Ongoing | 5% | Flag any tags requiring improved configuration (naming alignment, missing attributes, incorrect engineering units). |
| Screen linking - add or correct navigation links | Ongoing | 5% | Add or correct navigation links between screens; reference PFDs to ensure asset relationships are accurate. |

### AI & Python Applications - Exploration & Prototyping

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Explore AI-assisted workflow opportunities | Ongoing | 20% | Identify use cases where AI or ML could improve engineering efficiency at AltaGas. |
| Evaluate SOP automation feasibility | Ongoing | 10% | Assess whether AI can standardize or generate SOPs programmatically. |
| Investigate ML models on PI data for operational insights | Ongoing | 5% | Prototype ML approaches for anomaly detection or optimization using PI historian data. |


<div class="page-break"></div>

## Weekly Recurring Tasks

| Title | Site | Status | Priority |
| --- | --- | --- | --- |
| SCE Identification - Completed Facilities | Multiple | Completed | <span class="badge-critical">P1 Urgent</span> |
| SCE Identification - Harmattan & EEEP | Harmattan / EEEP | In Progress | <span class="badge-critical">P1 Urgent</span> |
| BAHX Technical Analysis | Multiple | Completed | <span class="badge-critical">P1 Urgent</span> |
| BAHX Final Report | N/A | In Progress | <span class="badge-critical">P1 Urgent</span> |
| Maximo Tag Matching | All | In Progress | <span class="badge-high">P2 High</span> |
| SCE Site Review Meetings | All | Not Started | <span class="badge-high">P2 High</span> |
| BAHX Presentation | N/A | In Progress | <span class="badge-high">P2 High</span> |
| BAHX Vendor Meeting - April 1 | N/A | In Progress | <span class="badge-high">P2 High</span> |
| BAHX SOP Review | Multiple | In Progress | <span class="badge-medium">P3 Medium</span> |
| SCE - On-Hold Facilities (PSGP-1 Dimsdale & Townsend) | PSGP-1 Dimsdale / Townsend | On Hold | <span class="badge-low">P4 Low</span> |

## Background & Lower Priority Work

| Title | Supervisor | Site | Status | Priority |
| --- | --- | --- | --- | --- |
| PI Vision Screen Cleanup - Units, Tags, and Navigation | Dustin MacDonald | All | Ongoing | <span class="badge-bg">P5 Background</span> |
| AI & Python Applications - Exploration & Prototyping | Self-Directed | N/A | Ongoing | <span class="badge-bg">P5 Background</span> |


<div class="page-break"></div>

## Recently Completed Projects (Past Week)

*No projects were completed since last Monday. Current project timelines extend beyond a single reporting period.*

## Deliverables Completed — Last 30 Days

*No projects have been formally completed in the last 30 days. Active work items are longer-duration efforts with deliverables expected in upcoming reporting periods.*

## Work Assigned by Supervisor

| Supervisor | Active Assignments | % of Workload |
| --- | --- | --- |
| Kurt MacKay | 15 | 88% |
| Dustin MacDonald | 1 | 6% |
| Self-Directed | 1 | 6% |

---

## Looking Ahead

> Heading into next week, primary focus will remain on **SCE Identification - Completed Facilities**, **SCE Identification - Harmattan & EEEP**, **BAHX Technical Analysis**. Lower-priority items will be advanced as capacity allows.
