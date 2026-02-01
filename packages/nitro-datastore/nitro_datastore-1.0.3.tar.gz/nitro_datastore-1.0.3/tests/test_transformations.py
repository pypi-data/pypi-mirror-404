"""Tests for data transformation operations."""

from nitro_datastore import NitroDataStore


class TestNitroDataStoreMerge:
    """Test merge operations."""

    def test_merge_with_datastore(self):
        """Test merging with another NitroDataStore."""
        data1 = NitroDataStore({"site": {"name": "Site 1", "url": "example.com"}})
        data2 = NitroDataStore({"site": {"name": "Site 2"}, "extra": "data"})

        data1.merge(data2)

        assert data1.get("site.name") == "Site 2"
        assert data1.get("site.url") == "example.com"
        assert data1.get("extra") == "data"

    def test_merge_with_dict(self):
        """Test merging with a plain dictionary."""
        data = NitroDataStore({"site": {"name": "Old"}})
        data.merge({"site": {"name": "New", "url": "example.com"}})

        assert data.get("site.name") == "New"
        assert data.get("site.url") == "example.com"

    def test_merge_deep(self):
        """Test deep merging of nested structures."""
        data1 = NitroDataStore(
            {"config": {"theme": {"colors": {"primary": "blue", "secondary": "green"}}}}
        )
        data2 = NitroDataStore(
            {"config": {"theme": {"colors": {"primary": "red"}, "font": "Arial"}}}
        )

        data1.merge(data2)

        assert data1.get("config.theme.colors.primary") == "red"
        assert data1.get("config.theme.colors.secondary") == "green"
        assert data1.get("config.theme.font") == "Arial"

    def test_merge_empty(self):
        """Test merging empty datastore does nothing."""
        data = NitroDataStore({"name": "Test"})
        data.merge(NitroDataStore())
        assert data.get("name") == "Test"


class TestNitroDataStoreFlatten:
    """Test flatten operations."""

    def test_flatten_simple(self):
        """Test flattening simple nested structure."""
        data = NitroDataStore({"site": {"name": "Test", "url": "example.com"}})
        flat = data.flatten()
        assert flat == {"site.name": "Test", "site.url": "example.com"}

    def test_flatten_deeply_nested(self):
        """Test flattening deeply nested structure."""
        data = NitroDataStore({"a": {"b": {"c": {"d": "value"}}}})
        flat = data.flatten()
        assert flat == {"a.b.c.d": "value"}

    def test_flatten_mixed(self):
        """Test flattening mixed structure."""
        data = NitroDataStore(
            {
                "simple": "value",
                "nested": {"key": "value2", "deeper": {"key": "value3"}},
            }
        )
        flat = data.flatten()
        assert flat == {
            "simple": "value",
            "nested.key": "value2",
            "nested.deeper.key": "value3",
        }

    def test_flatten_custom_separator(self):
        """Test flattening with custom separator."""
        data = NitroDataStore({"site": {"name": "Test"}})
        flat = data.flatten(separator="/")
        assert flat == {"site/name": "Test"}

    def test_flatten_preserves_non_dict_values(self):
        """Test that flatten preserves lists and other non-dict values."""
        data = NitroDataStore(
            {"site": {"tags": ["tag1", "tag2"], "enabled": True, "count": 42}}
        )
        flat = data.flatten()
        assert flat["site.tags"] == ["tag1", "tag2"]
        assert flat["site.enabled"] is True
        assert flat["site.count"] == 42


class TestNitroDataStoreTransformations:
    """Test transformation utilities."""

    def test_transform_all(self):
        """Test transforming all values."""
        data = NitroDataStore({"name": "test", "title": "hello"})
        upper = data.transform_all(lambda p, v: v.upper() if isinstance(v, str) else v)
        assert upper.name == "TEST"
        assert upper.title == "HELLO"
        assert data.name == "test"

    def test_transform_all_nested(self):
        """Test transforming nested values."""
        data = NitroDataStore({"site": {"name": "test", "count": 5}})
        transformed = data.transform_all(
            lambda p, v: v.upper() if isinstance(v, str) else v
        )
        assert transformed.site.name == "TEST"
        assert transformed.site.count == 5

    def test_transform_keys(self):
        """Test transforming keys."""
        data = NitroDataStore({"first-name": "John", "last-name": "Doe"})
        snake = data.transform_keys(lambda k: k.replace("-", "_"))
        assert "first_name" in snake
        assert "last_name" in snake
        assert "first-name" in data

    def test_transform_keys_nested(self):
        """Test transforming nested keys."""
        data = NitroDataStore({"user-info": {"first-name": "John"}})
        snake = data.transform_keys(lambda k: k.replace("-", "_"))
        assert "user_info" in snake
        assert snake.get("user_info.first_name") == "John"
