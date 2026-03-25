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

# Weekly Deliverables Report — March 24, 2026
**Ashwin Conrad** | Low Voltage Electrical Lead | UA FSAE

---

## Executive Summary

> This reporting period, the active workload includes **4** urgent-priority item(s) requiring immediate attention; **6** high-priority project(s) actively progressing across UA; **4** recurring weekly task(s). No projects were closed this reporting period — current deliverables are multi-week efforts progressing through their respective milestones.

## Site Support Distribution

| Site | Active Tasks | % of Active | Completed (Historical) | % of Completed |
| --- | --- | --- | --- | --- |
| UA | 14 | 100% | 0 | — |

## Workload Priority Distribution

| Priority | Count | % of Workload |
| --- | --- | --- |
| <span class="badge-critical">P1 Urgent</span> | 4 | 29% |
| <span class="badge-high">P2 High</span> | 7 | 50% |
| <span class="badge-medium">P3 Medium</span> | 3 | 21% |


<div class="page-break"></div>

## Priority Spotlight — Top Active Work

### <span class="badge-critical">P1 Urgent</span>  Harness Schematic Design

**Supervisor:**  &nbsp;|&nbsp; **Site:** UA &nbsp;|&nbsp; **Status:** Completed

> Schematic design phase complete. All circuits defined.

### <span class="badge-critical">P1 Urgent</span>  Harness Shape & Form Board

**Supervisor:**  &nbsp;|&nbsp; **Site:** UA &nbsp;|&nbsp; **Status:** Completed

> Form board built. Harness shape established.

### <span class="badge-critical">P1 Urgent</span>  Shutdown Circuit (SDC) Installation

**Supervisor:**  &nbsp;|&nbsp; **Site:** UA &nbsp;|&nbsp; **Status:** Not Started

> 


<div class="page-break"></div>

## Deliverable Breakdown

### Harness Schematic Design

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Define all electrical circuits and loads | Completed | 100% | Identify every circuit on the car: power, signal, sensor, actuator. |
| Create full electrical schematic | Completed | 100% | Draw complete wiring schematic showing all connections, fuses, relays, and ECU pinouts. |
| Define wire gauges and types per circuit | Completed | 100% | Select appropriate wire gauge, insulation type, and color for each circuit based on current draw. |
| Finalize harness routing layout | Completed | 100% | Define physical routing paths on the chassis for every branch of the harness. |

### Harness Shape & Form Board

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Build harness jig / form board | Completed | 100% | Construct the physical board with standoffs matching chassis routing. |
| Route primary wire paths on form board | Completed | 100% | Lay wires along defined paths, establish branch points and breakouts. |
| Cut wires to length | Completed | 100% | Measure and cut all wires with service-loop allowance per the routing layout. |

### Shutdown Circuit (SDC) Installation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Source and verify SDC components | Not Started | 0% | Confirm all SDC switches, relays, and interlocks are on hand and to spec. |
| Route SDC wiring through harness | Not Started | 0% | Run SDC loop wiring along defined path, maintaining isolation from signal wires. |
| Integrate SDC into harness and test loop continuity | Not Started | 0% | Connect SDC inline with harness, verify the full loop opens/closes correctly. |

### Cost Report Compilation & Submission

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Source pricing for all line items | Not Started | 0% | Obtain unit pricing from suppliers or FSAE standard cost tables for every part. |
| Calculate total BOM cost by assembly | Not Started | 0% | Sum extended costs per assembly and compute harness total. |
| Format cost report per FSAE template | Not Started | 0% | Enter all data into the official FSAE cost report spreadsheet template. |
| Review and submit cost report | Not Started | 0% | Final cross-check against BOM, resolve discrepancies, and submit. |

### Wiring Diagrams & Legends

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Complete circuit wiring diagrams | In Progress | 70% | Draw per-circuit wiring diagrams with pin assignments, wire colors, and routing notes. |
| Create wire color code legend | In Progress | 50% | Document the color coding scheme for every wire function and circuit type. |
| Document connector pinout tables | In Progress | 30% | Create pinout reference tables for every connector on the harness. |
| Create harness assembly drawing | In Progress | 40% | Produce a dimensioned assembly drawing showing all branches, breakouts, and connector positions. |

### Pin & Label All Wires

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Crimp pins and terminals on all wire ends | Not Started | 0% | Crimp correct pin/terminal for each connector type onto every wire. |
| Apply wire labels and heat-shrink IDs | Not Started | 0% | Label every wire at both ends with circuit ID using printed heat-shrink or flag labels. |
| Continuity check on all pinned wires | Not Started | 0% | Verify end-to-end continuity on every crimped and labeled wire. |

### Connector Installation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Install inline connectors | Not Started | 0% | Insert pins into inline connector housings per pinout tables. |
| Install bulkhead and panel-mount connectors | Not Started | 0% | Populate and secure all panel-mount and bulkhead connectors. |
| Verify connector seating and pin retention | Not Started | 0% | Tug-test every pin, confirm TPA clips engaged, and check for backed-out pins. |

### Taping, Sheathing & Sealing

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Tape wire bundles at branch points | Not Started | 0% | Spot-tape and spiral-wrap all branch junctions to secure wire groupings. |
| Apply protective sheathing and loom | Not Started | 0% | Slide braided loom or split conduit over all harness trunks and branches. |
| Seal harness endpoints and grommets | Not Started | 0% | Apply heat-shrink boots, grommets, and sealant at all harness pass-throughs. |
| Final harness QC inspection | Not Started | 0% | Full visual and electrical inspection — continuity, insulation resistance, label check. |

### Assembly Structure & Part Numbers

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Define assembly hierarchy | Not Started | 0% | Break the harness into logical assemblies and sub-assemblies (e.g. front loom, rear loom, engine loom, SDC loop). |
| Create part numbering scheme | Not Started | 0% | Establish a consistent part numbering convention that satisfies FSAE cost report rules. |
| Assign part numbers to all components | Not Started | 0% | Apply part numbers to every wire, connector, terminal, relay, fuse, and consumable. |

### Parts Itemization

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Itemize all wires — gauge, color, length, quantity | Not Started | 0% | List every wire run with its gauge, insulation color, measured length, and quantity. |
| Itemize connectors, pins, and terminals | Not Started | 0% | List every connector housing, pin, socket, seal, and TPA clip with quantity per connector. |
| Itemize consumables — tape, sheathing, heat-shrink, seals | Not Started | 0% | Catalog all consumable materials used in harness finishing with lengths/quantities. |
| Itemize relays, fuses, and miscellaneous electrical components | Not Started | 0% | List all relays, fuse holders, fuses, grounding hardware, and mounting brackets. |

### Design Brief Content Development

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Outline slide content and presentation structure | Not Started | 0% | Define the narrative flow and key talking points for all 6 slides. |
| Slide 1 — Design requirements and constraints | Not Started | 0% | Cover FSAE rules, vehicle electrical requirements, weight/packaging constraints. |
| Slide 2 — Harness architecture and topology | Not Started | 0% | Present the overall harness topology: star vs. bus, branch strategy, node locations. |
| Slide 3 — Wire gauge and connector selection rationale | Not Started | 0% | Justify gauge sizing, connector family choices, and contact ratings. |
| Slide 4 — Routing, packaging, and weight optimization | Not Started | 0% | Explain physical routing decisions, weight trade-offs, and serviceability considerations. |
| Slide 5 — Safety systems and SDC integration | Not Started | 0% | Detail SDC loop design, fail-safe philosophy, and rules compliance. |
| Slide 6 — Validation, testing, and lessons learned | Not Started | 0% | Summarize test plan, validation results, and design iteration takeaways. |

### Design Brief Review & Submission

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Internal team review of design brief | Not Started | 0% | Circulate draft to team leads for feedback. |
| Incorporate feedback and finalize slides | Not Started | 0% | Revise content and visuals based on review comments. |
| Submit design brief | Not Started | 0% | Final export and submission of the 6-slide design brief. |

### Design Binder Compilation

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Compile all wiring schematics and diagrams | Not Started | 0% | Collect final versions of all schematics and wiring diagrams into the binder. |
| Include wire legends and connector pinout documentation | Not Started | 0% | Insert color code legend, pinout tables, and wire schedule. |
| Insert cost report | Not Started | 0% | Add the completed harness cost report section. |
| Insert design brief | Not Started | 0% | Add the 6-slide design brief or its expanded narrative form. |
| Add construction photos and process notes | Not Started | 0% | Document the build process with photos, notes on techniques, and assembly order. |
| Compile test and validation records | Not Started | 0% | Include continuity test logs, insulation resistance results, and any inspection checklists. |

### Final Binder Review & Submission

| Deliverable | Status | % Complete | Description |
| --- | --- | --- | --- |
| Review binder for completeness and consistency | Not Started | 0% | Cross-check all sections against a checklist; ensure no missing documents. |
| Format, bind, and print final document | Not Started | 0% | Final formatting pass, print, and physically bind the design binder. |
| Submit design binder | Not Started | 0% | Deliver the completed design binder. |


<div class="page-break"></div>

## Weekly Recurring Tasks

| Title | Site | Status | Priority |
| --- | --- | --- | --- |
| Design Brief Content Development | UA | Not Started | <span class="badge-high">P2 High</span> |
| Design Brief Review & Submission | UA | Not Started | <span class="badge-medium">P3 Medium</span> |
| Design Binder Compilation | UA | Not Started | <span class="badge-medium">P3 Medium</span> |
| Final Binder Review & Submission | UA | Not Started | <span class="badge-medium">P3 Medium</span> |


<div class="page-break"></div>

## Recently Completed Projects (Past Week)

*No projects were completed since last Monday. Current project timelines extend beyond a single reporting period.*

## Deliverables Completed — Last 30 Days

*No projects have been formally completed in the last 30 days. Active work items are longer-duration efforts with deliverables expected in upcoming reporting periods.*

## Work Assigned by Supervisor

| Supervisor | Active Assignments | % of Workload |
| --- | --- | --- |

---

## Looking Ahead

> Heading into next week, primary focus will remain on **Harness Schematic Design**, **Harness Shape & Form Board**, **Shutdown Circuit (SDC) Installation**. Lower-priority items will be advanced as capacity allows.
