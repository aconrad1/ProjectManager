# Demand Planner

CSV-backed demand planning model using a star schema. All hour mutations flow through validated load sheets; the fact table is append-only.

## Structure

```
dimensions/         Dimension CSVs (human-editable, schema-locked)
facts/              fact_hours.csv (append-only)
load_sheets/        Drop incoming load sheets here
load_sheets/archive/  Processed sheets are moved here automatically
pipelines/          Python scripts for extraction, ingest, reporting
audits/             Ingest logs written after every run
```

## Quick Start

### 1. Run baseline extraction (one-time)

```bash
python pipelines/extract_baseline.py "Demand Plan 0409 copy.xlsx"
```

### 2. Ingest a load sheet

```bash
python pipelines/ingest_load_sheet.py load_sheets/my_update.csv
```

### 3. Generate a report

```bash
python pipelines/report.py
```

## Load Sheet Format

```csv
calendar_month,full_name,project_code,hours
2026-04,"Conrad, Ashwin",250800103,16
```

## Rules

- Never edit `facts/fact_hours.csv` directly.
- Corrections are submitted as new load sheets (latest source batch wins at reporting time).
- Deactivate people/projects by setting `active_flag = false`; never delete rows from dimensions.
- See `plan.md` for full schema documentation and governance rules.
