"""Tests for security features and validation."""

import pytest
from nitro_datastore import NitroDataStore


class TestPathTraversalProtection:
    """Tests for path traversal protection with base_dir parameter."""

    def test_from_file_without_base_dir(self, tmp_path):
        """Test from_file works without base_dir (backward compatible)."""
        test_file = tmp_path / "config.json"
        test_file.write_text('{"test": true}')

        data = NitroDataStore.from_file(test_file)
        assert data.test is True

    def test_from_file_with_base_dir_valid(self, tmp_path):
        """Test from_file accepts valid path within base_dir."""
        test_file = tmp_path / "config.json"
        test_file.write_text('{"secure": true}')

        data = NitroDataStore.from_file(test_file, base_dir=tmp_path)
        assert data.secure is True

    def test_from_file_with_base_dir_subdir(self, tmp_path):
        """Test from_file accepts subdirectory within base_dir."""
        subdir = tmp_path / "configs"
        subdir.mkdir()
        test_file = subdir / "app.json"
        test_file.write_text('{"app": "test"}')

        data = NitroDataStore.from_file(test_file, base_dir=tmp_path)
        assert data.app == "test"

    def test_from_file_blocks_path_traversal(self, tmp_path):
        """Test from_file blocks path traversal outside base_dir."""
        test_file = tmp_path / "config.json"
        test_file.write_text('{"test": true}')

        evil_path = tmp_path / "subdir" / ".." / ".." / "evil.json"

        with pytest.raises(ValueError, match="Path traversal detected"):
            NitroDataStore.from_file(evil_path, base_dir=tmp_path / "subdir")

    def test_from_file_blocks_absolute_path_outside(self, tmp_path):
        """Test from_file blocks absolute paths outside base_dir."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"outside": true}')
            outside_file = f.name

        try:
            with pytest.raises(ValueError, match="Path traversal detected"):
                NitroDataStore.from_file(outside_file, base_dir=tmp_path)
        finally:
            import os

            os.unlink(outside_file)

    def test_from_directory_without_base_dir(self, tmp_path):
        """Test from_directory works without base_dir (backward compatible)."""
        (tmp_path / "a.json").write_text('{"a": 1}')
        (tmp_path / "b.json").write_text('{"b": 2}')

        data = NitroDataStore.from_directory(tmp_path)
        assert data.a == 1
        assert data.b == 2

    def test_from_directory_with_base_dir_valid(self, tmp_path):
        """Test from_directory accepts valid directory within base_dir."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "config.json").write_text('{"valid": true}')

        data = NitroDataStore.from_directory(data_dir, base_dir=tmp_path)
        assert data.valid is True

    def test_from_directory_blocks_path_traversal(self, tmp_path):
        """Test from_directory blocks path traversal outside base_dir."""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        evil_path = safe_dir / ".." / ".."

        with pytest.raises(ValueError, match="Path traversal detected"):
            NitroDataStore.from_directory(evil_path, base_dir=safe_dir)

    def test_from_directory_with_pattern_and_base_dir(self, tmp_path):
        """Test from_directory works with custom pattern and base_dir."""
        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        (config_dir / "app.config.json").write_text('{"app": "test"}')
        (config_dir / "db.config.json").write_text('{"db": "postgres"}')
        (config_dir / "other.json").write_text('{"other": "skip"}')

        data = NitroDataStore.from_directory(
            config_dir, pattern="*.config.json", base_dir=tmp_path
        )
        assert data.app == "test"
        assert data.db == "postgres"
        assert not hasattr(data, "other")


class TestFileSizeLimits:
    """Tests for file size limit protection with max_size parameter."""

    def test_from_file_without_max_size(self, tmp_path):
        """Test from_file works without max_size (backward compatible)."""
        test_file = tmp_path / "large.json"
        test_file.write_text('{"data": "' + "x" * 10000 + '"}')

        data = NitroDataStore.from_file(test_file)
        assert len(data.data) == 10000

    def test_from_file_within_size_limit(self, tmp_path):
        """Test from_file accepts file within size limit."""
        test_file = tmp_path / "small.json"
        content = '{"small": true}'
        test_file.write_text(content)

        max_size = len(content.encode("utf-8")) + 100
        data = NitroDataStore.from_file(test_file, max_size=max_size)
        assert data.small is True

    def test_from_file_exact_size_limit(self, tmp_path):
        """Test from_file accepts file at exact size limit."""
        test_file = tmp_path / "exact.json"
        content = '{"exact": true}'
        test_file.write_text(content)

        max_size = len(content.encode("utf-8"))
        data = NitroDataStore.from_file(test_file, max_size=max_size)
        assert data.exact is True

    def test_from_file_exceeds_size_limit(self, tmp_path):
        """Test from_file rejects file exceeding size limit."""
        test_file = tmp_path / "large.json"
        test_file.write_text('{"data": "' + "x" * 10000 + '"}')

        with pytest.raises(ValueError, match="File size.*exceeds maximum"):
            NitroDataStore.from_file(test_file, max_size=100)

    def test_from_file_size_limit_error_message(self, tmp_path):
        """Test from_file provides clear error message with MB sizes."""
        test_file = tmp_path / "big.json"
        large_data = '{"data": "' + "x" * 1000000 + '"}'
        test_file.write_text(large_data)

        with pytest.raises(ValueError) as exc_info:
            NitroDataStore.from_file(test_file, max_size=1024)

        error_msg = str(exc_info.value)
        assert "MB" in error_msg
        assert "exceeds maximum" in error_msg

    def test_from_directory_without_max_size(self, tmp_path):
        """Test from_directory works without max_size (backward compatible)."""
        (tmp_path / "a.json").write_text('{"a": "' + "x" * 5000 + '"}')
        (tmp_path / "b.json").write_text('{"b": "' + "y" * 5000 + '"}')

        data = NitroDataStore.from_directory(tmp_path)
        assert len(data.a) == 5000
        assert len(data.b) == 5000

    def test_from_directory_all_files_within_limit(self, tmp_path):
        """Test from_directory accepts all files within size limit."""
        (tmp_path / "a.json").write_text('{"a": 1}')
        (tmp_path / "b.json").write_text('{"b": 2}')

        data = NitroDataStore.from_directory(tmp_path, max_size=1000)
        assert data.a == 1
        assert data.b == 2

    def test_from_directory_rejects_oversized_file(self, tmp_path):
        """Test from_directory rejects if any file exceeds size limit."""
        (tmp_path / "small.json").write_text('{"small": 1}')
        (tmp_path / "large.json").write_text('{"large": "' + "x" * 10000 + '"}')

        with pytest.raises(ValueError, match="File size.*exceeds maximum"):
            NitroDataStore.from_directory(tmp_path, max_size=100)

    def test_from_directory_size_limit_includes_filename(self, tmp_path):
        """Test from_directory error message includes the problematic file."""
        (tmp_path / "ok.json").write_text('{"ok": 1}')
        large_file = tmp_path / "problematic.json"
        large_file.write_text('{"data": "' + "x" * 10000 + '"}')

        with pytest.raises(ValueError) as exc_info:
            NitroDataStore.from_directory(tmp_path, max_size=100)

        error_msg = str(exc_info.value)
        assert "problematic.json" in error_msg

    def test_combined_base_dir_and_max_size(self, tmp_path):
        """Test from_file works with both base_dir and max_size."""
        test_file = tmp_path / "secure.json"
        test_file.write_text('{"secure": true}')

        data = NitroDataStore.from_file(test_file, base_dir=tmp_path, max_size=1000)
        assert data.secure is True

    def test_combined_validations_both_fail(self, tmp_path):
        """Test appropriate error when file fails both validations."""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        outside_file = tmp_path / "outside.json"
        outside_file.write_text('{"big": "' + "x" * 10000 + '"}')

        with pytest.raises(ValueError, match="Path traversal detected"):
            NitroDataStore.from_file(outside_file, base_dir=safe_dir, max_size=100)


class TestPathValidation:
    """Tests for path string validation in path-based methods."""

    def test_get_with_empty_string(self):
        """Test get() rejects empty path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.get("")

    def test_get_with_whitespace_only(self):
        """Test get() rejects whitespace-only path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.get("   ")

    def test_get_with_single_dot(self):
        """Test get() rejects single dot path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.get(".")

    def test_get_with_double_dots(self):
        """Test get() rejects double dot path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.get("..")

    def test_get_with_triple_dots(self):
        """Test get() rejects triple dot path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.get("...")

    def test_get_with_leading_dot(self):
        """Test get() rejects path with leading dot."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.get(".foo")

    def test_get_with_trailing_dot(self):
        """Test get() rejects path with trailing dot."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.get("foo.")

    def test_get_with_consecutive_dots(self):
        """Test get() rejects path with consecutive dots."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.get("foo..bar")

    def test_set_with_empty_string(self):
        """Test set() rejects empty path."""
        data = NitroDataStore()
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.set("", "value")

    def test_set_with_whitespace_only(self):
        """Test set() rejects whitespace-only path."""
        data = NitroDataStore()
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.set("   ", "value")

    def test_set_with_leading_dot(self):
        """Test set() rejects path with leading dot."""
        data = NitroDataStore()
        with pytest.raises(ValueError, match="contains empty segments"):
            data.set(".foo", "value")

    def test_set_with_trailing_dot(self):
        """Test set() rejects path with trailing dot."""
        data = NitroDataStore()
        with pytest.raises(ValueError, match="contains empty segments"):
            data.set("foo.", "value")

    def test_set_with_consecutive_dots(self):
        """Test set() rejects path with consecutive dots."""
        data = NitroDataStore()
        with pytest.raises(ValueError, match="contains empty segments"):
            data.set("foo..bar", "value")

    def test_delete_with_empty_string(self):
        """Test delete() rejects empty path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.delete("")

    def test_delete_with_whitespace_only(self):
        """Test delete() rejects whitespace-only path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.delete("   ")

    def test_delete_with_leading_dot(self):
        """Test delete() rejects path with leading dot."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.delete(".a")

    def test_delete_with_trailing_dot(self):
        """Test delete() rejects path with trailing dot."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.delete("a.")

    def test_delete_with_consecutive_dots(self):
        """Test delete() rejects path with consecutive dots."""
        data = NitroDataStore({"a": {"b": 1}})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.delete("a..b")

    def test_has_with_empty_string(self):
        """Test has() rejects empty path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.has("")

    def test_has_with_whitespace_only(self):
        """Test has() rejects whitespace-only path."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="Path cannot be empty"):
            data.has("   ")

    def test_has_with_leading_dot(self):
        """Test has() rejects path with leading dot."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.has(".a")

    def test_has_with_trailing_dot(self):
        """Test has() rejects path with trailing dot."""
        data = NitroDataStore({"a": 1})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.has("a.")

    def test_has_with_consecutive_dots(self):
        """Test has() rejects path with consecutive dots."""
        data = NitroDataStore({"a": {"b": 1}})
        with pytest.raises(ValueError, match="contains empty segments"):
            data.has("a..b")

    def test_valid_single_segment_path(self):
        """Test all methods accept valid single-segment paths."""
        data = NitroDataStore({"key": "value"})

        assert data.get("key") == "value"
        assert data.has("key") is True

        data.set("newkey", "newvalue")
        assert data.newkey == "newvalue"

        assert data.delete("key") is True

    def test_valid_multi_segment_path(self):
        """Test all methods accept valid multi-segment paths."""
        data = NitroDataStore({"a": {"b": {"c": "value"}}})

        assert data.get("a.b.c") == "value"
        assert data.has("a.b.c") is True

        data.set("x.y.z", "test")
        assert data.get("x.y.z") == "test"

        assert data.delete("a.b.c") is True
        assert data.has("a.b.c") is False


class TestCircularReferenceProtection:
    """Tests for circular reference detection in deep operations."""

    def test_deep_copy_with_circular_reference_in_dict(self):
        """Test _deep_copy raises ValueError for circular dict reference."""
        circular_dict = {"a": 1}
        circular_dict["self"] = circular_dict

        with pytest.raises(ValueError, match="Circular reference detected"):
            NitroDataStore._deep_copy(circular_dict)

    def test_deep_copy_with_nested_circular_reference(self):
        """Test _deep_copy detects circular reference in nested dict."""
        obj = {"level1": {"level2": {}}}
        obj["level1"]["level2"]["back_to_root"] = obj

        with pytest.raises(ValueError, match="Circular reference detected"):
            NitroDataStore._deep_copy(obj)

    def test_deep_copy_with_circular_list(self):
        """Test _deep_copy detects circular reference in list."""
        circular_list = [1, 2, 3]
        circular_list.append(circular_list)

        with pytest.raises(ValueError, match="Circular reference detected"):
            NitroDataStore._deep_copy(circular_list)

    def test_deep_copy_with_list_containing_circular_dict(self):
        """Test _deep_copy detects circular reference in dict within list."""
        circular_dict = {"a": 1}
        circular_dict["self"] = circular_dict
        obj = {"items": [circular_dict]}

        with pytest.raises(ValueError, match="Circular reference detected"):
            NitroDataStore._deep_copy(obj)

    def test_deep_copy_non_circular_succeeds(self):
        """Test _deep_copy succeeds with non-circular structures."""
        obj = {
            "a": {"b": {"c": 1}},
            "list": [1, 2, {"nested": "value"}],
            "repeated_value": 42,
        }
        another_ref = {"data": 42}
        obj["ref1"] = another_ref
        obj["ref2"] = another_ref

        result = NitroDataStore._deep_copy(obj)

        assert result == obj
        assert result is not obj
        assert result["a"] is not obj["a"]
        assert result["list"] is not obj["list"]

    def test_deep_merge_with_circular_reference_in_recursive_path(self):
        """Test _deep_merge detects circular reference during recursive merge."""
        base = {"a": {}}
        base["a"]["b"] = base["a"]
        overlay = {"a": {"b": {"new": "value"}}}

        with pytest.raises(ValueError, match="Circular reference detected"):
            NitroDataStore._deep_merge(base, overlay)

    def test_deep_merge_non_circular_succeeds(self):
        """Test _deep_merge succeeds with non-circular structures."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        overlay = {"a": {"y": 20, "z": 30}, "c": 4}

        result = NitroDataStore._deep_merge(base, overlay)

        assert result == {"a": {"x": 1, "y": 20, "z": 30}, "b": 3, "c": 4}
        assert result is not base
        assert result["a"] is not base["a"]

    def test_to_dict_with_circular_reference_raises(self):
        """Test to_dict() raises error when internal data has circular reference."""
        data = NitroDataStore({})
        data._data["self"] = data._data

        with pytest.raises(ValueError, match="Circular reference detected"):
            data.to_dict()

    def test_merge_with_circular_reference_raises(self):
        """Test merge() raises error when merging data with circular reference."""
        data = NitroDataStore({"config": {}})
        data._data["config"]["self"] = data._data["config"]
        overlay = {"config": {"self": {"new": "value"}}}

        with pytest.raises(ValueError, match="Circular reference detected"):
            data.merge(overlay)

    def test_deepcopy_module_with_circular_reference(self):
        """Test copy.deepcopy() raises error with circular reference."""
        import copy

        data = NitroDataStore({})
        data._data["self"] = data._data

        with pytest.raises(ValueError, match="Circular reference detected"):
            copy.deepcopy(data)

    def test_complex_non_circular_structure(self):
        """Test deeply nested non-circular structure works correctly."""
        obj = {
            "level1": {"level2": {"level3": {"level4": {"data": "deep"}}}},
            "lists": [[1, 2], [3, 4]],
            "mixed": {"items": [{"nested": "dict"}]},
        }

        result = NitroDataStore._deep_copy(obj)

        assert result == obj
        assert result is not obj
        assert (
            result["level1"]["level2"]["level3"]["level4"]
            is not obj["level1"]["level2"]["level3"]["level4"]
        )
