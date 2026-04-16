"""Tests for cascade delete behaviour in DomainService.

Verifies that deleting a project or task also cleans up notes, links,
and attachments via the _cleanup_task_files helper.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from helpers.domain.deliverable import Deliverable
from helpers.domain.profile import Profile
from helpers.domain.project import Project
from helpers.domain.task import Task


# ── Fixtures ───────────────────────────────────────────────────────────


def _make_profile() -> Profile:
    """Build a small synthetic profile for testing."""
    profile = Profile(id="test-user", title="Tester")

    p1 = Project(id="P-001", title="Project Alpha", category="Ongoing")
    t1 = Task(id="T-001", title="Task A1", project_id="P-001")
    t2 = Task(id="T-002", title="Task A2", project_id="P-001")
    d1 = Deliverable(id="D-001", title="Deliverable 1", task_id="T-001")
    t1.add_deliverable(d1)
    p1.add_task(t1)
    p1.add_task(t2)

    p2 = Project(id="P-002", title="Project Beta", category="Weekly")
    t3 = Task(id="T-003", title="Task B1", project_id="P-002")
    p2.add_task(t3)

    profile.add_project(p1)
    profile.add_project(p2)
    return profile


# Shared patch targets (module where the names are looked up at call time)
_DS = "helpers.commands.domain_service"


@pytest.fixture
def service():
    """Return a DomainService with a mocked workbook and patched file ops."""
    # Import here so module-level patches are easy
    from helpers.commands.domain_service import DomainService

    profile = _make_profile()
    wb = MagicMock(name="Workbook")
    persist_cb = MagicMock(name="on_persist")

    with (
        patch(f"{_DS}._dual_save") as _mock_save,
        patch(f"{_DS}.delete_notes") as mock_notes,
        patch(f"{_DS}.delete_link") as mock_link,
        patch(f"{_DS}.delete_attachments") as mock_attach,
    ):
        svc = DomainService(profile, wb, on_persist=persist_cb)
        svc._mock_save = _mock_save
        svc._mock_notes = mock_notes
        svc._mock_link = mock_link
        svc._mock_attach = mock_attach
        svc._mock_persist_cb = persist_cb
        yield svc


# ── delete_task tests ──────────────────────────────────────────────────


class TestDeleteTask:
    """Verify single-task deletion and file cleanup."""

    def test_task_removed_from_parent(self, service):
        """Deleting a task removes it from the parent project."""
        assert service.delete_task("T-001") is True
        project = service.profile.find_project("P-001")
        assert project is not None
        remaining = [t.id for t in project.tasks]
        assert "T-001" not in remaining

    def test_sibling_tasks_unaffected(self, service):
        """Other tasks in the same project remain after a sibling is deleted."""
        service.delete_task("T-001")
        project = service.profile.find_project("P-001")
        assert any(t.id == "T-002" for t in project.tasks)

    def test_cleanup_called(self, service):
        """File cleanup functions are called with the correct task ID."""
        service.delete_task("T-001")
        service._mock_notes.assert_called_once_with("T-001")
        service._mock_link.assert_called_once_with("T-001")
        service._mock_attach.assert_called_once_with("T-001")

    def test_persist_called(self, service):
        """Persistence is triggered after deletion."""
        service.delete_task("T-001")
        service._mock_save.assert_called_once()
        service._mock_persist_cb.assert_called_once()

    def test_nonexistent_task_returns_false(self, service):
        """Deleting a non-existent task returns False."""
        assert service.delete_task("T-999") is False

    def test_deliverables_removed_with_task(self, service):
        """Deliverables underneath a deleted task are gone."""
        task = service.profile.find_task_global("T-001")
        assert len(task.deliverables) == 1  # sanity check
        service.delete_task("T-001")
        # Task (and its deliverables) should no longer be reachable
        assert service.profile.find_task_global("T-001") is None


# ── delete_project tests ───────────────────────────────────────────────


class TestDeleteProject:
    """Verify project deletion cascades to all child tasks."""

    def test_project_removed(self, service):
        """Deleting a project removes it from the profile."""
        assert service.delete_project("P-001") is True
        assert service.profile.find_project("P-001") is None

    def test_all_child_tasks_cleaned_up(self, service):
        """Every task under the project triggers file cleanup."""
        service.delete_project("P-001")
        # P-001 had T-001 and T-002
        assert service._mock_notes.call_count == 2
        assert service._mock_link.call_count == 2
        assert service._mock_attach.call_count == 2
        cleaned_ids = {c.args[0] for c in service._mock_notes.call_args_list}
        assert cleaned_ids == {"T-001", "T-002"}

    def test_other_projects_unaffected(self, service):
        """Deleting one project does not affect siblings."""
        service.delete_project("P-001")
        assert service.profile.find_project("P-002") is not None
        assert len(service.profile.find_project("P-002").tasks) == 1

    def test_nonexistent_project_returns_false(self, service):
        """Deleting a non-existent project returns False."""
        assert service.delete_project("P-999") is False

    def test_persist_called_once(self, service):
        """Persistence is triggered exactly once (not per task)."""
        service.delete_project("P-001")
        service._mock_save.assert_called_once()
