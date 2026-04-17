"""
pipelines/report.py

Sample report script demonstrating common demand-plan aggregations.
All totals are computed at query time from the star schema – no stored sums.

Usage:
    python pipelines/report.py [--month 2026-04] [--out reports/]

Outputs one CSV per report grouping to the specified output directory
(or prints to stdout if --out is not given).
"""

import csv
import argparse
import sys
from collections import defaultdict
from pathlib import Path

BASE        = Path(__file__).resolve().parent.parent
DIM_PERSON  = BASE / "dimensions" / "dim_person.csv"
DIM_PROJECT = BASE / "dimensions" / "dim_project.csv"
DIM_DATE    = BASE / "dimensions" / "dim_date.csv"
DIM_FAC     = BASE / "dimensions" / "dim_facility.csv"
FACT_HOURS  = BASE / "facts"      / "fact_hours.csv"


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"File not found: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def index_by(rows: list[dict], key: str) -> dict[str, dict]:
    return {r[key]: r for r in rows if r.get(key)}


# ---------------------------------------------------------------------------
# Core join
# ---------------------------------------------------------------------------

def build_fact_view(month_filter: str | None = None) -> list[dict]:
    """
    Returns a flat list of enriched fact rows joined to all dimensions.
    Optionally filter to a single calendar_month (YYYY-MM).
    """
    people   = index_by(load_csv(DIM_PERSON),  "person_id")
    projects = index_by(load_csv(DIM_PROJECT), "project_id")
    dates    = index_by(load_csv(DIM_DATE),    "date_id")
    facs     = index_by(load_csv(DIM_FAC),     "facility_id")
    facts    = load_csv(FACT_HOURS)

    view = []
    for f in facts:
        if month_filter and f.get("date_id") != month_filter:
            continue
        person  = people .get(f.get("person_id",  ""), {})
        project = projects.get(f.get("project_id", ""), {})
        d       = dates  .get(f.get("date_id",     ""), {})
        fac     = facs   .get(project.get("facility_id", ""), {})

        try:
            hours = float(f.get("hours", 0))
        except ValueError:
            hours = 0.0

        view.append({
            "fact_id":        f.get("fact_id", ""),
            "date_id":        f.get("date_id", ""),
            "calendar_month": d.get("calendar_month", f.get("date_id", "")),
            "person_id":      f.get("person_id", ""),
            "full_name":      person.get("full_name", ""),
            "group":          person.get("group", ""),
            "project_id":     f.get("project_id", ""),
            "project_name":   project.get("project_name", ""),
            "project_code":   project.get("project_code", ""),
            "project_type":   project.get("project_type", ""),
            "facility_id":    project.get("facility_id", ""),
            "facility_name":  fac.get("facility_name", ""),
            "hours":          hours,
            "source":         f.get("source", ""),
        })
    return view


# ---------------------------------------------------------------------------
# Aggregation helper
# ---------------------------------------------------------------------------

def aggregate(view: list[dict], group_keys: list[str]) -> list[dict]:
    totals: dict[tuple, float] = defaultdict(float)
    for row in view:
        key = tuple(row.get(k, "") for k in group_keys)
        totals[key] += row["hours"]

    result = []
    for key, hrs in sorted(totals.items()):
        rec = dict(zip(group_keys, key))
        rec["hours"] = round(hrs, 2)
        result.append(rec)
    return result


# ---------------------------------------------------------------------------
# Report definitions
# ---------------------------------------------------------------------------

REPORTS = {
    "hours_by_person_month": {
        "keys":  ["full_name", "calendar_month"],
        "title": "Hours by Person × Month",
    },
    "hours_by_project_month": {
        "keys":  ["project_name", "calendar_month"],
        "title": "Hours by Project × Month",
    },
    "hours_by_facility_type_month": {
        "keys":  ["facility_name", "project_type", "calendar_month"],
        "title": "Hours by Facility × Project Type × Month",
    },
    "hours_by_group_month": {
        "keys":  ["group", "calendar_month"],
        "title": "Hours by Group × Month",
    },
}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_table(rows: list[dict], title: str):
    if not rows:
        print(f"\n{title}\n  (no data)")
        return
    cols = list(rows[0].keys())
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows))
              for c in cols}
    sep = "  ".join("-" * widths[c] for c in cols)
    hdr = "  ".join(c.ljust(widths[c]) for c in cols)
    print(f"\n{title}")
    print(hdr)
    print(sep)
    for r in rows:
        print("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))
    total = sum(r.get("hours", 0) for r in rows)
    print(sep)
    print(f"  TOTAL: {total:,.1f} hours  ({len(rows)} rows)")


def write_report_csv(rows: list[dict], path: Path):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate demand-plan reports.")
    parser.add_argument("--month", metavar="YYYY-MM",
                        help="Filter to a single calendar month")
    parser.add_argument("--out", metavar="DIR",
                        help="Output directory for CSV reports "
                             "(prints to console if omitted)")
    args = parser.parse_args()

    print("Loading data…")
    view = build_fact_view(month_filter=args.month)

    if not view:
        print("No data found" +
              (f" for month {args.month}" if args.month else "") + ".")
        return

    total_hours = sum(r["hours"] for r in view)
    month_str   = f" (month={args.month})" if args.month else ""
    print(f"  {len(view)} fact rows{month_str} | total hours = {total_hours:,.1f}")

    out_dir = Path(args.out) if args.out else None

    for report_id, meta in REPORTS.items():
        rows = aggregate(view, meta["keys"])
        if out_dir:
            write_report_csv(rows, out_dir / f"{report_id}.csv")
        else:
            print_table(rows, meta["title"])


if __name__ == "__main__":
    main()
