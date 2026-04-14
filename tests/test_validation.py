"""Tests for the validation layer (helpers.validation)."""

import pytest
from datetime import date
from helpers.validation import (
    validate_project,
    validate_task,
    validate_deliverable,
    ValidationError,
    format_errors,
)


# ── validate_project ───────────────────────────────────────────────────────────

class TestValidateProject:
    def test_valid_minimal(self):
        assert validate_project({"title": "Site Audit"}) == []

    def test_valid_full(self):
        data = {
            "title": "Site Audit",
            "category": "Ongoing",
            "priority": 2,
            "start": date(2025, 1, 1),
            "end": date(2025, 6, 1),
        }
        assert validate_project(data) == []

    def test_missing_title(self):
        errors = validate_project({})
        assert any("title" in e.lower() for e in errors)

    def test_blank_title(self):
        errors = validate_project({"title": "   "})
        assert any("title" in e.lower() for e in errors)

    def test_invalid_category(self):
        errors = validate_project({"title": "X", "category": "Bogus"})
        assert any("category" in e.lower() for e in errors)

    def test_invalid_priority_out_of_range(self):
        errors = validate_project({"title": "X", "priority": 99})
        assert any("priority" in e.lower() for e in errors)

    def test_invalid_priority_type(self):
        errors = validate_project({"title": "X", "priority": "high"})
        assert any("priority" in e.lower() for e in errors)

    def test_start_after_end(self):
        data = {"title": "X", "start": date(2025, 6, 1), "end": date(2025, 1, 1)}
        errors = validate_project(data)
        assert any("start" in e.lower() and "end" in e.lower() for e in errors)


# ── validate_task ──────────────────────────────────────────────────────────────

class TestValidateTask:
    def test_valid(self):
        assert validate_task({"title": "Review drawings", "priority": 1}) == []

    def test_missing_title(self):
        errors = validate_task({"priority": 1})
        assert any("title" in e.lower() for e in errors)

    def test_invalid_status(self):
        errors = validate_task({"title": "X", "status": "Done"})
        assert any("status" in e.lower() for e in errors)

    def test_valid_statuses(self):
        for s in ("Not Started", "In Progress", "On Track", "Ongoing",
                  "Recurring", "On Hold", "Completed"):
            assert validate_task({"title": "X", "status": s}) == []

    def test_priority_boundary(self):
        assert validate_task({"title": "X", "priority": 1}) == []
        assert validate_task({"title": "X", "priority": 5}) == []
        assert len(validate_task({"title": "X", "priority": 0})) > 0
        assert len(validate_task({"title": "X", "priority": 6})) > 0


# ── validate_deliverable ──────────────────────────────────────────────────────

class TestValidateDeliverable:
    def test_valid(self):
        data = {
            "title": "Draft report",
            "percent_complete": 50,
            "time_allocated": 4.0,
            "time_spent": 1.5,
        }
        assert validate_deliverable(data) == []

    def test_missing_title(self):
        errors = validate_deliverable({})
        assert any("title" in e.lower() for e in errors)

    def test_percent_out_of_range(self):
        errors = validate_deliverable({"title": "X", "percent_complete": 150})
        assert any("percent" in e.lower() for e in errors)

    def test_negative_time(self):
        errors = validate_deliverable({"title": "X", "time_allocated": -1})
        assert any("time allocated" in e.lower() for e in errors)

    def test_negative_time_spent(self):
        errors = validate_deliverable({"title": "X", "time_spent": -2.0})
        assert any("time spent" in e.lower() for e in errors)

    def test_non_numeric_time(self):
        errors = validate_deliverable({"title": "X", "time_allocated": "abc"})
        assert any("time allocated" in e.lower() for e in errors)


# ── ValidationError / format_errors ───────────────────────────────────────────

class TestValidationError:
    def test_single_error(self):
        err = ValidationError(["Bad input."])
        assert str(err) == "Bad input."
        assert err.errors == ["Bad input."]

    def test_multiple_errors(self):
        err = ValidationError(["A", "B"])
        assert "A" in str(err) and "B" in str(err)

    def test_format_errors_single(self):
        assert format_errors(["Oops"]) == "Oops"

    def test_format_errors_multiple(self):
        result = format_errors(["A", "B"])
        assert "A" in result and "B" in result
