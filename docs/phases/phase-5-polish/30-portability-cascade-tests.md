# Task 30: Add Tests for Portability and Cascade Delete

**Audit ID**: N-12  
**Effort**: Medium  
**Phase**: 5 — Polish

---

## Objective

Add integration tests for two untested modules: `helpers/profile/portability.py` (export/import round-trip) and cascade delete end-to-end (project delete → task cleanup → file cleanup).

---

## Audit Reference

> **N-12: No Tests for portability.py, pdf.py, shell.py, utilities.py**
>
> These modules contain meaningful logic but have zero test coverage.
>
> **Cascade delete end-to-end**: No test covers project delete → task cleanup → file cleanup.

---

## Affected Files

| File | Action |
|------|--------|
| `tests/test_portability.py` | **CREATE** — portability round-trip tests |
| `tests/test_cascade_delete.py` | **CREATE** — cascade delete integration tests |

---

## Test Design

### 1. `tests/test_portability.py` — Export/Import Round-Trip

The portability module provides `export_profile(index, dest)` and `import_profile(archive_path)`. Testing requires:

- A temporary directory for the export archive
- A mock (or real _TestCompany) profile to export
- Verification that the imported profile matches the original

```python
"""Tests for helpers.profile.portability — export/import round-trip."""

import pytest
import tempfile
from pathlib import Path

from helpers.profile.portability import export_profile, import_profile


class TestExportImport:
    """Round-trip test: export a profile → import it → verify contents match."""

    def test_export_creates_archive(self, tmp_path):
        """Exporting a profile creates a ZIP file at the destination."""
        # Use the _TestCompany profile (index depends on user_profile.yaml)
        dest = tmp_path / "exported.zip"
        export_profile(index=..., dest=dest)
        assert dest.exists()
        assert dest.stat().st_size > 0

    def test_round_trip_preserves_data(self, tmp_path):
        """Export then import preserves domain.json, notes, links."""
        dest = tmp_path / "exported.zip"
        export_profile(index=..., dest=dest)
        
        # Import into a fresh location
        import_profile(dest)
        
        # Verify the imported files exist and have valid content
        # (Check domain.json, task_notes.json, task_links.json)

    def test_import_invalid_archive_raises(self, tmp_path):
        """Importing a non-ZIP file raises an appropriate error."""
        bad_file = tmp_path / "not_a_zip.txt"
        bad_file.write_text("not a zip")
        with pytest.raises((ValueError, OSError)):
            import_profile(bad_file)
```

### 2. `tests/test_cascade_delete.py` — Cascade Delete Integration

Test the full cascade: delete a project → verify all child tasks are removed → verify notes/links/attachments are cleaned up.

```python
"""Tests for cascade delete: project → tasks → files."""

import pytest
from datetime import date
from unittest.mock import patch

from helpers.domain.profile import Profile
from helpers.domain.project import Project
from helpers.domain.task import Task
from helpers.domain.deliverable import Deliverable
from helpers.commands.domain_service import DomainService


def _make_test_hierarchy():
    """Build a Profile with 1 project, 2 tasks, 2 deliverables."""
    profile = Profile(name="Test", company="TestCo")
    project = Project(id="P-001", title="Test Project", category="Ongoing")
    task1 = Task(id="T-001", title="Task One", project_id="P-001")
    task2 = Task(id="T-002", title="Task Two", project_id="P-001")
    deliv = Deliverable(id="D-001", title="Deliverable One", task_id="T-001")
    task1.deliverables.append(deliv)
    project.tasks.extend([task1, task2])
    profile.projects.append(project)
    return profile


class TestCascadeDeleteProject:
    """Deleting a project removes all child tasks and their files."""

    def test_delete_project_removes_tasks(self):
        profile = _make_test_hierarchy()
        assert len(profile.all_tasks) == 2
        
        service = DomainService(profile, wb=None, on_persist=lambda: None)
        service.delete_project("P-001")
        
        assert len(profile.projects) == 0
        assert len(profile.all_tasks) == 0

    @patch("helpers.commands.domain_service.delete_notes")
    @patch("helpers.commands.domain_service.delete_link")
    @patch("helpers.commands.domain_service.delete_attachments")
    def test_delete_project_cleans_up_files(
        self, mock_attach, mock_link, mock_notes
    ):
        profile = _make_test_hierarchy()
        service = DomainService(profile, wb=None, on_persist=lambda: None)
        service.delete_project("P-001")
        
        # Verify cleanup was called for each task
        assert mock_notes.call_count == 2  # T-001, T-002
        assert mock_link.call_count == 2
        assert mock_attach.call_count == 2


class TestCascadeDeleteTask:
    """Deleting a task removes deliverables and cleans up files."""

    def test_delete_task_removes_deliverables(self):
        profile = _make_test_hierarchy()
        assert len(profile.all_tasks) == 2
        
        service = DomainService(profile, wb=None, on_persist=lambda: None)
        service.delete_task("T-001")
        
        assert len(profile.all_tasks) == 1
        remaining = profile.find_task_global("T-002")
        assert remaining is not None

    @patch("helpers.commands.domain_service.delete_notes")
    @patch("helpers.commands.domain_service.delete_link")
    @patch("helpers.commands.domain_service.delete_attachments")
    def test_delete_task_calls_cleanup(
        self, mock_attach, mock_link, mock_notes
    ):
        profile = _make_test_hierarchy()
        service = DomainService(profile, wb=None, on_persist=lambda: None)
        service.delete_task("T-001")
        
        mock_notes.assert_called_once_with("T-001")
        mock_link.assert_called_once_with("T-001")
        mock_attach.assert_called_once_with("T-001")
```

---

## Acceptance Criteria

1. `tests/test_portability.py` exists with ≥3 test cases covering export, import, and error handling
2. `tests/test_cascade_delete.py` exists with ≥4 test cases covering project delete, task delete, deliverable removal, and file cleanup
3. All new tests pass: `pytest tests/test_portability.py tests/test_cascade_delete.py`
4. Tests use `unittest.mock.patch` for file cleanup verification (no real file I/O in cascade tests)
5. Portability tests use temporary directories (`tmp_path` fixture)
6. No existing tests are broken

---

## Constraints

- Portability tests need a real or mock profile to export — use `_TestCompany` data or create synthetic profiles
- Cascade delete tests should NOT require a workbook (`wb=None` is acceptable for DomainService)
- The `on_persist` callback can be a no-op lambda in tests
- Mock `delete_notes`, `delete_link`, `delete_attachments` at the module level where they're imported in `domain_service.py`
- Do NOT test `pdf.py` in this task (requires Chrome) — it's noted as low priority in the audit
- Do NOT test `shell.py` or `utilities.py` — they're interactive/platform-specific
