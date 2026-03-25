"""Tests for ID-keyed notes (helpers.attachments.notes)."""

import json
import pytest
from unittest.mock import patch, MagicMock
from helpers.attachments.notes import (
    add_note, list_notes, delete_notes, migrate_notes,
    load_notes, save_notes,
)


@pytest.fixture
def notes_store(tmp_path):
    """Provide an in-memory notes dict and patch load/save."""
    store = {"_data": {}}

    def _load():
        return dict(store["_data"])

    def _save(notes):
        store["_data"] = dict(notes)

    with patch("helpers.attachments.notes.load_json", side_effect=lambda *a, **kw: _load()), \
         patch("helpers.attachments.notes.save_json", side_effect=lambda path, data: _save(data)):
        yield store


class TestIdKeyedNotes:
    def test_add_and_list(self, notes_store):
        add_note("T-001", "First note")
        add_note("T-001", "Second note")
        result = list_notes("T-001")
        assert len(result) == 2
        # newest first
        assert result[0]["text"] == "Second note"
        assert result[1]["text"] == "First note"

    def test_list_empty(self, notes_store):
        assert list_notes("T-999") == []

    def test_delete(self, notes_store):
        add_note("T-001", "A note")
        delete_notes("T-001")
        assert list_notes("T-001") == []

    def test_delete_nonexistent(self, notes_store):
        # Should not raise
        delete_notes("T-999")


class TestMigrateNotes:
    def test_basic_migration(self, notes_store):
        # Seed with title-keyed data
        notes_store["_data"] = {
            "Review drawings": [{"timestamp": "2025-01-01 10:00", "text": "note1"}],
            "Inspect valves": [{"timestamp": "2025-01-01 11:00", "text": "note2"}],
        }
        title_to_id = {"Review drawings": "T-001", "Inspect valves": "T-002"}
        count = migrate_notes(title_to_id)
        assert count == 2
        data = notes_store["_data"]
        assert "T-001" in data
        assert "T-002" in data
        assert "Review drawings" not in data

    def test_already_migrated_skipped(self, notes_store):
        notes_store["_data"] = {
            "T-001": [{"timestamp": "2025-01-01 10:00", "text": "already id-keyed"}],
        }
        count = migrate_notes({"Some Title": "T-002"})
        assert count == 0

    def test_unresolvable_preserved(self, notes_store):
        notes_store["_data"] = {
            "Unknown Title": [{"timestamp": "2025-01-01 10:00", "text": "orphan"}],
        }
        count = migrate_notes({"Other": "T-001"})
        assert count == 0
        assert "Unknown Title" in notes_store["_data"]

    def test_mixed_entries(self, notes_store):
        notes_store["_data"] = {
            "T-001": [{"timestamp": "2025-01-01 10:00", "text": "already ok"}],
            "Old Title": [{"timestamp": "2025-01-01 11:00", "text": "needs migration"}],
        }
        count = migrate_notes({"Old Title": "T-002"})
        assert count == 1
        data = notes_store["_data"]
        assert "T-001" in data and "T-002" in data
        assert "Old Title" not in data
