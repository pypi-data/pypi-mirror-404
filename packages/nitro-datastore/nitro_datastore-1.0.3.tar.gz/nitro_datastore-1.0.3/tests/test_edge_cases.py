"""Tests for edge cases and coverage completeness."""

import pytest
from nitro_datastore import NitroDataStore


class TestNitroDataStoreEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_datastore(self):
        """Test operations on empty datastore."""
        data = NitroDataStore()
        assert len(data) == 0
        assert data.get("any.key") is None
        assert data.has("any.key") is False
        assert data.to_dict() == {}

    def test_mixed_access_patterns(self):
        """Test mixing different access patterns."""
        data = NitroDataStore()

        data.set("site.name", "Test")

        assert data["site"]["name"] == "Test"

        assert data.site.name == "Test"

        assert data.get("site.name") == "Test"

    def test_modifying_returned_datastore(self):
        """Test that modifying returned NitroDataStore affects original."""
        data = NitroDataStore({"site": {"name": "Old"}})

        site = data.site
        site.name = "New"

        assert data.get("site.name") == "New"

    def test_to_dict_is_deep_copy(self):
        """Test that to_dict returns a deep copy."""
        data = NitroDataStore({"site": {"name": "Test"}})
        exported = data.to_dict()

        exported["site"]["name"] = "Modified"

        assert data.get("site.name") == "Test"

    def test_nested_lists_preserved(self):
        """Test that nested lists are preserved correctly."""
        data = NitroDataStore(
            {"tags": ["python", "web", "cli"], "nested": {"items": [1, 2, 3]}}
        )

        assert data.get("tags") == ["python", "web", "cli"]
        assert data.get("nested.items") == [1, 2, 3]
        assert data.tags == ["python", "web", "cli"]

    def test_unicode_support(self):
        """Test Unicode character support."""
        data = NitroDataStore({"japanese": "日本語", "smiley": ":)", "chinese": "中文"})

        assert data.get("japanese") == "日本語"
        assert data.get("smiley") == ":)"
        assert data.get("chinese") == "中文"

    def test_numeric_string_keys(self):
        """Test keys that look like numbers."""
        data = NitroDataStore({"123": "value", "456": {"789": "nested"}})
        assert data.get("123") == "value"
        assert data.get("456.789") == "nested"

    def test_special_character_keys(self):
        """Test keys with special characters (that aren't dots)."""
        data = NitroDataStore(
            {
                "key-with-dashes": "value1",
                "key_with_underscores": "value2",
                "key:with:colons": "value3",
            }
        )

        assert data["key-with-dashes"] == "value1"
        assert data["key_with_underscores"] == "value2"
        assert data["key:with:colons"] == "value3"

    def test_boolean_and_none_values(self):
        """Test storing boolean and None values."""
        data = NitroDataStore({"enabled": True, "disabled": False, "nullable": None})

        assert data.get("enabled") is True
        assert data.get("disabled") is False
        assert data.get("nullable") is None

    def test_deep_merge_with_lists(self):
        """Test that deep merge replaces lists (doesn't merge them)."""
        data1 = NitroDataStore({"tags": ["a", "b"]})
        data2 = NitroDataStore({"tags": ["c", "d"]})

        data1.merge(data2)

        assert data1.get("tags") == ["c", "d"]

    def test_getattr_invalid_private_attribute(self):
        """Test accessing a non-existent private attribute raises AttributeError."""
        data = NitroDataStore({"name": "Test"})
        with pytest.raises(AttributeError, match="has no attribute '_nonexistent'"):
            _ = data._nonexistent

    def test_to_dict_deep_copies_nested_lists(self):
        """Test that to_dict deep copies nested lists."""
        data = NitroDataStore({"items": {"list1": [1, 2, 3], "list2": ["a", "b", "c"]}})
        exported = data.to_dict()

        exported["items"]["list1"].append(4)
        exported["items"]["list2"].append("d")

        assert data.get("items.list1") == [1, 2, 3]
        assert data.get("items.list2") == ["a", "b", "c"]


class TestCoverageCompleteness:
    """Tests to achieve 100% code coverage."""

    def test_list_paths_cache_hit(self):
        """Test list_paths returns from cache on second call."""
        data = NitroDataStore({"a": {"b": 1}, "c": 2})
        paths1 = data.list_paths()
        paths2 = data.list_paths()
        assert paths1 == paths2
        assert paths1 is not paths2

    def test_find_all_keys_with_lists(self):
        """Test find_all_keys traverses lists correctly."""
        data = NitroDataStore(
            {"items": [{"name": "item1", "value": 10}, {"name": "item2", "value": 20}]}
        )
        result = data.find_all_keys("name")
        assert "items.0.name" in result
        assert "items.1.name" in result
        assert result["items.0.name"] == "item1"

    def test_find_values_with_lists(self):
        """Test find_values traverses lists correctly."""
        data = NitroDataStore(
            {"numbers": [1, 2, 3, 4, 5], "nested": {"nums": [10, 20, 30]}}
        )
        result = data.find_values(lambda v: isinstance(v, int) and v > 3)
        assert "numbers.3" in result
        assert "numbers.4" in result
        assert result["numbers.3"] == 4

    def test_transform_all_with_lists(self):
        """Test transform_all handles lists correctly."""
        data = NitroDataStore({"items": [1, 2, 3], "nested": {"values": [4, 5, 6]}})
        transformed = data.transform_all(
            lambda p, v: v * 2 if isinstance(v, int) else v
        )
        assert transformed.to_dict() == {
            "items": [2, 4, 6],
            "nested": {"values": [8, 10, 12]},
        }

    def test_transform_keys_with_lists(self):
        """Test transform_keys handles lists correctly."""
        data = NitroDataStore({"items": [1, 2, 3], "config": {"values": [4, 5]}})
        transformed = data.transform_keys(lambda k: k.upper())
        result = transformed.to_dict()
        assert "ITEMS" in result
        assert result["ITEMS"] == [1, 2, 3]

    def test_diff_with_plain_dict(self):
        """Test diff works with plain dict (not NitroDataStore)."""
        data = NitroDataStore({"a": 1, "b": 2})
        diff = data.diff({"a": 1, "b": 3, "c": 4})
        assert diff["added"] == {"c": 4}
        assert diff["changed"]["b"]["old"] == 2
        assert diff["changed"]["b"]["new"] == 3

    def test_eq_with_incompatible_types(self):
        """Test __eq__ returns False for incompatible types."""
        data = NitroDataStore({"a": 1})
        assert (data == "string") is False
        assert (data == 123) is False
        assert (data == None) is False  # noqa: E711
        assert (data == [1, 2, 3]) is False

    def test_repr(self):
        """Test __repr__ returns proper representation."""
        data = NitroDataStore({"a": 1, "b": 2})
        repr_str = repr(data)
        assert repr_str.startswith("NitroDataStore(")
        assert "'a': 1" in repr_str or '"a": 1' in repr_str

    def test_copy_module_support(self):
        """Test copy.copy creates shallow copy."""
        import copy

        data = NitroDataStore({"a": 1, "b": {"c": 2}})
        copied = copy.copy(data)
        assert copied.to_dict() == data.to_dict()
        assert copied is not data
        assert copied._data is not data._data

    def test_eq_with_dict(self):
        """Test __eq__ works with plain dict."""
        data = NitroDataStore({"a": 1, "b": 2})
        plain_dict = {"a": 1, "b": 2}
        assert data == plain_dict
        assert plain_dict == data

    def test_iter_protocol(self):
        """Test __iter__ allows iteration."""
        data = NitroDataStore({"a": 1, "b": 2, "c": 3})
        keys = []
        for key in data:
            keys.append(key)
        assert set(keys) == {"a", "b", "c"}

    def test_deepcopy_module_support(self):
        """Test copy.deepcopy creates deep copy."""
        import copy

        data = NitroDataStore({"a": 1, "b": {"c": 2}})
        deep = copy.deepcopy(data)
        assert deep.to_dict() == data.to_dict()
        assert deep is not data
        assert deep._data is not data._data
        deep._data["b"]["c"] = 999
        assert data._data["b"]["c"] == 2
