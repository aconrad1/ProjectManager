"""Reset the application to a blank state for distribution.

This script removes ALL user profiles, personal data, and generated files,
leaving the application shell ready for a new user to populate.

Usage:
    python setup/reset_for_distribution.py          # interactive confirmation
    python setup/reset_for_distribution.py --force  # skip confirmation (CI / scripted use)

What it does:
  1. Deletes every company folder under ``profiles/`` (attachments, data, exports, reports)
  2. Overwrites ``profiles/user_profile.yaml`` with a blank single-profile template
  3. Removes the template workbook (``profiles/_template.xlsx``) if present
  4. Clears any ``__pycache__`` folders

What it does NOT touch:
  - Source code (helpers/, scripts/)
  - Documentation (README.md, AGENTS.md, docs/)
  - requirements.txt, setup/install.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# ── Resolve project root ──────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # script lives in setup/ subfolder


PROFILES_DIR = PROJECT_ROOT / "profiles"
PROFILE_YAML = PROFILES_DIR / "user_profile.yaml"
TEMPLATE_WB = PROFILES_DIR / "_template.xlsx"

# Folders under profiles/ that belong to user data (company folders)
# We skip user_profile.yaml and the dev test profile during the scan.
_KEEP_FILES = {"user_profile.yaml"}
_KEEP_DIRS = {"_TestCompany"}  # dev/test profile — committed to repo

_BLANK_YAML = """\
# ──────────────────────────────────────────────────────────────────────────────
# User Profiles — Weekly Report Generator
# ──────────────────────────────────────────────────────────────────────────────
#
# Fill in your details below and launch the application.
# To add more profiles, copy the block below and adjust the values.
#

active_profile: 0
profiles:
  - name: ""
    role: ""
    company: ""
    email: ""
    phone: ""
    recipient_name: ""
    recipient_email: ""
    workbook_filename: ""
    daily_hours_budget: 8.0

  # ── Dev / Test profile (safe to commit — uses only fake data) ──
  - name: "Dev Tester"
    role: "Developer"
    company: "_TestCompany"
    email: "dev@example.com"
    phone: "+1-555-0100"
    recipient_name: "Test Reviewer"
    recipient_email: "reviewer@example.com"
    workbook_filename: "TestProjects.xlsx"
    daily_hours_budget: 8.0
    weekly_hours_budget: 40.0
"""


def _collect_targets() -> list[Path]:
    """Return all company folders under profiles/ that should be deleted."""
    targets: list[Path] = []
    if not PROFILES_DIR.exists():
        return targets
    for child in PROFILES_DIR.iterdir():
        if child.name in _KEEP_FILES:
            continue
        if child.is_dir() and child.name in _KEEP_DIRS:
            continue
        if child.name.startswith("_"):
            # Template workbook or similar — include for deletion
            targets.append(child)
            continue
        if child.is_dir():
            targets.append(child)
    return targets


def _clear_pycache(root: Path) -> int:
    """Remove __pycache__ directories recursively.  Returns count removed."""
    count = 0
    for cache_dir in root.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
            count += 1
    return count


def reset(*, force: bool = False) -> None:
    """Run the full reset."""
    targets = _collect_targets()

    print("=" * 60)
    print("  Weekly Report Generator — Distribution Reset")
    print("=" * 60)
    print()

    if not targets and PROFILE_YAML.exists():
        print("  No company folders found.  Only the YAML will be reset.")
    else:
        print("  The following will be PERMANENTLY DELETED:")
        for t in targets:
            size = sum(f.stat().st_size for f in t.rglob("*") if f.is_file()) if t.is_dir() else t.stat().st_size
            size_mb = size / (1024 * 1024)
            label = "dir " if t.is_dir() else "file"
            print(f"    [{label}]  {t.relative_to(PROJECT_ROOT)}  ({size_mb:.2f} MB)")

    print()
    print("  profiles/user_profile.yaml will be overwritten with a blank template.")
    print()

    if not force:
        answer = input("  Type YES to proceed: ").strip()
        if answer != "YES":
            print("\n  Aborted.")
            return

    # ── Delete company folders / files ─────────────────────────────────────
    for t in targets:
        if t.is_dir():
            shutil.rmtree(t, ignore_errors=True)
            print(f"  Deleted: {t.relative_to(PROJECT_ROOT)}/")
        elif t.is_file():
            t.unlink()
            print(f"  Deleted: {t.relative_to(PROJECT_ROOT)}")

    # ── Reset YAML ─────────────────────────────────────────────────────────
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_YAML.write_text(_BLANK_YAML, encoding="utf-8")
    print("  Reset:   profiles/user_profile.yaml")

    # ── Clear __pycache__ ──────────────────────────────────────────────────
    cleared = _clear_pycache(PROJECT_ROOT)
    if cleared:
        print(f"  Cleared: {cleared} __pycache__ folder(s)")

    print()
    print("  Done.  The application is ready for a new user.")
    print("  Next steps:")
    print("    1. Edit profiles/user_profile.yaml with the new user's details")
    print("    2. Run:  python scripts/gui.py")
    print()


if __name__ == "__main__":
    force = "--force" in sys.argv
    reset(force=force)
