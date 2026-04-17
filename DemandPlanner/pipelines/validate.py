"""
pipelines/validate.py

Reusable schema + foreign-key validation for load sheets.
Imported by ingest_load_sheet.py; can also be run standalone.

Usage (standalone):
    python pipelines/validate.py load_sheets/my_update.csv
"""

import csv
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

BASE = Path(__file__).resolve().parent.parent

DIM_PERSON   = BASE / "dimensions" / "dim_person.csv"
DIM_PROJECT  = BASE / "dimensions" / "dim_project.csv"
DIM_DATE     = BASE / "dimensions" / "dim_date.csv"

REQUIRED_COLUMNS = ["calendar_month", "full_name", "project_code", "hours"]

# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    row_number: int       # 1-based, excluding header
    column:     str
    value:      str
    message:    str

    def __str__(self):
        return f"Row {self.row_number} [{self.column}={self.value!r}]: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add(self, row: int, col: str, val: str, msg: str):
        self.errors.append(ValidationError(row, col, val, msg))

    def report(self) -> str:
        if self.ok:
            return "Validation passed – no errors."
        lines = [f"Validation failed – {len(self.errors)} error(s):"]
        for e in self.errors:
            lines.append(f"  {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dimension loaders
# ---------------------------------------------------------------------------

def _load_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Dimension file not found: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_active_people() -> dict[str, str]:
    """Returns dict: full_name (stripped) -> person_id  for active people."""
    rows = _load_csv(DIM_PERSON)
    return {
        r["full_name"].strip(): r["person_id"]
        for r in rows
        if r.get("active_flag", "true").lower() == "true"
        and r["full_name"].strip()
    }


def load_projects() -> dict[str, str]:
    """Returns dict: project_code -> project_id  for all projects."""
    rows = _load_csv(DIM_PROJECT)
    return {
        r["project_code"].strip(): r["project_id"]
        for r in rows
        if r["project_code"].strip()
    }


def load_date_ids() -> set[str]:
    """Returns set of valid date_id strings ('YYYY-MM')."""
    rows = _load_csv(DIM_DATE)
    return {r["date_id"].strip() for r in rows if r["date_id"].strip()}


# ---------------------------------------------------------------------------
# Schema validation helpers
# ---------------------------------------------------------------------------

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _check_schema(reader_fieldnames: list[str], result: ValidationResult):
    """Verify all required columns are present."""
    missing = [c for c in REQUIRED_COLUMNS if c not in reader_fieldnames]
    if missing:
        result.add(0, "header", "", f"Missing required columns: {missing}")


def _validate_row(
    row_num:    int,
    row:        dict,
    people:     dict[str, str],
    projects:   dict[str, str],
    date_ids:   set[str],
    seen_keys:  set[tuple],
    result:     ValidationResult,
) -> Optional[dict]:
    """
    Validates a single data row. Returns a normalized record on success,
    or None on any failure (errors are appended to result).
    """
    ok = True

    # calendar_month
    cal_month = (row.get("calendar_month") or "").strip()
    if not cal_month:
        result.add(row_num, "calendar_month", cal_month, "Value is blank")
        ok = False
    elif not MONTH_RE.match(cal_month):
        result.add(row_num, "calendar_month", cal_month,
                   "Must be YYYY-MM format (e.g. 2026-04)")
        ok = False
    elif cal_month not in date_ids:
        result.add(row_num, "calendar_month", cal_month,
                   "Not found in dim_date – add it first")
        ok = False

    # full_name
    full_name = (row.get("full_name") or "").strip()
    if not full_name:
        result.add(row_num, "full_name", full_name, "Value is blank")
        ok = False
    elif full_name not in people:
        result.add(row_num, "full_name", full_name,
                   "No active person with this full_name in dim_person")
        ok = False

    # project_code
    proj_code = (row.get("project_code") or "").strip()
    if not proj_code:
        result.add(row_num, "project_code", proj_code, "Value is blank")
        ok = False
    elif proj_code not in projects:
        result.add(row_num, "project_code", proj_code,
                   "Not found in dim_project")
        ok = False

    # hours
    hours_raw = (row.get("hours") or "").strip()
    try:
        hours = float(hours_raw)
        if hours < 0:
            result.add(row_num, "hours", hours_raw, "Must be >= 0")
            ok = False
    except ValueError:
        result.add(row_num, "hours", hours_raw, "Must be a number")
        ok = False
        hours = None

    if not ok:
        return None

    # Duplicate check within this load sheet
    dup_key = (full_name, proj_code, cal_month)
    if dup_key in seen_keys:
        result.add(row_num, "duplicate",
                   f"{full_name}|{proj_code}|{cal_month}",
                   "Duplicate row (same person, project, month) in this sheet")
        return None
    seen_keys.add(dup_key)

    return {
        "calendar_month": cal_month,
        "full_name":      full_name,
        "project_code":   proj_code,
        "hours":          hours,
        "person_id":      people[full_name],
        "project_id":     projects[proj_code],
        "date_id":        cal_month,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_load_sheet(
    csv_path: Path,
) -> tuple[ValidationResult, list[dict]]:
    """
    Validate a load-sheet CSV against the dimension tables.

    Returns:
        result  – ValidationResult (result.ok is True only if zero errors)
        records – list of normalized dicts ready for fact insertion
                  (empty if result.ok is False)
    """
    result  = ValidationResult()
    records: list[dict] = []

    if not csv_path.exists():
        result.add(0, "file", str(csv_path), "File not found")
        return result, []

    try:
        people   = load_active_people()
        projects = load_projects()
        date_ids = load_date_ids()
    except FileNotFoundError as exc:
        result.add(0, "dimension", "", str(exc))
        return result, []

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        _check_schema(reader.fieldnames or [], result)
        if not result.ok:
            return result, []

        seen_keys: set[tuple] = set()
        for i, row in enumerate(reader, start=1):
            rec = _validate_row(i, row, people, projects, date_ids,
                                seen_keys, result)
            if rec is not None:
                records.append(rec)

    # If any errors were found, discard all records (no partial loads)
    if not result.ok:
        records = []

    return result, records


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        sys.exit("Usage: python pipelines/validate.py <load_sheet.csv>")

    path = Path(sys.argv[1])
    res, recs = validate_load_sheet(path)
    print(res.report())
    if res.ok:
        print(f"{len(recs)} record(s) would be ingested.")
