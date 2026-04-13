"""PDF generation — convert Markdown to PDF via Chrome / Edge headless."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import markdown as md_lib

from helpers.reporting.markdown import CSS


def _find_chrome() -> str:
    """Locate a Chrome or Edge executable for headless PDF printing."""
    import shutil

    candidates = [
        # Windows
        os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/microsoft-edge",
        "/usr/bin/microsoft-edge-stable",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # Also check PATH for common browser command names
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError(
        "No Chrome or Edge browser found. Install chromium or use the Markdown report instead."
    )


def generate_pdf(md_text: str, dest: Path) -> Path:
    """Convert raw Markdown *md_text* to a PDF at *dest*.

    Returns the output path.
    """
    html_body = md_lib.markdown(md_text, extensions=["tables"])
    html_doc = (
        '<!DOCTYPE html>\n<html lang="en">\n'
        f'<head><meta charset="utf-8"><style>{CSS}</style></head>\n'
        f'<body>{html_body}</body>\n</html>'
    )

    dest.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_doc)
        tmp_html = f.name

    try:
        chrome = _find_chrome()
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={dest}",
                "--print-to-pdf-no-header",
                tmp_html,
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
    finally:
        Path(tmp_html).unlink(missing_ok=True)

    return dest
