"""Markdown report builder.

Produces the full Markdown text (with embedded CSS) for the weekly
deliverables report.  Separated from PDF conversion so it can be
tested independently.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from helpers.config.loader import load as load_config
from helpers.domain.profile import Profile
from helpers.domain.task import Task
from helpers.reporting.snapshot_diff import SnapshotDiff
from helpers.util.dates import previous_monday

# ── Priority tiers (mirrored from config, kept local to avoid circular deps) ──
URGENT_PRIORITIES = {1}
HIGH_PRIORITIES = {2}
MEDIUM_PRIORITIES = {3}
LOW_PRIORITIES = {4, 5}

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """\
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
"""

PAGE_BREAK = '\n<div class="page-break"></div>\n'


def _priority_badge(p: int) -> str:
    cls = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "bg"}.get(p, "bg")
    label = {1: "P1 Urgent", 2: "P2 High", 3: "P3 Medium", 4: "P4 Low", 5: "P5 Background"}.get(p, f"P{p}")
    return f'<span class="badge-{cls}">{label}</span>'


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "—"
    return f"{n / total * 100:.0f}%"


def _site_counts(tasks: list) -> Counter:
    c: Counter = Counter()
    for t in tasks:
        site = getattr(t, "site", "") or ""
        sites = [s.strip() for s in site.replace("&", ",").split(",") if s.strip()]
        if not sites or sites == ["N/A"]:
            sites = ["Unassigned / Internal"]
        for s in sites:
            c[s] += 1
    return c


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def build_markdown(
    profile: Profile,
    moved_titles: list[str],
    today: date | None = None,
    *,
    author: str = "",
    role: str = "",
    company: str = "",
    snapshot_diff: SnapshotDiff | None = None,
) -> str:
    """Build the full Markdown text for the weekly report.

    Derives task lists from the domain profile hierarchy.
    Returns the Markdown string (without the CSS preamble — call
    ``save_markdown`` to write the styled file).

    Parameters
    ----------
    snapshot_diff : SnapshotDiff, optional
        If provided, a Change History section is included in the report.
    """
    if today is None:
        today = date.today()

    # Load configurable rolling windows
    try:
        dl_cfg = load_config("deadlines")
    except FileNotFoundError:
        dl_cfg = {}
    recent_days = dl_cfg.get("recent_completed_days", 7)
    extended_days = dl_cfg.get("extended_completed_days", 30)

    # Derive task lists from domain hierarchy
    weekly = profile.tasks_for_category("Weekly")
    ongoing = profile.tasks_for_category("Ongoing")
    completed = profile.tasks_for_category("Completed")

    last_monday = previous_monday(today)
    prev_monday = last_monday - timedelta(days=recent_days)
    extended_cutoff = today - timedelta(days=extended_days)

    active_ongoing = ongoing
    critical = [t for t in active_ongoing if t.priority in URGENT_PRIORITIES]
    high = [t for t in active_ongoing if t.priority in HIGH_PRIORITIES]
    medium = [t for t in active_ongoing if t.priority in MEDIUM_PRIORITIES]
    low = [t for t in active_ongoing if t.priority in LOW_PRIORITIES]

    md: list[str] = []

    # Title
    md.append(f"# Weekly Deliverables Report — {today.strftime('%B %d, %Y')}")
    md.append(f"**{author}** | {role} | {company}\n")
    md.append("---\n")

    # Executive Summary
    md.append("## Executive Summary\n")
    parts = []
    if critical:
        parts.append(f"**{len(critical)}** urgent-priority item(s) requiring immediate attention")
    if high:
        sites: set[str] = set()
        for t in high:
            sites.update(s.strip() for s in t.site.replace("&", ",").split(",") if s.strip())
        parts.append(f"**{len(high)}** high-priority project(s) actively progressing across {', '.join(sorted(sites))}")
    if medium:
        parts.append(f"**{len(medium)}** medium-priority project(s) being completed with available time")
    parts.append(f"**{len(weekly)}** recurring weekly task(s)")
    if low:
        parts.append(f"**{len(low)}** background item(s) progressed opportunistically")

    summary = f"This reporting period, the active workload includes {'; '.join(parts)}."
    if moved_titles:
        summary += f" Completed and archived this cycle: _{', '.join(moved_titles)}_."
    else:
        recent_week_check = [t for t in completed if t.date_completed and t.date_completed >= prev_monday]
        if not recent_week_check:
            summary += (
                " No projects were closed this reporting period — current deliverables are multi-week"
                " efforts progressing through their respective milestones."
            )
    md.append(f"> {summary}\n")

    # Site Support Distribution
    md.append("## Site Support Distribution\n")
    ongoing_sites = _site_counts(active_ongoing + weekly)
    completed_sites = _site_counts(completed)
    all_sites = sorted(set(ongoing_sites.keys()) | set(completed_sites.keys()))
    total_ongoing = sum(ongoing_sites.values())
    total_completed = sum(completed_sites.values())
    rows = []
    for site in all_sites:
        oc = ongoing_sites.get(site, 0)
        cc = completed_sites.get(site, 0)
        rows.append([site, str(oc), _pct(oc, total_ongoing), str(cc), _pct(cc, total_completed)])
    md.append(_table(["Site", "Active Tasks", "% of Active", "Completed (Historical)", "% of Completed"], rows))
    md.append("")

    # Priority Distribution
    md.append("## Workload Priority Distribution\n")
    all_active = active_ongoing + weekly
    total_active = len(all_active)
    prio_counts = Counter(t.priority for t in all_active)
    rows = [[_priority_badge(p), str(cnt), _pct(cnt, total_active)] for p, cnt in sorted(prio_counts.items())]
    md.append(_table(["Priority", "Count", "% of Workload"], rows))
    md.append("")

    # Priority Spotlight
    spotlight = sorted(critical + high + medium, key=lambda t: t.priority)[:3]
    if spotlight:
        md.append(PAGE_BREAK)
        md.append("## Priority Spotlight — Top Active Work\n")
        for t in spotlight:
            md.append(f"### {_priority_badge(t.priority)}  {t.title}\n")
            md.append(f"**Supervisor:** {t.supervisor} &nbsp;|&nbsp; **Site:** {t.site} &nbsp;|&nbsp; **Status:** {t.status}\n")
            md.append(f"> {t.commentary}\n")

    # Deliverable Breakdown
    tasks_with_deliverables = [t for t in all_active if t.deliverables]
    if tasks_with_deliverables:
        md.append(PAGE_BREAK)
        md.append("## Deliverable Breakdown\n")
        for t in sorted(tasks_with_deliverables, key=lambda x: x.priority):
            md.append(f"### {t.title}\n")
            rows = [
                [d.title, d.status, f"{d.percent_complete}%", d.description[:120] if d.description else "—"]
                for d in t.deliverables
            ]
            md.append(_table(["Deliverable", "Status", "% Complete", "Description"], rows))
            md.append("")

    # Weekly Recurring
    md.append(PAGE_BREAK)
    md.append("## Weekly Recurring Tasks\n")
    rows = [[t.title, t.site, t.status, _priority_badge(t.priority)] for t in sorted(weekly, key=lambda x: x.priority)]
    md.append(_table(["Title", "Site", "Status", "Priority"], rows))
    md.append("")

    # Background
    if low:
        md.append("## Background & Lower Priority Work\n")
        rows = [[t.title, t.supervisor, t.site, t.status, _priority_badge(t.priority)] for t in sorted(low, key=lambda x: x.priority)]
        md.append(_table(["Title", "Supervisor", "Site", "Status", "Priority"], rows))
        md.append("")

    # Recently Completed
    md.append(PAGE_BREAK)
    md.append(f"## Recently Completed Projects (Past {recent_days} Days)\n")
    recent_week = [t for t in completed if t.date_completed and t.date_completed >= prev_monday]
    recent_week += [Task(id=f"moved:{title}", title=title, date_completed=today) for title in moved_titles]
    if recent_week:
        rows = [[t.title, t.site, t.date_completed.strftime("%Y-%m-%d") if t.date_completed else "—", _priority_badge(t.priority)] for t in recent_week]
        md.append(_table(["Title", "Site", "Date Completed", "Priority"], rows))
    else:
        md.append(f"*No projects were completed in the past {recent_days} days. Current project timelines extend beyond a single reporting period.*\n")

    # Extended completed window
    md.append(f"## Deliverables Completed — Last {extended_days} Days\n")
    recent_ext = [t for t in completed if t.date_completed and t.date_completed >= extended_cutoff]
    if recent_ext:
        md.append(f"Over the past {extended_days} days, **{len(recent_ext)}** project(s) have been delivered. This reflects a steady cadence of closing out actionable work alongside ongoing priorities.\n")
        rows = [[t.title, t.site, t.date_completed.strftime("%Y-%m-%d") if t.date_completed else "—", _priority_badge(t.priority)] for t in sorted(recent_ext, key=lambda x: x.date_completed or today, reverse=True)]
        md.append(_table(["Title", "Site", "Date Completed", "Priority"], rows))
    else:
        md.append(f"*No projects have been formally completed in the last {extended_days} days. Active work items are longer-duration efforts with deliverables expected in upcoming reporting periods.*\n")

    # Supervisor Distribution
    md.append("## Work Assigned by Supervisor\n")
    sup_counts = Counter(t.supervisor for t in all_active if t.supervisor)
    rows = [[sup, str(cnt), _pct(cnt, total_active)] for sup, cnt in sup_counts.most_common()]
    md.append(_table(["Supervisor", "Active Assignments", "% of Workload"], rows))
    md.append("")

    # Change History (snapshot diff)
    if snapshot_diff is not None and snapshot_diff.has_changes:
        md.append(PAGE_BREAK)
        md.append("## Change History\n")
        md.append("*Changes detected since the previous snapshot.*\n")
        if snapshot_diff.added:
            md.append("### Added\n")
            rows = [[c.entity_type.title(), c.entity_id, c.title] for c in snapshot_diff.added]
            md.append(_table(["Type", "ID", "Title"], rows))
            md.append("")
        if snapshot_diff.removed:
            md.append("### Removed\n")
            rows = [[c.entity_type.title(), c.entity_id, c.title] for c in snapshot_diff.removed]
            md.append(_table(["Type", "ID", "Title"], rows))
            md.append("")
        if snapshot_diff.modified:
            md.append("### Modified\n")
            rows = []
            for c in snapshot_diff.modified:
                detail = "; ".join(f"{fc.field}: {fc.old!r} → {fc.new!r}" for fc in c.fields)
                rows.append([c.entity_type.title(), c.entity_id, c.title, detail])
            md.append(_table(["Type", "ID", "Title", "Changes"], rows))
            md.append("")

    # Looking Ahead
    md.append("---\n")
    md.append("## Looking Ahead\n")
    top_next = sorted(active_ongoing + weekly, key=lambda t: t.priority)[:3]
    look_ahead = (
        "Heading into next week, primary focus will remain on "
        + ", ".join(f'**{t.title}**' for t in top_next)
        + ". Lower-priority items will be advanced as capacity allows."
    )
    md.append(f"> {look_ahead}\n")

    return "\n".join(md)


def save_markdown(md_text: str, dest: Path) -> Path:
    """Write the Markdown text (with CSS preamble) to *dest*.

    Returns the path written.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"<style>\n{CSS}</style>\n\n{md_text}", encoding="utf-8")
    return dest
