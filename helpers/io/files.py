"""File-system helpers: safe names, copy, move, and platform open."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


def safe_filename(name: str) -> str:
    """Convert *name* into a filesystem-safe string."""
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()


def copy_files(sources: list[str | Path], dest_dir: Path) -> list[str]:
    """Copy *sources* into *dest_dir*, creating it if needed.

    Returns the list of destination filenames.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for src in sources:
        src_path = Path(src)
        dest_path = dest_dir / src_path.name
        shutil.copy2(str(src_path), str(dest_path))
        copied.append(src_path.name)
    return copied


def open_path(target: str | Path) -> None:
    """Open *target* using the platform's default handler.

    Works on Windows (``os.startfile``), macOS (``open``),
    and Linux (``xdg-open``).
    """
    target = str(target)
    system = platform.system()
    if system == "Windows":
        os.startfile(target)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])


def find_latest(folder: Path, pattern: str) -> Path | None:
    """Return the newest file matching *pattern* in *folder*, or ``None``."""
    if not folder.exists():
        return None
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None
