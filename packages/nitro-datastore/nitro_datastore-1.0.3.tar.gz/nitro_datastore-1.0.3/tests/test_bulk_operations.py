"""Tests for bulk data operations."""

from nitro_datastore import NitroDataStore


class TestNitroDataStoreBulkOperations:
    """Test bulk operations."""

    def test_update_where(self):
        """Test updating values matching condition."""
        data = NitroDataStore(
            {"urls": ["http://a.com", "https://b.com", "http://c.com"]}
        )
        count = data.update_where(
            lambda p, v: isinstance(v, str) and "http://" in v,
            lambda v: v.replace("http://", "https://"),
        )
        assert count == 2
        assert all("https://" in url for url in data.urls)

    def test_update_where_nested(self):
        """Test updating nested values."""
        data = NitroDataStore(
            {
                "site": {"url": "http://site.com"},
                "social": {"github": "http://github.com"},
            }
        )
        count = data.update_where(
            lambda p, v: isinstance(v, str) and "http://" in v,
            lambda v: v.replace("http://", "https://"),
        )
        assert count == 2
        assert data.get("site.url") == "https://site.com"
        assert data.get("social.github") == "https://github.com"

    def test_remove_nulls(self):
        """Test removing None values."""
        data = NitroDataStore({"a": 1, "b": None, "c": {"d": None, "e": 2}})
        count = data.remove_nulls()
        assert count == 2
        assert data.to_dict() == {"a": 1, "c": {"e": 2}}

    def test_remove_nulls_in_lists(self):
        """Test removing None from lists."""
        data = NitroDataStore({"items": [1, None, 2, None, 3]})
        count = data.remove_nulls()
        assert count == 2
        assert data["items"] == [1, 2, 3]

    def test_remove_empty(self):
        """Test removing empty containers."""
        data = NitroDataStore({"a": {}, "b": [], "c": {"d": 1, "e": {}}, "f": "value"})
        count = data.remove_empty()
        assert count == 3
        result = data.to_dict()
        assert "a" not in result
        assert "b" not in result
        assert result["c"] == {"d": 1}

    def test_remove_empty_nested_lists(self):
        """Test removing empty nested lists."""
        data = NitroDataStore({"items": [[], [1], []]})
        count = data.remove_empty()
        assert count == 2
        assert data["items"] == [[1]]
