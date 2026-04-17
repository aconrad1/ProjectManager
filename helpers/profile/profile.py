"""Profile management — load, switch, persist, and initialise profiles.

This is a thin wrapper around the YAML profile file.  The GUI and CLI
both go through these functions so behaviour stays consistent.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from helpers.io.paths import (
    PROFILE_PATH, PROFILES_DIR, TEMPLATE_WORKBOOK, PROFILE_SUBDIRS,
    profile_dir, _safe_dir_name,
)


@dataclass(frozen=True)
class ProfileConfig:
    """Immutable snapshot of the active profile configuration."""
    name: str = ""
    role: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    recipient_name: str = ""
    recipient_email: str = ""
    workbook_filename: str = ""
    daily_hours_budget: float = 8.0
    weekly_hours_budget: float = 40.0


class ProfileNotFoundError(Exception):
    """Raised when user_profile.yaml is missing or invalid."""


_profiles: list[dict] = []
_active_index: int = 0
_active_config: ProfileConfig = ProfileConfig()
_initialized: bool = False


# ── Internal loaders ──────────────────────────────────────────────────────────

def _load_profiles() -> tuple[list[dict], int]:
    """Read all profiles and the active index from the YAML file."""
    if not PROFILE_PATH.exists():
        # Check legacy location (root-level user_profile.yaml)
        from helpers.io.paths import BASE_DIR
        legacy = BASE_DIR / "user_profile.yaml"
        if legacy.exists():
            PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy), str(PROFILE_PATH))
        else:
            raise ProfileNotFoundError(
                f"user_profile.yaml not found at {PROFILE_PATH}. "
                "Copy the template and fill in your details before running."
            )

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict) and "profiles" in data:
        profiles = data["profiles"]
        active = int(data.get("active_profile", 0))
    elif isinstance(data, dict) and data.get("name"):
        profiles = [data]
        active = 0
    else:
        raise ProfileNotFoundError(
            "user_profile.yaml is missing required fields."
        )

    active = max(0, min(active, len(profiles) - 1))
    if not profiles:
        raise ProfileNotFoundError(
            "No profiles defined in user_profile.yaml."
        )

    if not profiles[active].get("name"):
        print(
            "WARNING: Active profile has no 'name' set. "
            "Please configure your profile in the GUI or edit profiles/user_profile.yaml.",
            file=sys.stderr,
        )

    return profiles, active


# ── Module-level profile data (set by _apply_profile) ─────────────────────────
# DEPRECATED: Use get_active_config() instead.
# These are kept for backward compatibility and synced from _active_config.

USER_NAME: str = ""
USER_ROLE: str = ""
USER_COMPANY: str = ""
USER_EMAIL: str = ""
USER_PHONE: str = ""
RECIPIENT_NAME: str = ""
RECIPIENT_EMAIL: str = ""
WORKBOOK_FILENAME: str = ""
DAILY_HOURS_BUDGET: float = 8.0
WEEKLY_HOURS_BUDGET: float = 40.0


def _sync_legacy_globals() -> None:
    """Keep legacy globals in sync for backward compatibility.
    
    DEPRECATED: Consumers should use get_active_config() instead.
    """
    global USER_NAME, USER_ROLE, USER_COMPANY, USER_EMAIL, USER_PHONE
    global RECIPIENT_NAME, RECIPIENT_EMAIL, WORKBOOK_FILENAME
    global DAILY_HOURS_BUDGET, WEEKLY_HOURS_BUDGET
    
    cfg = _active_config
    USER_NAME = cfg.name
    USER_ROLE = cfg.role
    USER_COMPANY = cfg.company
    USER_EMAIL = cfg.email
    USER_PHONE = cfg.phone
    RECIPIENT_NAME = cfg.recipient_name
    RECIPIENT_EMAIL = cfg.recipient_email
    WORKBOOK_FILENAME = cfg.workbook_filename
    DAILY_HOURS_BUDGET = cfg.daily_hours_budget
    WEEKLY_HOURS_BUDGET = cfg.weekly_hours_budget


def _apply_profile(index: int) -> None:
    global _active_index, _active_config
    
    _active_index = index
    p = _profiles[index]
    _active_config = ProfileConfig(
        name=p.get("name", ""),
        role=p.get("role", ""),
        company=p.get("company", ""),
        email=p.get("email", ""),
        phone=str(p.get("phone", "")),
        recipient_name=p.get("recipient_name", ""),
        recipient_email=p.get("recipient_email", ""),
        workbook_filename=p.get("workbook_filename", ""),
        daily_hours_budget=float(p.get("daily_hours_budget", 8.0)),
        weekly_hours_budget=float(p.get("weekly_hours_budget", 40.0)),
    )
    # Backward compatibility: update legacy globals
    _sync_legacy_globals()


# ── Public API ─────────────────────────────────────────────────────────────────

def ensure_initialized() -> None:
    """Load profiles from YAML if not already done.

    Call this once from the app entry point (cli.py or gui.py).
    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _profiles, _active_index, _initialized
    if _initialized:
        return
    _profiles, _active_index = _load_profiles()
    _apply_profile(_active_index)
    _initialized = True


def get_active_config() -> ProfileConfig:
    """Return the current profile configuration snapshot.

    Returns a default (empty) ProfileConfig if called before initialization.
    Prefer this over importing module-level constants (USER_NAME, USER_COMPANY, etc.).
    """
    return _active_config


def get_profiles() -> list[dict]:
    ensure_initialized()
    return list(_profiles)


def get_active_index() -> int:
    ensure_initialized()
    return _active_index


def get_active_profile() -> dict:
    ensure_initialized()
    return dict(_profiles[_active_index])


def _save_profiles() -> None:
    data: dict[str, Any] = {"active_profile": _active_index, "profiles": _profiles}
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        f.write("# " + "─" * 78 + "\n")
        f.write("# User Profiles — Weekly Report Generator\n")
        f.write("# " + "─" * 78 + "\n\n")
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def switch_profile(index: int) -> None:
    ensure_initialized()
    if index < 0 or index >= len(_profiles):
        raise IndexError(f"Profile index {index} out of range (0–{len(_profiles) - 1})")
    _apply_profile(index)
    _save_profiles()


def save_profile(index: int, data: dict) -> None:
    """Update a profile by index with *data* dict and persist."""
    if index < 0 or index >= len(_profiles):
        raise IndexError(f"Profile index {index} out of range")
    _profiles[index].update(data)
    _apply_profile(_active_index)
    _save_profiles()


def file_prefix(name: str | None = None) -> str:
    """Return a filesystem-safe version of the user's name for file naming."""
    if name is None:
        cfg = get_active_config()
        name = cfg.name
    return name.replace(" ", "_")


# ── Profile initialisation ────────────────────────────────────────────────────

def scaffold_profile(company: str, workbook_filename: str = "") -> Path:
    """Create the folder tree for *company* and generate a blank workbook if needed.

    If the workbook doesn't exist, generates one from the schema template
    (no dependency on ``_template.xlsx``).  Also creates an empty
    ``domain.json`` so the app can start cleanly.

    Returns the profile directory path.
    """
    from helpers.schema.template import create_template
    from helpers.persistence.serializer import save_profile_json
    from helpers.domain.profile import Profile

    p_dir = profile_dir(company)
    for sub in PROFILE_SUBDIRS:
        (p_dir / sub).mkdir(parents=True, exist_ok=True)

    if workbook_filename:
        dest_wb = p_dir / workbook_filename
        if not dest_wb.exists():
            if TEMPLATE_WORKBOOK.exists():
                shutil.copy2(str(TEMPLATE_WORKBOOK), str(dest_wb))
            else:
                create_template(dest_wb)

    # Ensure domain.json exists so contract.sync() doesn't fail
    domain_json = p_dir / "data" / "domain.json"
    if not domain_json.exists():
        stub = Profile(
            id=f"profile:{company or 'default'}",
            title=company or "Default",
            company=company,
            status="Active",
        )
        save_profile_json(stub, domain_json)

    return p_dir


def init_profile(data: dict) -> int:
    """Add a new profile, scaffold its directory, and persist.

    *data* must contain at least ``name`` and ``company``.
    Returns the new profile's index.
    """
    required = ("name", "company")
    for key in required:
        if not data.get(key):
            raise ValueError(f"Profile data must include '{key}'")

    defaults = {
        "role": "", "email": "", "phone": "",
        "recipient_name": "", "recipient_email": "",
        "workbook_filename": "",
        "daily_hours_budget": 8.0,
    }
    profile = {**defaults, **data}
    _profiles.append(profile)
    idx = len(_profiles) - 1

    scaffold_profile(profile["company"], profile.get("workbook_filename", ""))
    _save_profiles()
    return idx


def delete_profile(index: int, *, remove_files: bool = False) -> None:
    """Remove a profile by index.

    If this is the last remaining profile, a "Default" fallback profile is
    auto-generated so the application always has at least one entry.

    If *remove_files* is ``True`` the profile's company folder under
    ``profiles/`` is also deleted from disk.
    """
    global _active_index
    if index < 0 or index >= len(_profiles):
        raise IndexError(f"Profile index {index} out of range (0–{len(_profiles) - 1})")

    is_last = len(_profiles) == 1
    company = _profiles[index].get("company", "")
    _profiles.pop(index)

    if is_last:
        # Auto-generate a fallback "Default" profile
        fallback = {
            "name": "Default User",
            "company": "Default",
            "role": "",
            "email": "",
            "phone": "",
            "recipient_name": "",
            "recipient_email": "",
            "workbook_filename": "Projects.xlsx",
            "daily_hours_budget": 8.0,
        }
        _profiles.append(fallback)
        _active_index = 0
        _apply_profile(0)
        _save_profiles()
        scaffold_profile("Default", "Projects.xlsx")
    else:
        # Adjust the active index after removal
        if _active_index >= len(_profiles):
            _active_index = len(_profiles) - 1
        elif _active_index > index:
            _active_index -= 1
        # If the deleted profile was the active one, the new index already points
        # to a valid entry — just re-apply.
        _apply_profile(_active_index)
        _save_profiles()

    if remove_files and company:
        import shutil as _shutil
        target = profile_dir(company)
        if target.exists():
            _shutil.rmtree(target, ignore_errors=True)


def reload() -> None:
    """Re-read profiles from YAML and re-apply the active profile's globals.

    Call this after ``save_profile()`` or ``switch_profile()`` so that
    every module referencing the module-level constants (``USER_NAME``,
    ``USER_COMPANY``, etc.) sees the updated values without restarting.
    """
    global _profiles, _active_index, _initialized
    _profiles, _active_index = _load_profiles()
    _apply_profile(_active_index)
    _initialized = True


def ensure_profile_dirs() -> None:
    """Ensure the active profile's folder tree exists (idempotent)."""
    cfg = get_active_config()
    scaffold_profile(cfg.company, cfg.workbook_filename)
