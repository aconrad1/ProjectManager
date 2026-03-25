"""JSON serialisation / deserialisation for the domain hierarchy.

Used for:
  - future CLI / automation JSON export/import
  - snapshot persistence alongside the Excel workbook

File format
-----------
domain.json wraps the profile data in a ``_meta`` envelope::

    {
      "_meta": {
        "schema_version": 1,
        "workbook_hash": "<sha256 of last imported .xlsx>",
        "last_modified": "<ISO datetime>"
      },
      ... profile fields ...
    }

The workbook_hash lets sync() detect genuine Excel edits without relying on
unreliable file mtimes (which OneDrive can bump without content changes).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from helpers.domain.profile import Profile

# Increment when the JSON schema changes in a breaking way
SCHEMA_VERSION = 1


# ── Hash helper ────────────────────────────────────────────────────────────────

def hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path* contents."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Serialisation ──────────────────────────────────────────────────────────────

def serialize_profile(profile: Profile, workbook_hash: str = "") -> str:
    """Return the profile hierarchy as a pretty-printed JSON string.

    The envelope includes ``_meta`` so sync logic can verify freshness
    without relying on file-system timestamps.
    """
    envelope = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "workbook_hash": workbook_hash,
            "last_modified": datetime.now(tz=timezone.utc).isoformat(),
        },
        **profile.to_dict(),
    }
    return json.dumps(envelope, indent=2, ensure_ascii=False, default=str)


def deserialize_profile(json_str: str) -> tuple[Profile, dict]:
    """Reconstruct a Profile hierarchy from a JSON string.

    Returns ``(profile, meta)`` where *meta* is the ``_meta`` envelope dict
    (empty dict if absent, e.g. for legacy files without the envelope).
    """
    data = json.loads(json_str)
    meta = data.pop("_meta", {})
    return Profile.from_dict(data), meta


def save_profile_json(
    profile: Profile,
    path: Path,
    *,
    workbook_hash: str = "",
) -> None:
    """Write the profile hierarchy to a JSON file.

    Pass *workbook_hash* (from :func:`hash_file`) when saving after an Excel
    import so the hash is stored for future sync comparisons.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_profile(profile, workbook_hash), encoding="utf-8")


def load_profile_json(path: Path) -> tuple[Profile, dict]:
    """Load a profile hierarchy from a JSON file.

    Returns ``(profile, meta)`` — callers that don't need meta can ignore it::

        profile, _ = load_profile_json(path)
    """
    return deserialize_profile(path.read_text(encoding="utf-8-sig"))
