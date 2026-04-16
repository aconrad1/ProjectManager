"""Domain ↔ Workbook sync contract.

This module is the single authority for keeping ``domain.json`` (source of
truth) and the Excel workbook (rendered view) in lockstep.

Architecture
------------
**JSON is the single source of truth.**  The Excel workbook is a rendered
view that is kept in sync with JSON.  The workbook is *never* used as the
primary read source once JSON exists.

Data flow
---------
* ``save()``             — atomic write JSON + render to Excel (the only mutation exit-point)
* ``load_profile()``     — read from JSON; bootstrap from workbook if no JSON yet
* ``push_to_workbook()`` — render JSON → Excel
* ``import_from_workbook()`` — explicit one-way import: Excel → JSON (for
  historical migrations, profile management page, etc.)
* ``sync()``             — startup reconciliation: load JSON, detect genuine
  external Excel edits via content hash, push JSON to Excel
* ``detect_external_edits()`` — mid-session check for workbook edits

Hash-based sync
---------------
Every time we write JSON we store the SHA-256 of the .xlsx at that moment
in ``domain.json._meta.workbook_hash``.  On next startup, if the current
workbook hash differs from the stored hash, the file was genuinely edited
outside the app and we import it.  This is immune to mtime false-positives
(e.g. OneDrive cloud-sync touching a file without changing content).

Every mutation (add/edit/delete) performed through the app MUST call
``save()`` which persists to BOTH JSON and the workbook atomically.

Atomic dual-write
-----------------
``save()`` uses temp-file-then-rename to ensure that a crash or error
mid-write cannot leave ``domain.json`` in a corrupt/truncated state.
The JSON is written to ``domain.json.tmp`` first, then atomically renamed
over the canonical file.  If the subsequent workbook render fails, the
JSON is rolled back to the previous version.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from openpyxl.workbook import Workbook

log = logging.getLogger(__name__)

from helpers.domain.profile import Profile
from helpers.persistence.serializer import (
    save_profile_json,
    load_profile_json,
    hash_file,
)
from helpers.persistence.workbook_reader import load_profile_from_workbook
from helpers.persistence.workbook_writer import save_profile_to_workbook
from helpers.io.paths import data_dir


# ── Path helpers ───────────────────────────────────────────────────────────────

def domain_json_path(company: str) -> Path:
    """Return the canonical ``domain.json`` path for a profile."""
    return data_dir(company) / "domain.json"


# ── Internal helpers ───────────────────────────────────────────────────────────

def _make_meta_kwargs(
    profile_name: str,
    company: str,
    role: str,
    email: str,
    phone: str,
    recipient_name: str,
    recipient_email: str,
    workbook_filename: str,
    daily_hours_budget: float,
) -> dict:
    return dict(
        profile_name=profile_name,
        company=company,
        role=role,
        email=email,
        phone=phone,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        workbook_filename=workbook_filename,
        daily_hours_budget=daily_hours_budget,
    )


def _patch_metadata(profile: Profile, **meta) -> None:
    """Overwrite YAML-sourced metadata onto an already-loaded Profile.

    Ensures that changes made in Settings (name, role, email, etc.) are
    reflected on the in-memory profile without needing a full re-import.
    Always applies daily_hours_budget unconditionally so YAML is authoritative.
    """
    if meta.get("profile_name"):
        profile.title = meta["profile_name"]
    if meta.get("company"):
        profile.company = meta["company"]
    if meta.get("role"):
        profile.role = meta["role"]
    if meta.get("email"):
        profile.email = meta["email"]
    if meta.get("phone"):
        profile.phone = meta["phone"]
    if meta.get("recipient_name"):
        profile.recipient_name = meta["recipient_name"]
    if meta.get("recipient_email"):
        profile.recipient_email = meta["recipient_email"]
    if meta.get("workbook_filename"):
        profile.workbook_filename = meta["workbook_filename"]
    profile.daily_hours_budget = meta.get("daily_hours_budget", 8.0)


# ── Load ───────────────────────────────────────────────────────────────────────

def load_profile(
    company: str,
    wb: Workbook | None = None,
    *,
    profile_name: str = "",
    role: str = "",
    email: str = "",
    phone: str = "",
    recipient_name: str = "",
    recipient_email: str = "",
    workbook_filename: str = "",
    daily_hours_budget: float = 8.0,
) -> Profile:
    """Load the canonical Profile for *company*.

    Priority:
      1. ``domain.json`` exists → JSON is source of truth, load from it.
      2. No JSON but workbook provided → bootstrap JSON from workbook.
      3. Neither → return an empty stub Profile.

    YAML metadata (name, role, email …) is always patched on top so Settings
    changes take effect without re-importing.
    """
    json_path = domain_json_path(company)
    meta = _make_meta_kwargs(
        profile_name, company, role, email, phone,
        recipient_name, recipient_email, workbook_filename, daily_hours_budget,
    )
    profile: Profile | None = None

    if json_path.exists():
        profile, _ = load_profile_json(json_path)
    elif wb is not None:
        # Bootstrap: no JSON yet — build from workbook and save
        profile = load_profile_from_workbook(wb, **meta)
        save_profile_json(profile, json_path)

    if profile is None:
        profile = Profile(
            id=f"profile:{company or 'default'}",
            title=profile_name or company or "Default",
            company=company,
            status="Active",
        )

    _patch_metadata(profile, **meta)

    # Auto-migrate legacy title-keyed notes/links/attachments to ID-based keys
    # (skip if domain.json already records a current migration_version)
    from helpers.persistence.serializer import read_migration_version, MIGRATION_VERSION
    current_ver = read_migration_version(json_path) if json_path.exists() else 0
    if current_ver < MIGRATION_VERSION:
        from helpers.migration import migrate_to_id_keying
        migrate_to_id_keying(profile)
        log.info("Migration complete (version %d → %d)", current_ver, MIGRATION_VERSION)
        # Re-save to stamp the new migration_version in _meta
        save_profile_json(profile, json_path)

    return profile


# ── Save (atomic dual-write — the only mutation exit-point) ───────────────────

def save(profile: Profile, wb: Workbook, *, wb_path: Path | None = None) -> None:
    """Persist *profile* to BOTH ``domain.json`` and the workbook in-memory.

    Uses temp-file-then-rename for crash safety:
    1. Write JSON to ``domain.json.tmp``
    2. Atomically rename ``.tmp`` → ``domain.json``
    3. Render profile into the workbook (in-memory)

    If step 3 fails, the JSON is rolled back to the pre-save backup so the
    two stores remain consistent.

    Pass *wb_path* to record the workbook content hash so that future
    ``sync()`` calls can distinguish genuine external edits from cloud-sync
    mtime bumps.
    """
    json_path = domain_json_path(profile.company)
    tmp_path = json_path.with_suffix(".json.tmp")
    backup_path = json_path.with_suffix(".json.bak")
    wb_hash = hash_file(wb_path) if wb_path and wb_path.exists() else ""

    # 1. Write JSON to temp file
    save_profile_json(profile, tmp_path, workbook_hash=wb_hash)

    # 2. Back up existing JSON (if any) then atomically swap
    had_backup = False
    if json_path.exists():
        shutil.copy2(str(json_path), str(backup_path))
        had_backup = True

    try:
        # Atomic rename (on Windows this replaces the target)
        _atomic_replace(tmp_path, json_path)
    except OSError:
        # Rename failed — clean up temp, leave original intact
        tmp_path.unlink(missing_ok=True)
        if had_backup:
            backup_path.unlink(missing_ok=True)
        raise

    # 3. Render to workbook — if this fails, roll back JSON
    try:
        save_profile_to_workbook(profile, wb)
    except Exception:
        # Roll back JSON to the pre-save state
        if had_backup:
            _atomic_replace(backup_path, json_path)
        else:
            json_path.unlink(missing_ok=True)
        raise

    # Success — clean up backup
    if had_backup:
        backup_path.unlink(missing_ok=True)


def _atomic_replace(src: Path, dst: Path) -> None:
    """Replace *dst* with *src* as atomically as the OS allows."""
    try:
        os.replace(str(src), str(dst))
    except OSError:
        # Fallback for cross-device or permission issues
        shutil.move(str(src), str(dst))


# ── Directional syncs ─────────────────────────────────────────────────────────

def push_to_workbook(profile: Profile, wb: Workbook) -> None:
    """Render the profile (from JSON) into the workbook data sheets."""
    save_profile_to_workbook(profile, wb)


def import_from_workbook(
    wb: Workbook,
    company: str,
    wb_path: Path,
    *,
    profile_name: str = "",
    role: str = "",
    email: str = "",
    phone: str = "",
    recipient_name: str = "",
    recipient_email: str = "",
    workbook_filename: str = "",
    daily_hours_budget: float = 8.0,
) -> Profile:
    """Force a one-way import: Excel → JSON (overwrites existing JSON).

    Use for:
    - Historical workbook migrations (Profile Management page)
    - Manual Excel edits that the user explicitly wants to promote
    """
    meta = _make_meta_kwargs(
        profile_name, company, role, email, phone,
        recipient_name, recipient_email, workbook_filename, daily_hours_budget,
    )
    profile = load_profile_from_workbook(wb, **meta)
    json_path = domain_json_path(company)
    wb_hash = hash_file(wb_path) if wb_path.exists() else ""
    save_profile_json(profile, json_path, workbook_hash=wb_hash)
    return profile


def resync_json(
    wb: Workbook,
    company: str,
    wb_path: Path,
    *,
    profile_name: str = "",
    role: str = "",
    email: str = "",
    phone: str = "",
    recipient_name: str = "",
    recipient_email: str = "",
    workbook_filename: str = "",
    daily_hours_budget: float = 8.0,
) -> Profile:
    """Rebuild JSON from the current workbook state.

    Called by the CLI after any workbook mutation to keep JSON in sync.
    This is the CLI's equivalent of the GUI's ``DomainService._persist()``.
    """
    return import_from_workbook(
        wb, company, wb_path,
        profile_name=profile_name,
        role=role,
        email=email,
        phone=phone,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        workbook_filename=workbook_filename,
        daily_hours_budget=daily_hours_budget,
    )


# ── Full sync (startup reconciliation) ────────────────────────────────────────

def sync(
    wb: Workbook,
    company: str,
    wb_path: Path,
    *,
    profile_name: str = "",
    role: str = "",
    email: str = "",
    phone: str = "",
    recipient_name: str = "",
    recipient_email: str = "",
    workbook_filename: str = "",
    daily_hours_budget: float = 8.0,
) -> Profile:
    """Startup reconciliation: load JSON, detect genuine Excel edits, push to Excel.

    JSON is always the source of truth.  The workbook is only imported when
    its content hash differs from the hash stored in ``domain.json._meta``,
    which means the file was genuinely edited outside the app (not just
    touched by OneDrive or a filesystem sync).

    Returns the reconciled Profile with the workbook rendered from JSON.
    """
    json_path = domain_json_path(company)
    meta = _make_meta_kwargs(
        profile_name, company, role, email, phone,
        recipient_name, recipient_email, workbook_filename, daily_hours_budget,
    )
    # import_from_workbook / load_profile receive company as a positional arg,
    # so strip it from the keyword dict to avoid "got multiple values" errors.
    meta_no_company = {k: v for k, v in meta.items() if k != "company"}

    json_exists = json_path.exists()
    wb_exists = wb_path.exists()

    if json_exists:
        profile, stored_meta = load_profile_json(json_path)
        _patch_metadata(profile, **meta)

        # Run migration if needed (skip if already at current version)
        from helpers.persistence.serializer import read_migration_version, MIGRATION_VERSION
        current_ver = int(stored_meta.get("migration_version", 0))
        if current_ver < MIGRATION_VERSION:
            from helpers.migration import migrate_to_id_keying
            migrate_to_id_keying(profile)
            log.info("Migration complete (version %d → %d)", current_ver, MIGRATION_VERSION)
            save_profile_json(profile, json_path)

        # Check if the workbook was edited externally by comparing content hash
        if wb_exists:
            stored_hash = stored_meta.get("workbook_hash", "")
            current_hash = hash_file(wb_path)
            if stored_hash and current_hash != stored_hash:
                # Workbook content genuinely changed — import it
                profile = import_from_workbook(wb, company, wb_path, **meta_no_company)
            else:
                # JSON is canonical — render it into the workbook
                push_to_workbook(profile, wb)
        # If no workbook, just return the JSON profile as-is
    elif wb_exists:
        # Bootstrap: first time running, no JSON yet
        profile = import_from_workbook(wb, company, wb_path, **meta_no_company)
    else:
        # Neither exists — return empty stub
        profile = load_profile(company, None, **meta_no_company)

    return profile


# ── Mid-session external edit detection ────────────────────────────────────────

def detect_external_edits(company: str, wb_path: Path) -> bool:
    """Return ``True`` if the workbook on disk has been modified externally.

    Compares the current SHA-256 of *wb_path* against the hash stored in
    ``domain.json._meta.workbook_hash``.  Returns ``False`` if either file
    is missing or no stored hash exists (e.g. first run).

    This is safe to call frequently (on focus, tab change, etc.) because
    it only reads the ``_meta`` envelope from JSON and hashes the workbook.
    """
    json_path = domain_json_path(company)
    if not json_path.exists() or not wb_path.exists():
        return False

    _, stored_meta = load_profile_json(json_path)
    stored_hash = stored_meta.get("workbook_hash", "")
    if not stored_hash:
        return False

    current_hash = hash_file(wb_path)
    return current_hash != stored_hash

