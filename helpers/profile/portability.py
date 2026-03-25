"""Profile import / export — package a profile as a .pmprofile bundle.

A ``.pmprofile`` file is a standard ZIP archive containing the profile's
company folder (data, attachments, exports, reports, and optionally the
workbook).  The archive also stores a ``_profile.yaml`` manifest with the
profile's YAML dict so it can be re-created on import.

Export
------
``export_profile(index, dest_path)`` → writes ``<dest_path>.pmprofile``

Import
------
``import_profile(path)`` → extracts into ``profiles/<company>/``, adds a
YAML entry, returns the new profile index.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import yaml

from helpers.io.paths import PROFILES_DIR, _safe_dir_name, PROFILE_SUBDIRS
from helpers.profile.profile import (
    get_profiles,
    init_profile,
    scaffold_profile,
)


_MANIFEST_NAME = "_profile.yaml"


def export_profile(index: int, dest: Path) -> Path:
    """Package profile *index* as a ``.pmprofile`` ZIP archive.

    *dest* is the output file path.  If it doesn't end with ``.pmprofile``
    the extension is appended automatically.

    Returns the final path of the written archive.
    """
    profiles = get_profiles()
    if index < 0 or index >= len(profiles):
        raise IndexError(f"Profile index {index} out of range (0–{len(profiles) - 1})")

    prof = dict(profiles[index])
    company = prof.get("company", "")
    if not company:
        raise ValueError("Cannot export a profile without a company name.")

    safe_name = _safe_dir_name(company)
    source_dir = PROFILES_DIR / safe_name

    if not source_dir.exists():
        raise FileNotFoundError(f"Profile directory not found: {source_dir}")

    dest = Path(dest)
    if dest.suffix != ".pmprofile":
        dest = dest.with_suffix(".pmprofile")

    dest.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest
        manifest_content = yaml.dump(prof, default_flow_style=False, allow_unicode=True)
        zf.writestr(_MANIFEST_NAME, manifest_content)

        # Walk the profile directory and add all files
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = f"{safe_name}/{file_path.relative_to(source_dir)}"
                zf.write(file_path, arcname)

    return dest


def import_profile(archive_path: Path) -> int:
    """Import a ``.pmprofile`` bundle into the application.

    1. Reads the ``_profile.yaml`` manifest from the archive
    2. Extracts files into ``profiles/<company>/``
    3. Adds the profile to the YAML config via ``init_profile()``

    Returns the new profile's index.

    Raises ``ValueError`` if a profile with the same company already exists.
    """
    archive_path = Path(archive_path)
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        # Validate: must contain _profile.yaml
        if _MANIFEST_NAME not in zf.namelist():
            raise ValueError(
                f"Invalid .pmprofile archive: missing {_MANIFEST_NAME}"
            )

        # Read manifest
        manifest_bytes = zf.read(_MANIFEST_NAME)
        prof_data = yaml.safe_load(manifest_bytes.decode("utf-8"))

        company = prof_data.get("company", "")
        if not company:
            raise ValueError("Archive manifest has no 'company' field.")

        # Check for duplicate company
        existing = get_profiles()
        for p in existing:
            if _safe_dir_name(p.get("company", "")) == _safe_dir_name(company):
                raise ValueError(
                    f"A profile for company '{company}' already exists. "
                    "Delete or rename it before importing."
                )

        safe_name = _safe_dir_name(company)
        target_dir = PROFILES_DIR / safe_name

        # Extract profile files (skip the manifest itself)
        for member in zf.namelist():
            if member == _MANIFEST_NAME:
                continue
            # Security: prevent path traversal
            resolved = (PROFILES_DIR / member).resolve()
            if not str(resolved).startswith(str(PROFILES_DIR.resolve())):
                raise ValueError(f"Path traversal detected in archive: {member}")

        # Extract all profile files
        for member in zf.namelist():
            if member == _MANIFEST_NAME:
                continue
            # Extract to profiles/ dir (archive paths start with <company>/)
            zf.extract(member, PROFILES_DIR)

    # Ensure all subdirectories exist
    for sub in PROFILE_SUBDIRS:
        (target_dir / sub).mkdir(parents=True, exist_ok=True)

    # Add profile to YAML
    idx = init_profile(prof_data)
    return idx
