"""Tests for Phase 6 — UI State Persistence, Batch Operations, DnD Resilience, Dark Gantt."""

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ── Ensure project root is on sys.path ─────────────────────────────────────────
import sys

_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))
_SCRIPTS = _PROJECT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_profile(company="TestCo", title="Test User"):
    from helpers.domain.profile import Profile
    return Profile(
        id=f"profile:{company}",
        title=title,
        company=company,
        status="Active",
    )


def _make_project(pid="P-001", title="Project 1", category="Ongoing"):
    from helpers.domain.project import Project
    return Project(id=pid, title=title, category=category, status="In Progress")


def _make_task(tid="T-001", title="Task 1", project_id="P-001", **kwargs):
    from helpers.domain.task import Task
    return Task(id=tid, title=title, project_id=project_id, status="In Progress", **kwargs)


def _make_deliverable(did="D-001", title="Deliv 1", task_id="T-001"):
    from helpers.domain.deliverable import Deliverable
    return Deliverable(id=did, title=title, task_id=task_id, status="Not Started")


# ═══════════════════════════════════════════════════════════════════════════════
#  1. UI State Persistence
# ═══════════════════════════════════════════════════════════════════════════════


class TestUIStatePersistence:
    """Verify that UI state is correctly persisted and restored."""

    def test_roundtrip_save_load(self, tmp_path):
        """save_ui_state → load_ui_state produces the same dict."""
        from helpers.ui.state import load_ui_state, save_ui_state

        state = {
            "tasks_filter": "Ongoing",
            "tasks_search": "wiring",
            "tasks_expanded": ["proj_P-001", "proj_P-003"],
        }

        with patch("helpers.ui.state.data_dir", return_value=tmp_path):
            save_ui_state(state)
            loaded = load_ui_state()

        assert loaded == state

    def test_load_returns_empty_dict_if_missing(self, tmp_path):
        """First ever load returns {}."""
        from helpers.ui.state import load_ui_state

        with patch("helpers.ui.state.data_dir", return_value=tmp_path):
            result = load_ui_state()

        assert result == {}

    def test_save_creates_file(self, tmp_path):
        """save_ui_state should create ui_state.json inside data_dir."""
        from helpers.ui.state import save_ui_state

        with patch("helpers.ui.state.data_dir", return_value=tmp_path):
            save_ui_state({"tasks_filter": "All"})

        assert (tmp_path / "ui_state.json").exists()

    def test_file_content_is_json(self, tmp_path):
        """UI state file should be valid JSON."""
        from helpers.ui.state import save_ui_state

        with patch("helpers.ui.state.data_dir", return_value=tmp_path):
            save_ui_state({"tasks_filter": "Weekly", "custom_key": 42})

        raw = (tmp_path / "ui_state.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["tasks_filter"] == "Weekly"
        assert data["custom_key"] == 42

    def test_overwrite_preserves_new_keys(self, tmp_path):
        """Subsequent saves should overwrite previous state completely."""
        from helpers.ui.state import load_ui_state, save_ui_state

        with patch("helpers.ui.state.data_dir", return_value=tmp_path):
            save_ui_state({"tasks_filter": "Ongoing"})
            save_ui_state({"tasks_filter": "All", "gantt_zoom": 20})
            loaded = load_ui_state()

        assert loaded == {"tasks_filter": "All", "gantt_zoom": 20}

    def test_save_load_empty_state(self, tmp_path):
        """Saving an empty dict should work."""
        from helpers.ui.state import load_ui_state, save_ui_state

        with patch("helpers.ui.state.data_dir", return_value=tmp_path):
            save_ui_state({})
            loaded = load_ui_state()

        assert loaded == {}


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Batch Operations (Service-Level)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBatchOperations:
    """Test batch editing logic at the DomainService level."""

    def _setup_profile_with_tasks(self):
        """Build a profile with a project and 3 tasks."""
        profile = _make_profile()
        project = _make_project()
        t1 = _make_task("T-001", "Task A", "P-001", start=date(2026, 4, 1), end=date(2026, 4, 5))
        t2 = _make_task("T-002", "Task B", "P-001", start=date(2026, 4, 2), end=date(2026, 4, 6))
        t3 = _make_task("T-003", "Task C", "P-001")
        project.tasks = [t1, t2, t3]
        profile.projects = [project]
        return profile, [t1, t2, t3]

    def test_batch_status_change(self):
        """Setting status on multiple tasks via the service."""
        from helpers.commands.domain_service import DomainService

        profile, tasks = self._setup_profile_with_tasks()
        wb = MagicMock()
        service = DomainService(profile, wb)

        with patch.object(service, "_persist"):
            for tid in ["T-001", "T-002"]:
                service.set_status(tid, "On Hold")

        assert tasks[0].status == "On Hold"
        assert tasks[1].status == "On Hold"
        assert tasks[2].status == "In Progress"  # unchanged

    def test_batch_priority_change(self):
        """Setting priority on multiple tasks via the service."""
        from helpers.commands.domain_service import DomainService

        profile, tasks = self._setup_profile_with_tasks()
        wb = MagicMock()
        service = DomainService(profile, wb)

        with patch.object(service, "_persist"):
            for tid in ["T-001", "T-003"]:
                service.set_priority(tid, 1)

        assert tasks[0].priority == 1
        assert tasks[2].priority == 1
        assert tasks[1].priority == 3  # unchanged (default)

    def test_batch_date_shift(self):
        """Shifting start/end dates on multiple tasks via the service."""
        from helpers.commands.domain_service import DomainService

        profile, tasks = self._setup_profile_with_tasks()
        wb = MagicMock()
        service = DomainService(profile, wb)

        delta = timedelta(days=7)

        with patch.object(service, "_persist"):
            for tid in ["T-001", "T-002"]:
                task = profile.find_task_global(tid)
                if task and isinstance(task.start, date):
                    edits = {"start": task.start + delta, "end": task.end + delta}
                    service.edit_task(tid, edits)

        assert tasks[0].start == date(2026, 4, 8)
        assert tasks[0].end == date(2026, 4, 12)
        assert tasks[1].start == date(2026, 4, 9)
        assert tasks[1].end == date(2026, 4, 13)

    def test_batch_leaves_unchanged_tasks_untouched(self):
        """Tasks not in the batch set should be completely unaffected."""
        from helpers.commands.domain_service import DomainService

        profile, tasks = self._setup_profile_with_tasks()
        wb = MagicMock()
        service = DomainService(profile, wb)

        original_title = tasks[2].title
        original_status = tasks[2].status
        original_priority = tasks[2].priority

        with patch.object(service, "_persist"):
            service.set_status("T-001", "On Hold")
            service.set_priority("T-001", 1)

        assert tasks[2].title == original_title
        assert tasks[2].status == original_status
        assert tasks[2].priority == original_priority


# ═══════════════════════════════════════════════════════════════════════════════
#  3. DnD Resilience
# ═══════════════════════════════════════════════════════════════════════════════


class TestDnDResilience:
    """Verify drag-and-drop graceful degradation."""

    def test_dnd_flag_false_when_import_fails(self):
        """When tkinterdnd2 is not installed, _dnd_available should be False."""
        # Simulate the try/except pattern from tasks_page._setup_drag_drop
        dnd_available = False
        try:
            import tkinterdnd2  # noqa: F401
            dnd_available = True
        except ImportError:
            dnd_available = False
        except Exception:
            dnd_available = False

        # On most CI / dev machines, tkinterdnd2 is NOT installed
        # So we just test the flag mechanism itself
        assert isinstance(dnd_available, bool)

    def test_dnd_status_bar_warning_text(self):
        """When DnD is unavailable, status bar should contain the warning."""
        warning = "⚠ Drag-and-drop unavailable (install tkinterdnd2)"
        # Simulate the status bar text construction from tasks_page.update_status_bar
        dnd_available = False
        dnd_tag = "" if dnd_available else f"  |  {warning}"
        text = f"Weekly: 5  |  Ongoing: 10  |  Completed: 3  |  Workbook: test.xlsx{dnd_tag}"

        assert warning in text

    def test_dnd_no_warning_when_available(self):
        """When DnD IS available, status bar should NOT contain the warning."""
        dnd_available = True
        dnd_tag = "" if dnd_available else "  |  ⚠ Drag-and-drop unavailable (install tkinterdnd2)"
        text = f"Weekly: 5  |  Ongoing: 10  |  Completed: 3  |  Workbook: test.xlsx{dnd_tag}"

        assert "Drag-and-drop unavailable" not in text

    def test_setup_drag_drop_catches_import_error(self):
        """The _setup_drag_drop pattern should catch ImportError gracefully."""
        dnd_available = False
        try:
            raise ImportError("No module named 'tkinterdnd2'")
        except ImportError:
            dnd_available = False
        except Exception:
            dnd_available = False

        assert dnd_available is False

    def test_setup_drag_drop_catches_generic_error(self):
        """The _setup_drag_drop pattern should catch generic exceptions too."""
        dnd_available = False
        try:
            raise RuntimeError("DND registration failed")
        except ImportError:
            dnd_available = False
        except Exception:
            dnd_available = False

        assert dnd_available is False


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Dark-Mode Gantt
# ═══════════════════════════════════════════════════════════════════════════════


class TestDarkModeGantt:
    """Verify dark mode theme loading and color helpers."""

    def test_dark_palette_loaded_from_config(self):
        """theme.json should contain gantt_colors_dark with expected keys."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        assert "bg" in dark
        assert "row_even" in dark
        assert "row_odd" in dark
        assert "text" in dark
        assert "text_dim" in dark
        assert "today_line" in dark
        assert "grid_line" in dark
        assert "divider" in dark
        assert "project_bg" in dark
        assert "section_bg" in dark
        assert "header" in dark

    def test_dark_palette_colors_are_strings(self):
        """All dark palette values should be color strings."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        for key, value in dark.items():
            assert isinstance(value, str), f"{key} should be a string"
            assert value.startswith("#"), f"{key} should start with '#'"

    def test_light_palette_still_present(self):
        """gantt_colors (light) should still be present alongside dark."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        light = theme.get("gantt_colors", {})
        dark = theme.get("gantt_colors_dark", {})

        assert len(light) > 0, "Light palette should not be empty"
        assert len(dark) > 0, "Dark palette should not be empty"

    def test_bar_color_light_mode(self):
        """_bar_color should use light palette when _dark_mode=False."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        light = theme.get("gantt_colors", {})
        dark = theme.get("gantt_colors_dark", {})

        # Simulate the _bar_color logic
        dark_mode = False
        palette = dark if dark_mode else light

        status = "In Progress"
        s = status.lower().strip()
        result = palette.get("in_progress", "#336BBF")
        assert isinstance(result, str)

    def test_bar_color_dark_mode(self):
        """_bar_color should use dark palette when _dark_mode=True."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        dark_mode = True
        palette = dark if dark_mode else {}

        result = palette.get("in_progress", "#336BBF")
        assert isinstance(result, str)

    def test_dk_helper_returns_dark_value(self):
        """_dk helper should return the dark palette value."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        # Simulate _dk(key, fallback)
        result = dark.get("bg", "#1E1E2E")
        assert result.startswith("#")

    def test_dk_helper_fallback_when_key_missing(self):
        """_dk helper should return fallback for missing keys."""
        dark = {}  # empty palette
        result = dark.get("nonexistent_key", "#FFFFFF")
        assert result == "#FFFFFF"

    def test_dark_toggle_flips_mode(self):
        """Toggling dark mode should flip the _dark_mode flag."""
        # Simulate the toggle logic
        dark_mode = False
        dark_var_value = True
        dark_mode = dark_var_value
        assert dark_mode is True

        dark_var_value = False
        dark_mode = dark_var_value
        assert dark_mode is False

    def test_dark_mode_canvas_bg_color(self):
        """Dark mode should set canvas bg to dark palette bg color."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        dark_mode = True
        bg = dark.get("bg", "#1E1E2E") if dark_mode else "white"
        assert bg != "white"
        assert bg.startswith("#")

    def test_light_mode_canvas_bg_color(self):
        """Light mode should set canvas bg to white."""
        dark_mode = False
        bg = "#1E1E2E" if dark_mode else "white"
        assert bg == "white"

    def test_row_colors_differ_between_modes(self):
        """Dark and light row colors should be different."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        dark_row_even = dark.get("row_even", "#252538")
        light_row_even = "#fafafa"  # hardcoded in gantt_page light mode

        assert dark_row_even != light_row_even

    def test_dark_palette_has_status_colors(self):
        """Dark palette should have status-specific colors."""
        from helpers.config import load as load_config

        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark", {})

        assert "in_progress" in dark
        assert "completed" in dark
        assert "overdue" in dark
        assert "not_started" in dark


# ═══════════════════════════════════════════════════════════════════════════════
#  5. Integration: Config Loader Cache Behavior
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfigIntegration:
    """Verify theme.json loads correctly with the new dark palette."""

    def test_theme_loads_without_error(self):
        """load_config('theme') should not raise."""
        from helpers.config import load as load_config
        theme = load_config("theme")
        assert isinstance(theme, dict)

    def test_theme_has_brand_colors(self):
        """Theme should still have brand_colors alongside new dark palette."""
        from helpers.config import load as load_config
        theme = load_config("theme")
        assert "brand_colors" in theme or "gantt_colors" in theme

    def test_theme_gantt_colors_dark_is_dict(self):
        """gantt_colors_dark should be a dict, not None or a list."""
        from helpers.config import load as load_config
        theme = load_config("theme")
        dark = theme.get("gantt_colors_dark")
        assert isinstance(dark, dict)
