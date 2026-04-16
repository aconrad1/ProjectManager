"""Report pipeline command — the full generate-reports flow.

Both the GUI 'Generate Reports' button and the CLI ``generate`` subcommand
delegate to :func:`generate_reports`.

Builds a domain Profile from the workbook, captures a pre-mutation
snapshot for change history, syncs Timelines and Gantt sheets (with
integrity checking), then generates Markdown and PDF reports.
"""

from __future__ import annotations

import shutil
from datetime import date
from typing import Callable

from helpers.commands.registry import register
from helpers.data.completions import process_completions
from helpers.data.workbook import load_workbook
from helpers.data.overview import write_overview
from helpers.config.loader import load_deadline_windows
from helpers.reporting.markdown import build_markdown, save_markdown
from helpers.reporting.pdf import generate_pdf
from helpers.reporting.snapshot_diff import (
    diff_profiles, load_previous_snapshot, SnapshotDiff, baseline_profile_for_diff,
)
from helpers.profile.profile import get_active_config, file_prefix
from helpers.profile.config import (
    workbook_path, reports_dir, markdown_dir, pdf_dir,
)
from helpers.util.dates import report_filename

from helpers.persistence.contract import sync as sync_profile, save as save_profile_dual
from helpers.schema.timelines import sync_timelines
from helpers.schema.gantt import build_gantt_sheet
from helpers.schema.integrity import check_and_repair
from helpers.scheduling.engine import compute_schedule


@register("generate_reports")
def generate_reports(
    *,
    log: Callable[[str], None] | None = None,
    today: date | None = None,
) -> dict:
    """Run the full report-generation pipeline.

    Returns a dict with keys:
        moved, wb, md_path, pdf_path, profile, snapshot_diff
    """
    if today is None:
        today = date.today()
    if log is None:
        log = print

    wb_path = workbook_path()
    prefix = file_prefix()

    # Capture pre-mutation snapshot for change history
    log("[1/9] Capturing previous snapshot for change history…")
    cfg = get_active_config()
    previous_profile = load_previous_snapshot(cfg.company, reports_dir())
    if previous_profile:
        log("   Previous snapshot loaded.")
    else:
        log("   No previous snapshot found — a first-run baseline diff will be generated.")

    windows = load_deadline_windows(log=log)

    log("[2/9] Processing completed tasks…")
    wb = load_workbook(wb_path)
    moved = process_completions(wb, today)
    if moved:
        for t in moved:
            log(f"   Moved to Completed: {t}")
    else:
        log("   No newly completed tasks.")

    log("[3/9] Syncing domain hierarchy…")
    profile = sync_profile(
        wb,
        cfg.company,
        wb_path,
        profile_name=cfg.name,
        role=cfg.role,
        email=cfg.email,
        phone=cfg.phone,
        recipient_name=cfg.recipient_name,
        recipient_email=cfg.recipient_email,
        workbook_filename=cfg.workbook_filename,
        daily_hours_budget=cfg.daily_hours_budget,
    )
    log(f"   Profile: {profile.title}  |  Projects: {len(profile.projects)}  |  Tasks: {len(profile.all_tasks)}")

    # Compute snapshot diff
    snapshot_diff: SnapshotDiff | None = None
    if previous_profile is not None:
        snapshot_diff = diff_profiles(previous_profile, profile)
        if snapshot_diff.has_changes:
            log(f"   Change history: {len(snapshot_diff.added)} added, "
                f"{len(snapshot_diff.removed)} removed, "
                f"{len(snapshot_diff.modified)} modified")
        else:
            log("   No changes detected since previous snapshot.")
    else:
        snapshot_diff = diff_profiles(baseline_profile_for_diff(profile), profile)
        if snapshot_diff.has_changes:
            log(f"   Initial change history: {len(snapshot_diff.added)} added (baseline report).")
        else:
            log("   Initial change history: no entities to report.")

    log("[4/9] Running daily scheduler…")
    schedule = compute_schedule(profile, today)
    scheduled_count = sum(
        len(entries) for pri_map in schedule.values() for entries in pri_map.values()
    )
    log(f"   Scheduled {scheduled_count} task-slots across {len(schedule)} days")

    log("[5/9] Writing Overview tab…")
    write_overview(wb, profile, moved, today,
                   author=cfg.name, role=cfg.role, company=cfg.company,
                   snapshot_diff=snapshot_diff, deadline_windows=windows)

    log("[6/9] Checking Timelines integrity & syncing derived sheets…")
    integrity = check_and_repair(wb, log=log)
    if integrity.is_healthy or integrity.repaired:
        tl_rows = sync_timelines(wb)
    else:
        log("   ⚠ Timelines has unresolved errors — rebuilding from scratch…")
        tl_rows = sync_timelines(wb)
    gantt_rows = build_gantt_sheet(wb)
    log(f"   Timelines: {tl_rows} rows  |  Gantt: {gantt_rows} rows")

    log("[7/9] Saving workbook & domain.json…")
    save_profile_dual(profile, wb)
    wb.save(str(wb_path))
    r_dir = reports_dir()
    r_dir.mkdir(parents=True, exist_ok=True)
    dated = r_dir / report_filename(f"{prefix}_Weekly_Deliverables_Report", "xlsx")
    shutil.copy2(str(wb_path), str(dated))
    log(f"   Saved: {dated.name}")

    log("[8/9] Generating Markdown & PDF reports…")
    md_text = build_markdown(
        profile, moved, today,
        author=cfg.name, role=cfg.role, company=cfg.company,
        snapshot_diff=snapshot_diff, deadline_windows=windows,
    )
    m_dir = markdown_dir()
    md_path = m_dir / report_filename(f"{prefix}_Weekly_Deliverables_Report", "md")
    save_markdown(md_text, md_path)
    log(f"   Saved: {md_path.name}")

    p_dir = pdf_dir()
    pdf_path = p_dir / report_filename(f"{prefix}_Weekly_Deliverables_Report", "pdf")
    generate_pdf(md_text, pdf_path)
    log(f"   Saved: {pdf_path.name}")

    log(f"\n[9/9] Done! Reports generated for {today.strftime('%B %d, %Y')}.")

    return {
        "moved": moved,
        "wb": wb,
        "md_path": md_path,
        "pdf_path": pdf_path,
        "profile": profile,
        "snapshot_diff": snapshot_diff,
    }
