"""Tests for configurable scheduling fallback (helpers.scheduling.engine)."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from helpers.scheduling.engine import _task_hours


def _make_deliverable(time_allocated):
    d = MagicMock()
    d.time_allocated = time_allocated
    return d


def _make_task(deliverables=None):
    t = MagicMock()
    t.deliverables = deliverables or []
    return t


class TestTaskHours:
    def test_with_deliverables(self):
        task = _make_task([_make_deliverable(2.0), _make_deliverable(3.0)])
        assert _task_hours(task) == 5.0

    def test_partial_none(self):
        task = _make_task([_make_deliverable(2.0), _make_deliverable(None)])
        assert _task_hours(task) == 2.0

    def test_all_none_uses_default(self):
        task = _make_task([_make_deliverable(None), _make_deliverable(None)])
        with patch("helpers.scheduling.engine.load_config", return_value={"default_time_allocated_hours": 1.0}):
            assert _task_hours(task) == 1.0

    def test_empty_deliverables_uses_default(self):
        task = _make_task([])
        with patch("helpers.scheduling.engine.load_config", return_value={"default_time_allocated_hours": 1.0}):
            assert _task_hours(task) == 1.0

    def test_custom_default(self):
        task = _make_task([])
        with patch("helpers.scheduling.engine.load_config", return_value={"default_time_allocated_hours": 2.5}):
            assert _task_hours(task) == 2.5

    def test_missing_config_key_falls_back_to_1(self):
        task = _make_task([])
        with patch("helpers.scheduling.engine.load_config", return_value={}):
            assert _task_hours(task) == 1.0
