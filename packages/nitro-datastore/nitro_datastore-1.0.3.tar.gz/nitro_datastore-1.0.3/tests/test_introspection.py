"""Tests for data introspection and analysis."""

from nitro_datastore import NitroDataStore


class TestNitroDataStorePathIntrospection:
    """Test path introspection utilities."""

    def test_list_paths_simple(self):
        """Test listing all paths in simple structure."""
        data = NitroDataStore({"site": {"name": "Test", "url": "example.com"}})
        paths = data.list_paths()
        assert set(paths) == {"site", "site.name", "site.url"}

    def test_list_paths_nested(self):
        """Test listing paths in deeply nested structure."""
        data = NitroDataStore({"config": {"theme": {"colors": {"primary": "#007bff"}}}})
        paths = data.list_paths()
        assert "config" in paths
        assert "config.theme" in paths
        assert "config.theme.colors" in paths
        assert "config.theme.colors.primary" in paths

    def test_list_paths_with_lists(self):
        """Test listing paths with list indices."""
        data = NitroDataStore({"posts": [{"title": "A"}, {"title": "B"}]})
        paths = data.list_paths()
        assert "posts" in paths
        assert "posts.0" in paths
        assert "posts.1" in paths
        assert "posts.0.title" in paths
        assert "posts.1.title" in paths

    def test_list_paths_with_prefix(self):
        """Test filtering paths by prefix."""
        data = NitroDataStore(
            {"site": {"name": "Test", "url": "example.com"}, "theme": {"color": "blue"}}
        )
        paths = data.list_paths(prefix="site")
        assert all(p.startswith("site") for p in paths)
        assert "theme" not in paths

    def test_find_paths_wildcard_single(self):
        """Test finding paths with single wildcard."""
        data = NitroDataStore({"posts": [{"title": "A"}, {"title": "B"}]})
        paths = data.find_paths("posts.*.title")
        assert set(paths) == {"posts.0.title", "posts.1.title"}

    def test_find_paths_wildcard_any(self):
        """Test finding paths with ** wildcard."""
        data = NitroDataStore({"a": {"b": {"c": 1}}, "x": {"y": {"c": 2}}})
        paths = data.find_paths("**.c")
        assert "a.b.c" in paths
        assert "x.y.c" in paths

    def test_get_many(self):
        """Test getting multiple paths at once."""
        data = NitroDataStore(
            {"site": {"name": "Test", "url": "example.com"}, "theme": "dark"}
        )
        result = data.get_many(["site.name", "site.url", "theme", "missing"])
        assert result == {
            "site.name": "Test",
            "site.url": "example.com",
            "theme": "dark",
            "missing": None,
        }


class TestNitroDataStoreDeepSearch:
    """Test deep search utilities."""

    def test_find_all_keys(self):
        """Test finding all occurrences of a key name."""
        data = NitroDataStore(
            {"site": {"url": "site.com"}, "social": {"github": {"url": "github.com"}}}
        )
        result = data.find_all_keys("url")
        assert result == {"site.url": "site.com", "social.github.url": "github.com"}

    def test_find_all_keys_single_occurrence(self):
        """Test finding key with single occurrence."""
        data = NitroDataStore({"name": "Test", "info": {"age": 25}})
        result = data.find_all_keys("name")
        assert result == {"name": "Test"}

    def test_find_all_keys_no_matches(self):
        """Test finding key that doesn't exist."""
        data = NitroDataStore({"name": "Test"})
        result = data.find_all_keys("missing")
        assert result == {}

    def test_find_values_by_type(self):
        """Test finding values by type."""
        data = NitroDataStore(
            {"name": "test", "count": 42, "enabled": True, "nested": {"value": "hello"}}
        )
        result = data.find_values(lambda v: isinstance(v, str))
        assert set(result.keys()) == {"name", "nested.value"}

    def test_find_values_by_pattern(self):
        """Test finding values matching pattern."""
        data = NitroDataStore(
            {"images": {"hero": "pic.jpg", "thumb": "small.png"}, "count": 5}
        )
        result = data.find_values(lambda v: isinstance(v, str) and v.endswith(".jpg"))
        assert result == {"images.hero": "pic.jpg"}


class TestNitroDataStoreIntrospection:
    """Test data introspection."""

    def test_describe_simple(self):
        """Test describing simple structure."""
        data = NitroDataStore({"name": "Test", "count": 42})
        description = data.describe()
        assert description["name"]["type"] == "str"
        assert description["count"]["type"] == "int"

    def test_describe_nested(self):
        """Test describing nested structure."""
        data = NitroDataStore({"site": {"name": "Test", "settings": {"theme": "dark"}}})
        description = data.describe()
        assert description["site"]["type"] == "dict"
        assert "name" in description["site"]["structure"]

    def test_describe_list(self):
        """Test describing lists."""
        data = NitroDataStore({"posts": [{"title": "A"}, {"title": "B"}]})
        description = data.describe()
        assert description["posts"]["type"] == "list"
        assert description["posts"]["length"] == 2
        assert "dict" in description["posts"]["item_types"]

    def test_stats(self):
        """Test getting statistics."""
        data = NitroDataStore({"a": {"b": {"c": 1}}, "x": [1, 2, 3]})
        stats = data.stats()
        assert stats["total_dicts"] == 3
        assert stats["total_lists"] == 1
        assert stats["total_keys"] == 4
        assert stats["max_depth"] >= 2

    def test_stats_empty(self):
        """Test stats on empty datastore."""
        data = NitroDataStore()
        stats = data.stats()
        assert stats["total_dicts"] == 1
        assert stats["total_lists"] == 0
        assert stats["total_keys"] == 0


class TestNitroDataStoreDiff:
    """Test diff and equals."""

    def test_diff_added(self):
        """Test detecting added keys."""
        data1 = NitroDataStore({"a": 1})
        data2 = NitroDataStore({"a": 1, "b": 2})
        diff = data1.diff(data2)
        assert diff["added"] == {"b": 2}
        assert diff["removed"] == {}
        assert diff["changed"] == {}

    def test_diff_removed(self):
        """Test detecting removed keys."""
        data1 = NitroDataStore({"a": 1, "b": 2})
        data2 = NitroDataStore({"a": 1})
        diff = data1.diff(data2)
        assert diff["removed"] == {"b": 2}
        assert diff["added"] == {}

    def test_diff_changed(self):
        """Test detecting changed values."""
        data1 = NitroDataStore({"a": 1, "b": 2})
        data2 = NitroDataStore({"a": 1, "b": 3})
        diff = data1.diff(data2)
        assert diff["changed"] == {"b": {"old": 2, "new": 3}}

    def test_diff_complex(self):
        """Test diff with complex changes."""
        data1 = NitroDataStore(
            {"site": {"name": "Old", "url": "old.com"}, "theme": "light"}
        )
        data2 = NitroDataStore(
            {"site": {"name": "New", "url": "old.com"}, "version": "2.0"}
        )
        diff = data1.diff(data2)
        assert "site.name" in diff["changed"]
        assert "version" in diff["added"]
        assert "theme" in diff["removed"]

    def test_equals_true(self):
        """Test equals with identical data."""
        data1 = NitroDataStore({"a": 1, "b": {"c": 2}})
        data2 = NitroDataStore({"a": 1, "b": {"c": 2}})
        assert data1.equals(data2)

    def test_equals_false(self):
        """Test equals with different data."""
        data1 = NitroDataStore({"a": 1})
        data2 = NitroDataStore({"a": 2})
        assert not data1.equals(data2)

    def test_equals_with_dict(self):
        """Test equals with plain dict."""
        data = NitroDataStore({"a": 1})
        assert data.equals({"a": 1})
        assert not data.equals({"a": 2})
