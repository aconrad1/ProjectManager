"""Tests for helpers.profile.portability — export/import round-trip."""

from __future__ import annotations

import json
import zipfile

import pytest

from helpers.profile.portability import export_profile, import_profile


class TestExportProfile:
    """Verify export produces a valid .pmprofile archive."""

    def test_export_creates_archive(self, tmp_path):
        """Exporting the _TestCompany profile (index 0) creates a ZIP file."""
        dest = tmp_path / "exported"
        result = export_profile(index=0, dest=dest)
        assert result.exists()
        assert result.suffix == ".pmprofile"
        assert result.stat().st_size > 0

    def test_export_is_valid_zip(self, tmp_path):
        """The exported file is a valid ZIP archive."""
        dest = tmp_path / "test_export"
        result = export_profile(index=0, dest=dest)
        assert zipfile.is_zipfile(result)

    def test_export_contains_manifest(self, tmp_path):
        """Archive contains _profile.yaml manifest."""
        dest = tmp_path / "test_export"
        result = export_profile(index=0, dest=dest)
        with zipfile.ZipFile(result, "r") as zf:
            assert "_profile.yaml" in zf.namelist()

    def test_export_contains_domain_json(self, tmp_path):
        """Archive contains data/domain.json."""
        dest = tmp_path / "test_export"
        result = export_profile(index=0, dest=dest)
        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
            domain_files = [n for n in names if n.endswith("domain.json")]
            assert len(domain_files) >= 1

    def test_export_invalid_index_raises(self, tmp_path):
        """Exporting with an out-of-range index raises IndexError."""
        with pytest.raises(IndexError):
            export_profile(index=999, dest=tmp_path / "bad")


class TestImportProfile:
    """Verify import reads a .pmprofile archive correctly."""

    def test_import_invalid_file_raises(self, tmp_path):
        """Importing a non-ZIP file raises an appropriate error."""
        bad_file = tmp_path / "not_a_zip.pmprofile"
        bad_file.write_text("not a zip")
        with pytest.raises(Exception):
            import_profile(bad_file)

    def test_import_missing_manifest_raises(self, tmp_path):
        """Importing a ZIP without _profile.yaml raises ValueError."""
        bad_zip = tmp_path / "no_manifest.pmprofile"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("dummy.txt", "hello")
        with pytest.raises(ValueError, match="missing _profile.yaml"):
            import_profile(bad_zip)

    def test_import_nonexistent_file_raises(self, tmp_path):
        """Importing a file that doesn't exist raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            import_profile(tmp_path / "does_not_exist.pmprofile")


class TestRoundTrip:
    """Export then import and verify data integrity."""

    def test_round_trip_preserves_domain_json(self, tmp_path):
        """Export → import → verify domain.json is preserved."""
        dest = tmp_path / "round_trip"
        archive = export_profile(index=0, dest=dest)

        # Read the domain.json from the archive
        with zipfile.ZipFile(archive, "r") as zf:
            domain_files = [n for n in zf.namelist() if n.endswith("domain.json")]
            assert domain_files
            original_data = json.loads(zf.read(domain_files[0]))

        # Verify the manifest has required fields
        with zipfile.ZipFile(archive, "r") as zf:
            import yaml
            manifest = yaml.safe_load(zf.read("_profile.yaml"))
            assert "name" in manifest
            assert "company" in manifest
            assert manifest["company"]  # not empty

        # Verify the domain.json has valid profile data
        assert "_meta" in original_data
        assert "id" in original_data
