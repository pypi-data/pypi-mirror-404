"""Tests for NitroDataStore file operations."""

import json

import pytest
from nitro_datastore import NitroDataStore


class TestNitroDataStoreFileOperations:
    """Test file loading and saving."""

    def test_from_file_valid(self, tmp_path):
        """Test loading from a valid JSON file."""
        test_data = {"site": {"name": "Test Site", "version": 1}}
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(test_data))

        data = NitroDataStore.from_file(json_file)
        assert data.to_dict() == test_data

    def test_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            NitroDataStore.from_file("nonexistent.json")

    def test_from_file_invalid_json(self, tmp_path):
        """Test loading from file with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            NitroDataStore.from_file(json_file)

    def test_from_directory_single_file(self, tmp_path):
        """Test loading from directory with single file."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        test_data = {"site": {"name": "Site 1"}}
        (data_dir / "data1.json").write_text(json.dumps(test_data))

        data = NitroDataStore.from_directory(data_dir)
        assert data.to_dict() == test_data

    def test_from_directory_multiple_files_merge(self, tmp_path):
        """Test loading from directory merges files correctly."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "a.json").write_text(
            json.dumps({"site": {"name": "Site A", "url": "a.com"}})
        )
        (data_dir / "b.json").write_text(
            json.dumps({"site": {"name": "Site B"}, "extra": "data"})
        )

        data = NitroDataStore.from_directory(data_dir)
        result = data.to_dict()

        assert result["site"]["name"] == "Site B"
        assert result["site"]["url"] == "a.com"
        assert result["extra"] == "data"

    def test_from_directory_not_found(self):
        """Test loading from non-existent directory."""
        with pytest.raises(FileNotFoundError):
            NitroDataStore.from_directory("nonexistent_dir")

    def test_from_directory_skips_invalid_json(self, tmp_path):
        """Test that invalid JSON files are skipped during directory load."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "valid.json").write_text(json.dumps({"valid": "data"}))
        (data_dir / "invalid.json").write_text("{ invalid }")

        data = NitroDataStore.from_directory(data_dir)
        assert data.to_dict() == {"valid": "data"}

    def test_from_directory_custom_pattern(self, tmp_path):
        """Test loading from directory with custom pattern."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "config.json").write_text(json.dumps({"config": "data"}))
        (data_dir / "data.txt").write_text(json.dumps({"txt": "data"}))

        data = NitroDataStore.from_directory(data_dir, pattern="*.json")
        assert "config" in data.to_dict()
        assert "txt" not in data.to_dict()

    def test_save(self, tmp_path):
        """Test saving data to file."""
        data = NitroDataStore({"site": {"name": "My Site"}})
        output_file = tmp_path / "output.json"

        data.save(output_file)

        assert output_file.exists()
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data == {"site": {"name": "My Site"}}

    def test_save_creates_parent_dirs(self, tmp_path):
        """Test that save creates parent directories."""
        data = NitroDataStore({"test": "data"})
        output_file = tmp_path / "nested" / "dirs" / "output.json"

        data.save(output_file)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_save_custom_indent(self, tmp_path):
        """Test saving with custom indentation."""
        data = NitroDataStore({"site": {"name": "Test"}})
        output_file = tmp_path / "output.json"

        data.save(output_file, indent=4)

        content = output_file.read_text()
        assert '    "site"' in content
