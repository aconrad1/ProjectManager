"""Utility commands — save workbook, open latest report, email report."""

from __future__ import annotations

import shutil
import webbrowser
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from helpers.commands.registry import register
from helpers.io.files import find_latest, open_path
from helpers.profile.profile import get_active_config, file_prefix
from helpers.profile.config import workbook_path, reports_dir, pdf_dir, markdown_dir
from helpers.util.dates import report_filename


@register("save_workbook")
def save_workbook_cmd(
    wb,
    *,
    log: Callable[[str], None] | None = None,
) -> Path | None:
    """Save the workbook and create a dated snapshot. Returns snapshot path."""
    if log is None:
        log = print
    wb_path = workbook_path()
    wb.save(str(wb_path))
    r_dir = reports_dir()
    r_dir.mkdir(parents=True, exist_ok=True)
    dated = r_dir / report_filename(f"{file_prefix()}_Weekly_Deliverables_Report", "xlsx")
    shutil.copy2(str(wb_path), str(dated))
    log(f"Saved workbook: {wb_path.name}")
    log(f"Snapshot: {dated.name}")
    return dated


@register("open_latest")
def open_latest_report() -> Path | None:
    """Open the most recent PDF (or Markdown) report."""
    p = find_latest(pdf_dir(), "*.pdf") or find_latest(markdown_dir(), "*.md")
    if p:
        open_path(p)
    return p


@register("email_report")
def email_report(
    *,
    log: Callable[[str], None] | None = None,
) -> None:
    """Open an Outlook draft (or mailto: fallback) with the latest PDF attached."""
    if log is None:
        log = print

    cfg = get_active_config()
    pdf = find_latest(pdf_dir(), "*.pdf")
    if not pdf:
        raise FileNotFoundError("No PDF report found. Generate one first.")

    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon"
    recipient_line = f"{greeting}, {cfg.recipient_name},\n\n" if cfg.recipient_name else f"{greeting},\n\n"
    subject = f"Weekly Deliverables Report — {date.today().strftime('%B %d, %Y')}"
    body = (
        f"{recipient_line}"
        "Please find attached my weekly deliverables report.\n\n"
        f"Best regards,\n{cfg.name}"
    )

    try:
        import win32com.client  # type: ignore[import-not-found]
        outlook = win32com.client.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.Body = body
        if cfg.recipient_email:
            mail.To = cfg.recipient_email
        mail.Attachments.Add(str(pdf))
        mail.Display()
        log("Outlook email draft opened.")
    except ImportError:
        from urllib.parse import quote
        mailto = f"mailto:{quote(cfg.recipient_email)}?subject={quote(subject)}&body={quote(body)}"
        webbrowser.open(mailto)
        log("Opened mailto link. Attach the PDF manually:")
        log(f"  {pdf}")
