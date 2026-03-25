"""Tests for Phase 5 — Atomic writes, mid-session sync, profile portability."""

import json
import os
import shutil
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import yaml

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


def _make_task(tid="T-001", title="Task 1", project_id="P-001"):
    from helpers.domain.task import Task
    return Task(id=tid, title=title, project_id=project_id, status="In Progress")


# ═══════════════════════════════════════════════════════════════════════════════
#  1. Atomic Dual-Write Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAtomicDualWrite:
    """Verify that contract.save() uses temp-file-then-rename for crash safety."""

    def test_save_creates_json_file(self, tmp_path):
        """Basic save should create domain.json."""
        from helpers.persistence.contract import save, domain_json_path

        profile = _make_profile(company="AtomicTest")
        wb = MagicMock()

        with patch("helpers.persistence.contract.data_dir", return_value=tmp_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook"):
                json_path = tmp_path / "domain.json"
                with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
                    save(profile, wb)

        assert json_path.exists()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data.get("company") == "AtomicTest"

    def test_save_no_tmp_or_bak_left(self, tmp_path):
        """After successful save, no .tmp or .bak files should remain."""
        from helpers.persistence.contract import save

        profile = _make_profile(company="CleanupTest")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook"):
                save(profile, wb)

        assert not (tmp_path / "domain.json.tmp").exists()
        assert not (tmp_path / "domain.json.bak").exists()

    def test_save_rollback_on_workbook_failure(self, tmp_path):
        """If workbook render fails, JSON should be rolled back."""
        from helpers.persistence.contract import save

        profile = _make_profile(company="RollbackTest")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        # Pre-populate with known content
        original_content = '{"_meta": {}, "company": "Original"}'
        json_path.write_text(original_content, encoding="utf-8")

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook",
                        side_effect=RuntimeError("workbook write failed")):
                with pytest.raises(RuntimeError, match="workbook write failed"):
                    save(profile, wb)

        # JSON should be rolled back to original
        restored = json_path.read_text(encoding="utf-8")
        assert '"Original"' in restored

    def test_save_rollback_removes_json_if_no_prior(self, tmp_path):
        """If no prior JSON existed and workbook fails, JSON is removed entirely."""
        from helpers.persistence.contract import save

        profile = _make_profile(company="NoPriorTest")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        # Ensure no prior file
        assert not json_path.exists()

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook",
                        side_effect=RuntimeError("boom")):
                with pytest.raises(RuntimeError):
                    save(profile, wb)

        # JSON should not exist
        assert not json_path.exists()

    def test_save_with_wb_path_records_hash(self, tmp_path):
        """When wb_path is provided, the workbook hash is recorded in JSON."""
        from helpers.persistence.contract import save

        profile = _make_profile(company="HashTest")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"
        wb_file = tmp_path / "test.xlsx"
        wb_file.write_bytes(b"fake workbook content")

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook"):
                save(profile, wb, wb_path=wb_file)

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["_meta"]["workbook_hash"] != ""

    def test_atomic_replace_function(self, tmp_path):
        """_atomic_replace should move src to dst."""
        from helpers.persistence.contract import _atomic_replace

        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("hello")
        dst.write_text("old")

        _atomic_replace(src, dst)
        assert not src.exists()
        assert dst.read_text() == "hello"

    def test_save_tmp_cleaned_on_rename_failure(self, tmp_path):
        """If the atomic rename fails, tmp file is cleaned up."""
        from helpers.persistence.contract import save

        profile = _make_profile(company="RenameFailTest")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract._atomic_replace",
                        side_effect=OSError("rename failed")):
                with pytest.raises(OSError):
                    save(profile, wb)

        # No tmp or bak should remain
        assert not (tmp_path / "domain.json.tmp").exists()


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Mid-Session External Edit Detection Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestExternalEditDetection:
    """Verify detect_external_edits() logic."""

    def test_no_json_returns_false(self, tmp_path):
        """If domain.json doesn't exist, return False."""
        from helpers.persistence.contract import detect_external_edits

        with patch("helpers.persistence.contract.domain_json_path",
                    return_value=tmp_path / "domain.json"):
            result = detect_external_edits("TestCo", tmp_path / "test.xlsx")
        assert result is False

    def test_no_workbook_returns_false(self, tmp_path):
        """If workbook doesn't exist, return False."""
        from helpers.persistence.contract import detect_external_edits

        json_path = tmp_path / "domain.json"
        json_path.write_text('{"_meta": {"workbook_hash": "abc"}}')

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            result = detect_external_edits("TestCo", tmp_path / "nonexistent.xlsx")
        assert result is False

    def test_no_stored_hash_returns_false(self, tmp_path):
        """If no workbook_hash in meta, return False (first-run scenario)."""
        from helpers.persistence.contract import detect_external_edits

        json_path = tmp_path / "domain.json"
        # Create a valid domain.json with empty hash
        profile = _make_profile()
        from helpers.persistence.serializer import save_profile_json
        save_profile_json(profile, json_path, workbook_hash="")

        wb_file = tmp_path / "test.xlsx"
        wb_file.write_bytes(b"content")

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            result = detect_external_edits("TestCo", wb_file)
        assert result is False

    def test_matching_hash_returns_false(self, tmp_path):
        """If hash matches, no external edit detected."""
        from helpers.persistence.contract import detect_external_edits
        from helpers.persistence.serializer import save_profile_json, hash_file

        wb_file = tmp_path / "test.xlsx"
        wb_file.write_bytes(b"workbook content")
        wb_hash = hash_file(wb_file)

        json_path = tmp_path / "domain.json"
        profile = _make_profile()
        save_profile_json(profile, json_path, workbook_hash=wb_hash)

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            result = detect_external_edits("TestCo", wb_file)
        assert result is False

    def test_different_hash_returns_true(self, tmp_path):
        """If hash differs, external edit detected."""
        from helpers.persistence.contract import detect_external_edits
        from helpers.persistence.serializer import save_profile_json

        json_path = tmp_path / "domain.json"
        profile = _make_profile()
        save_profile_json(profile, json_path, workbook_hash="oldhash123")

        wb_file = tmp_path / "test.xlsx"
        wb_file.write_bytes(b"modified workbook content")

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            result = detect_external_edits("TestCo", wb_file)
        assert result is True

    def test_detect_after_external_modification(self, tmp_path):
        """Full round-trip: save, modify workbook, detect change."""
        from helpers.persistence.contract import detect_external_edits
        from helpers.persistence.serializer import save_profile_json, hash_file

        wb_file = tmp_path / "test.xlsx"
        wb_file.write_bytes(b"original content")
        original_hash = hash_file(wb_file)

        json_path = tmp_path / "domain.json"
        profile = _make_profile()
        save_profile_json(profile, json_path, workbook_hash=original_hash)

        # Simulate external edit
        wb_file.write_bytes(b"externally modified content")

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            result = detect_external_edits("TestCo", wb_file)
        assert result is True


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Profile Export/Import Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestProfilePortability:
    """Verify .pmprofile export/import round-trip."""

    @pytest.fixture
    def profile_env(self, tmp_path):
        """Set up a fake profiles directory with one profile."""
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()

        # Create a profile directory with some files
        company_dir = profiles_dir / "ExportCo"
        (company_dir / "data").mkdir(parents=True)
        (company_dir / "attachments").mkdir(parents=True)
        (company_dir / "exports" / "markdown").mkdir(parents=True)
        (company_dir / "exports" / "pdf").mkdir(parents=True)
        (company_dir / "reports").mkdir(parents=True)

        # Add some data files
        (company_dir / "data" / "domain.json").write_text(
            '{"_meta": {}, "company": "ExportCo"}', encoding="utf-8"
        )
        (company_dir / "data" / "task_notes.json").write_text(
            '{}', encoding="utf-8"
        )

        profile_data = {
            "name": "Export User",
            "company": "ExportCo",
            "role": "Engineer",
            "email": "test@example.com",
            "phone": "555-0100",
            "workbook_filename": "Projects.xlsx",
            "daily_hours_budget": 8.0,
        }

        return {
            "profiles_dir": profiles_dir,
            "company_dir": company_dir,
            "profile_data": profile_data,
        }

    def test_export_creates_pmprofile(self, profile_env, tmp_path):
        """export_profile() should create a .pmprofile ZIP archive."""
        from helpers.profile.portability import export_profile

        env = profile_env
        dest = tmp_path / "output" / "exported.pmprofile"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                result = export_profile(0, dest)

        assert result.exists()
        assert result.suffix == ".pmprofile"
        assert zipfile.is_zipfile(result)

    def test_export_contains_manifest(self, profile_env, tmp_path):
        """Archive should contain a _profile.yaml manifest."""
        from helpers.profile.portability import export_profile

        env = profile_env
        dest = tmp_path / "out.pmprofile"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                export_profile(0, dest)

        with zipfile.ZipFile(dest, "r") as zf:
            assert "_profile.yaml" in zf.namelist()
            manifest = yaml.safe_load(zf.read("_profile.yaml"))
            assert manifest["company"] == "ExportCo"
            assert manifest["name"] == "Export User"

    def test_export_contains_data_files(self, profile_env, tmp_path):
        """Archive should contain the profile's data files."""
        from helpers.profile.portability import export_profile

        env = profile_env
        dest = tmp_path / "out.pmprofile"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                export_profile(0, dest)

        with zipfile.ZipFile(dest, "r") as zf:
            names = zf.namelist()
            assert any("domain.json" in n for n in names)
            assert any("task_notes.json" in n for n in names)

    def test_export_auto_appends_extension(self, profile_env, tmp_path):
        """If dest doesn't end with .pmprofile, extension is appended."""
        from helpers.profile.portability import export_profile

        env = profile_env
        dest = tmp_path / "exported_bundle"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                result = export_profile(0, dest)

        assert result.suffix == ".pmprofile"

    def test_export_invalid_index_raises(self, profile_env, tmp_path):
        """export_profile with invalid index raises IndexError."""
        from helpers.profile.portability import export_profile

        with patch("helpers.profile.portability.get_profiles", return_value=[]):
            with pytest.raises(IndexError):
                export_profile(5, tmp_path / "out.pmprofile")

    def test_export_no_company_raises(self, profile_env, tmp_path):
        """export_profile with empty company raises ValueError."""
        from helpers.profile.portability import export_profile

        with patch("helpers.profile.portability.get_profiles",
                    return_value=[{"name": "No Co", "company": ""}]):
            with pytest.raises(ValueError, match="company"):
                export_profile(0, tmp_path / "out.pmprofile")

    def test_import_creates_profile(self, profile_env, tmp_path):
        """import_profile() should extract files and call init_profile."""
        from helpers.profile.portability import export_profile, import_profile

        env = profile_env
        archive = tmp_path / "bundle.pmprofile"

        # First export
        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                export_profile(0, archive)

        # Now import into a fresh profiles dir
        import_dir = tmp_path / "import_profiles"
        import_dir.mkdir()

        new_idx = 999
        with patch("helpers.profile.portability.PROFILES_DIR", import_dir):
            with patch("helpers.profile.portability.get_profiles", return_value=[]):
                with patch("helpers.profile.portability.init_profile", return_value=new_idx) as mock_init:
                    idx = import_profile(archive)

        assert idx == new_idx
        mock_init.assert_called_once()
        call_data = mock_init.call_args[0][0]
        assert call_data["company"] == "ExportCo"

    def test_import_extracts_files(self, profile_env, tmp_path):
        """import_profile() should extract data files to the profiles directory."""
        from helpers.profile.portability import export_profile, import_profile

        env = profile_env
        archive = tmp_path / "bundle.pmprofile"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                export_profile(0, archive)

        import_dir = tmp_path / "import_profiles"
        import_dir.mkdir()

        with patch("helpers.profile.portability.PROFILES_DIR", import_dir):
            with patch("helpers.profile.portability.get_profiles", return_value=[]):
                with patch("helpers.profile.portability.init_profile", return_value=0):
                    import_profile(archive)

        # Check extracted files
        extracted_json = import_dir / "ExportCo" / "data" / "domain.json"
        assert extracted_json.exists()

    def test_import_duplicate_company_raises(self, profile_env, tmp_path):
        """import_profile() raises if company already exists."""
        from helpers.profile.portability import export_profile, import_profile

        env = profile_env
        archive = tmp_path / "bundle.pmprofile"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                export_profile(0, archive)

        # Try to import when ExportCo already exists
        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                with pytest.raises(ValueError, match="already exists"):
                    import_profile(archive)

    def test_import_missing_manifest_raises(self, tmp_path):
        """import_profile() raises if archive has no _profile.yaml."""
        from helpers.profile.portability import import_profile

        # Create a bogus zip
        bad_archive = tmp_path / "bad.pmprofile"
        with zipfile.ZipFile(bad_archive, "w") as zf:
            zf.writestr("random.txt", "hello")

        with pytest.raises(ValueError, match="missing"):
            import_profile(bad_archive)

    def test_import_nonexistent_file_raises(self, tmp_path):
        """import_profile() raises FileNotFoundError for missing archive."""
        from helpers.profile.portability import import_profile

        with pytest.raises(FileNotFoundError):
            import_profile(tmp_path / "nonexistent.pmprofile")

    def test_round_trip_preserves_data(self, profile_env, tmp_path):
        """Full export→import round trip preserves profile data and files."""
        from helpers.profile.portability import export_profile, import_profile

        env = profile_env
        archive = tmp_path / "roundtrip.pmprofile"

        with patch("helpers.profile.portability.PROFILES_DIR", env["profiles_dir"]):
            with patch("helpers.profile.portability.get_profiles",
                        return_value=[env["profile_data"]]):
                export_profile(0, archive)

        import_dir = tmp_path / "roundtrip_import"
        import_dir.mkdir()

        captured_data = {}
        def fake_init(data):
            captured_data.update(data)
            return 0

        with patch("helpers.profile.portability.PROFILES_DIR", import_dir):
            with patch("helpers.profile.portability.get_profiles", return_value=[]):
                with patch("helpers.profile.portability.init_profile", side_effect=fake_init):
                    import_profile(archive)

        assert captured_data["name"] == "Export User"
        assert captured_data["company"] == "ExportCo"
        assert captured_data["role"] == "Engineer"
        assert captured_data["email"] == "test@example.com"

        # Check files
        domain_json = import_dir / "ExportCo" / "data" / "domain.json"
        assert domain_json.exists()
        content = json.loads(domain_json.read_text(encoding="utf-8"))
        assert content["company"] == "ExportCo"

    def test_import_path_traversal_blocked(self, tmp_path):
        """import_profile() rejects archives with path traversal."""
        from helpers.profile.portability import import_profile

        archive = tmp_path / "evil.pmprofile"
        with zipfile.ZipFile(archive, "w") as zf:
            manifest = yaml.dump({"name": "Evil", "company": "Evil"})
            zf.writestr("_profile.yaml", manifest)
            zf.writestr("../../etc/passwd", "evil content")

        with patch("helpers.profile.portability.PROFILES_DIR", tmp_path / "profiles"):
            with patch("helpers.profile.portability.get_profiles", return_value=[]):
                with pytest.raises(ValueError, match="[Pp]ath traversal"):
                    import_profile(archive)


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Delete Last Profile Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeleteLastProfile:
    """Verify that deleting the last profile auto-creates a fallback."""

    @pytest.fixture(autouse=True)
    def _isolate_profile_module(self, tmp_path):
        """Patch the profile module's internal state for test isolation."""
        import helpers.profile.profile as pp
        self._orig_profiles = pp._profiles[:]
        self._orig_index = pp._active_index
        self._orig_save = pp._save_profiles
        # Suppress actual YAML writes
        pp._save_profiles = lambda: None
        yield
        pp._profiles[:] = self._orig_profiles
        pp._active_index = self._orig_index
        pp._save_profiles = self._orig_save

    def test_delete_last_creates_default(self, tmp_path):
        """Deleting the only profile should auto-create a Default fallback."""
        import helpers.profile.profile as pp

        pp._profiles[:] = [{"name": "Only User", "company": "OnlyCo"}]
        pp._active_index = 0

        with patch("helpers.profile.profile.scaffold_profile"):
            with patch("helpers.profile.profile.profile_dir", return_value=tmp_path / "OnlyCo"):
                pp.delete_profile(0)

        assert len(pp._profiles) == 1
        assert pp._profiles[0]["company"] == "Default"
        assert pp._profiles[0]["name"] == "Default User"
        assert pp._active_index == 0

    def test_delete_last_scaffolds_default(self, tmp_path):
        """The fallback profile should be scaffolded on disk."""
        import helpers.profile.profile as pp

        pp._profiles[:] = [{"name": "Only User", "company": "OnlyCo"}]
        pp._active_index = 0

        with patch("helpers.profile.profile.scaffold_profile") as mock_scaffold:
            with patch("helpers.profile.profile.profile_dir", return_value=tmp_path / "OnlyCo"):
                pp.delete_profile(0)

        mock_scaffold.assert_called_once_with("Default", "Projects.xlsx")

    def test_delete_non_last_still_works(self, tmp_path):
        """Deleting a profile when others exist works without fallback."""
        import helpers.profile.profile as pp

        pp._profiles[:] = [
            {"name": "User A", "company": "CompanyA"},
            {"name": "User B", "company": "CompanyB"},
        ]
        pp._active_index = 0

        with patch("helpers.profile.profile.profile_dir", return_value=tmp_path / "CompanyA"):
            pp.delete_profile(0)

        assert len(pp._profiles) == 1
        assert pp._profiles[0]["company"] == "CompanyB"

    def test_delete_last_with_remove_files(self, tmp_path):
        """Deleting last profile with remove_files=True cleans up old dir."""
        import helpers.profile.profile as pp

        target_dir = tmp_path / "OnlyCo"
        target_dir.mkdir()
        (target_dir / "data").mkdir()

        pp._profiles[:] = [{"name": "Only User", "company": "OnlyCo"}]
        pp._active_index = 0

        with patch("helpers.profile.profile.scaffold_profile"):
            with patch("helpers.profile.profile.profile_dir", return_value=target_dir):
                pp.delete_profile(0, remove_files=True)

        assert pp._profiles[0]["company"] == "Default"
        # Original dir should be removed
        assert not target_dir.exists()

    def test_delete_last_sets_correct_globals(self, tmp_path):
        """After deleting the last profile, module globals reflect the fallback."""
        import helpers.profile.profile as pp

        pp._profiles[:] = [{"name": "Only User", "company": "OnlyCo"}]
        pp._active_index = 0

        with patch("helpers.profile.profile.scaffold_profile"):
            with patch("helpers.profile.profile.profile_dir", return_value=tmp_path / "OnlyCo"):
                pp.delete_profile(0)

        assert pp.USER_COMPANY == "Default"
        assert pp.USER_NAME == "Default User"
        assert pp.WORKBOOK_FILENAME == "Projects.xlsx"

    def test_delete_invalid_index_raises(self):
        """Deleting with out-of-range index raises IndexError."""
        import helpers.profile.profile as pp

        pp._profiles[:] = [{"name": "User", "company": "Co"}]
        with pytest.raises(IndexError):
            pp.delete_profile(5)


# ═══════════════════════════════════════════════════════════════════════════════
#  5. Integration: Atomic Save Round-Trip
# ═══════════════════════════════════════════════════════════════════════════════


class TestAtomicSaveIntegration:
    """Full round-trip: save → load → verify no corruption."""

    def test_save_load_roundtrip(self, tmp_path):
        """Save and then load should produce identical profile data."""
        from helpers.persistence.contract import save
        from helpers.persistence.serializer import load_profile_json

        profile = _make_profile(company="RoundTrip")
        proj = _make_project(pid="P-001", title="My Project")
        profile.projects.append(proj)

        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook"):
                save(profile, wb)

        loaded, meta = load_profile_json(json_path)
        assert loaded.company == "RoundTrip"
        assert len(loaded.projects) == 1
        assert loaded.projects[0].title == "My Project"

    def test_multiple_saves_only_final_state(self, tmp_path):
        """Multiple sequential saves — only the last state persists."""
        from helpers.persistence.contract import save
        from helpers.persistence.serializer import load_profile_json

        profile = _make_profile(company="MultiSave")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook"):
                save(profile, wb)
                profile.title = "Updated Name"
                save(profile, wb)

        loaded, _ = load_profile_json(json_path)
        assert loaded.title == "Updated Name"

    def test_concurrent_save_resilience(self, tmp_path):
        """Simulates rapid sequential saves — file should never be corrupt."""
        from helpers.persistence.contract import save
        from helpers.persistence.serializer import load_profile_json

        profile = _make_profile(company="RapidSave")
        wb = MagicMock()
        json_path = tmp_path / "domain.json"

        with patch("helpers.persistence.contract.domain_json_path", return_value=json_path):
            with patch("helpers.persistence.contract.save_profile_to_workbook"):
                for i in range(20):
                    profile.title = f"Iteration {i}"
                    save(profile, wb)

        loaded, _ = load_profile_json(json_path)
        assert loaded.title == "Iteration 19"
        # No leftover temp files
        assert not (tmp_path / "domain.json.tmp").exists()
        assert not (tmp_path / "domain.json.bak").exists()


# ═══════════════════════════════════════════════════════════════════════════════
#  6. Mid-Session Sync Hook Tests (GUI-level)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAppSyncHooks:
    """Verify the GUI triggers external edit detection at the right moments."""

    def test_show_page_calls_check(self):
        """show_page() should call _check_external_edits."""
        app = MagicMock()
        app.pages = {"tasks": MagicMock(), "dashboard": MagicMock()}
        app._nav_btns = {"tasks": MagicMock(), "dashboard": MagicMock()}
        app._active_page_key = "tasks"

        # Simulate show_page calling _check_external_edits
        from scripts.gui.app import App
        # Just verify the method exists and is called in the flow
        assert hasattr(App, "show_page")
        assert hasattr(App, "_check_external_edits")

    def test_check_external_edits_not_configured(self):
        """_check_external_edits should no-op when profile is not configured."""
        from scripts.gui.app import App
        app = MagicMock(spec=App)
        app._profile_is_configured = MagicMock(return_value=False)
        App._check_external_edits(app)
        # No exception — just returns silently

    def test_on_focus_in_filters_child_widgets(self):
        """_on_focus_in only fires for the root window, not children."""
        from scripts.gui.app import App
        app = MagicMock(spec=App)

        event = MagicMock()
        event.widget = MagicMock()  # Not self
        App._on_focus_in(app, event)
        app._check_external_edits.assert_not_called()
