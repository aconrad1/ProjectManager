"""
pipelines/ingest_load_sheet.py

Validates and ingests a load-sheet CSV into fact_hours.csv.

Usage:
    python pipelines/ingest_load_sheet.py load_sheets/my_update.csv

Load-sheet format (CSV):
    calendar_month,full_name,project_code,hours
    2026-04,"Conrad, Ashwin",SOME_PROJECT_CODE,16

Rules:
  - Any validation failure aborts the entire ingest (no partial loads).
  - A processed sheet is moved to load_sheets/archive/.
  - An audit log is written to audits/.
"""

import csv
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import validate_load_sheet

BASE        = Path(__file__).resolve().parent.parent
FACT_HOURS  = BASE / "facts"            / "fact_hours.csv"
ARCHIVE_DIR = BASE / "load_sheets"     / "archive"
AUDIT_DIR   = BASE / "audits"

FACT_COLS = ["fact_id", "date_id", "person_id", "project_id",
             "hours", "source", "created_at"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def source_tag(filename: str) -> str:
    """Derive a short source label from the load-sheet filename."""
    stem = Path(filename).stem  # strip directory and extension
    # Normalise to lowercase, replace whitespace/special chars with _
    import re
    tag = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")
    return f"load_{tag}"


def append_to_fact_hours(records: list[dict], source: str, created_at: str) -> int:
    """Append validated records to fact_hours.csv. Returns rows written."""
    FACT_HOURS.parent.mkdir(parents=True, exist_ok=True)

    # Ensure header exists if file is empty / new
    write_header = not FACT_HOURS.exists() or FACT_HOURS.stat().st_size == 0
    rows_written = 0

    with open(FACT_HOURS, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FACT_COLS, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        for rec in records:
            writer.writerow({
                "fact_id":    new_uuid(),
                "date_id":    rec["date_id"],
                "person_id":  rec["person_id"],
                "project_id": rec["project_id"],
                "hours":      rec["hours"],
                "source":     source,
                "created_at": created_at,
            })
            rows_written += 1

    return rows_written


def write_audit_log(
    filename:    str,
    timestamp:   str,
    rows_added:  int,
    success:     bool,
    errors:      list[str],
    warnings:    list[str],
):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    stem   = Path(filename).stem
    log_ts = timestamp.replace(":", "").replace("-", "").replace("T", "_")[:15]
    log_path = AUDIT_DIR / f"ingest_{stem}_{log_ts}.json"

    payload = {
        "filename":   filename,
        "timestamp":  timestamp,
        "success":    success,
        "rows_added": rows_added,
        "errors":     errors,
        "warnings":   warnings,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"  audit log → {log_path.relative_to(BASE)}")
    return log_path


def archive_sheet(csv_path: Path):
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest = ARCHIVE_DIR / csv_path.name
    # Avoid overwriting an existing archive entry
    if dest.exists():
        ts   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        dest = ARCHIVE_DIR / f"{csv_path.stem}_{ts}{csv_path.suffix}"
    shutil.move(str(csv_path), str(dest))
    print(f"  archived  → {dest.relative_to(BASE)}")


# ---------------------------------------------------------------------------
# Main ingest flow
# ---------------------------------------------------------------------------

def ingest(csv_path: Path) -> bool:
    """
    Full ingest pipeline. Returns True on success, False on failure.
    """
    timestamp = utc_now()
    filename  = csv_path.name

    print(f"\nIngesting: {filename}")
    print(f"Timestamp: {timestamp}")

    # 1. Validate
    print("\n[1/4] Validating…")
    result, records = validate_load_sheet(csv_path)

    if not result.ok:
        print(result.report())
        write_audit_log(
            filename   = filename,
            timestamp  = timestamp,
            rows_added = 0,
            success    = False,
            errors     = [str(e) for e in result.errors],
            warnings   = [],
        )
        print("\nIngest aborted -- see audit log for details.")
        return False

    print(f"  {len(records)} row(s) passed validation")

    # 2. Append to fact_hours
    print("\n[2/4] Appending to fact_hours.csv…")
    src        = source_tag(filename)
    rows_added = append_to_fact_hours(records, src, timestamp)
    print(f"  appended {rows_added} row(s)  (source='{src}')")

    # 3. Archive the processed sheet
    print("\n[3/4] Archiving load sheet…")
    archive_sheet(csv_path)

    # 4. Write audit log
    print("\n[4/4] Writing audit log…")
    write_audit_log(
        filename   = filename,
        timestamp  = timestamp,
        rows_added = rows_added,
        success    = True,
        errors     = [],
        warnings   = [],
    )

    print(f"\nIngest complete -- {rows_added} row(s) added to fact_hours.csv")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        sys.exit(
            "Usage: python pipelines/ingest_load_sheet.py "
            "load_sheets/my_update.csv"
        )

    csv_path = Path(sys.argv[1])
    if not csv_path.is_absolute():
        csv_path = Path.cwd() / csv_path

    if not csv_path.exists():
        sys.exit(f"File not found: {csv_path}")

    success = ingest(csv_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
