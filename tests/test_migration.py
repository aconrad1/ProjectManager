"""Tests for the migration layer (helpers.migration)."""

import json
import pytest
from unittest.mock import patch, MagicMock
from helpers.migration import build_title_to_id_map, migrate_to_id_keying


def _make_task(task_id: str, title: str):
    """Create a minimal mock task."""
    t = MagicMock()
    t.id = task_id
    t.title = title
    return t


def _make_profile(tasks: list):
    """Create a minimal mock profile with all_tasks."""
    p = MagicMock()
    p.all_tasks = tasks
    return p


class TestBuildTitleToIdMap:
    def test_basic_mapping(self):
        tasks = [_make_task("T-001", "Review drawings"), _make_task("T-002", "Inspect valves")]
        profile = _make_profile(tasks)
        mapping = build_title_to_id_map(profile)
        assert mapping == {"Review drawings": "T-001", "Inspect valves": "T-002"}

    def test_duplicate_titles_first_wins(self):
        tasks = [_make_task("T-001", "Dup"), _make_task("T-002", "Dup")]
        profile = _make_profile(tasks)
        mapping = build_title_to_id_map(profile)
        assert mapping == {"Dup": "T-001"}

    def test_empty_profile(self):
        profile = _make_profile([])
        assert build_title_to_id_map(profile) == {}

    def test_empty_title_skipped(self):
        tasks = [_make_task("T-001", ""), _make_task("T-002", "Good")]
        profile = _make_profile(tasks)
        mapping = build_title_to_id_map(profile)
        assert mapping == {"Good": "T-002"}


class TestMigrateToIdKeying:
    @patch("helpers.migration.migrate_attachments", return_value=0)
    @patch("helpers.migration.migrate_links", return_value=0)
    @patch("helpers.migration.migrate_notes", return_value=0)
    def test_calls_all_sub_migrations(self, m_notes, m_links, m_attach):
        profile = _make_profile([_make_task("T-001", "Task A")])
        migrate_to_id_keying(profile)
        expected_map = {"Task A": "T-001"}
        m_notes.assert_called_once_with(expected_map)
        m_links.assert_called_once_with(expected_map)
        m_attach.assert_called_once_with(expected_map)

    @patch("helpers.migration.migrate_attachments", return_value=0)
    @patch("helpers.migration.migrate_links", return_value=0)
    @patch("helpers.migration.migrate_notes", return_value=0)
    def test_noop_on_empty_profile(self, m_notes, m_links, m_attach):
        profile = _make_profile([])
        migrate_to_id_keying(profile)
        m_notes.assert_not_called()
        m_links.assert_not_called()
        m_attach.assert_not_called()
