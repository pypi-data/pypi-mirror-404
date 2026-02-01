"""Tests for basic NitroDataStore operations."""

import json

import pytest
from nitro_datastore import NitroDataStore


class TestNitroDataStoreInit:
    """Test initialization."""

    def test_init_empty(self):
        """Test initializing with no data."""
        data = NitroDataStore()
        assert len(data) == 0
        assert data.to_dict() == {}

    def test_init_with_data(self):
        """Test initializing with data."""
        initial = {"site": {"name": "My Site", "url": "example.com"}}
        data = NitroDataStore(initial)
        assert len(data) == 1
        assert data.to_dict() == initial

    def test_init_with_none(self):
        """Test initializing with None explicitly."""
        data = NitroDataStore(None)
        assert len(data) == 0
        assert data.to_dict() == {}


class TestNitroDataStoreGet:
    """Test get operations."""

    def test_get_simple_key(self):
        """Test getting a simple top-level key."""
        data = NitroDataStore({"name": "Test"})
        assert data.get("name") == "Test"

    def test_get_nested_key(self):
        """Test getting nested key with dot notation."""
        data = NitroDataStore({"site": {"name": "My Site", "url": "example.com"}})
        assert data.get("site.name") == "My Site"
        assert data.get("site.url") == "example.com"

    def test_get_deeply_nested_key(self):
        """Test getting deeply nested key."""
        data = NitroDataStore({"config": {"theme": {"colors": {"primary": "#007bff"}}}})
        assert data.get("config.theme.colors.primary") == "#007bff"

    def test_get_missing_key_returns_none(self):
        """Test that missing key returns None."""
        data = NitroDataStore({"name": "Test"})
        assert data.get("missing") is None

    def test_get_missing_nested_key_returns_none(self):
        """Test that missing nested key returns None."""
        data = NitroDataStore({"site": {"name": "Test"}})
        assert data.get("site.missing") is None
        assert data.get("missing.nested.key") is None

    def test_get_with_default(self):
        """Test get with default value."""
        data = NitroDataStore({"name": "Test"})
        assert data.get("missing", "default") == "default"
        assert data.get("site.missing", "fallback") == "fallback"

    def test_get_returns_various_types(self):
        """Test that get returns correct types."""
        data = NitroDataStore(
            {
                "string": "text",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
            }
        )
        assert isinstance(data.get("string"), str)
        assert isinstance(data.get("number"), int)
        assert isinstance(data.get("float"), float)
        assert isinstance(data.get("bool"), bool)
        assert isinstance(data.get("list"), list)
        assert isinstance(data.get("dict"), dict)


class TestNitroDataStoreSet:
    """Test set operations."""

    def test_set_simple_key(self):
        """Test setting a simple key."""
        data = NitroDataStore()
        data.set("name", "Test")
        assert data.get("name") == "Test"

    def test_set_nested_key(self):
        """Test setting nested key with dot notation."""
        data = NitroDataStore()
        data.set("site.name", "My Site")
        assert data.get("site.name") == "My Site"

    def test_set_deeply_nested_key(self):
        """Test setting deeply nested key creates structure."""
        data = NitroDataStore()
        data.set("config.theme.colors.primary", "#007bff")
        assert data.get("config.theme.colors.primary") == "#007bff"

    def test_set_overwrites_existing(self):
        """Test that set overwrites existing values."""
        data = NitroDataStore({"name": "Old"})
        data.set("name", "New")
        assert data.get("name") == "New"

    def test_set_overwrites_nested(self):
        """Test that set overwrites nested values."""
        data = NitroDataStore({"site": {"name": "Old"}})
        data.set("site.name", "New")
        assert data.get("site.name") == "New"

    def test_set_creates_missing_intermediate_dicts(self):
        """Test that set creates missing intermediate dictionaries."""
        data = NitroDataStore()
        data.set("a.b.c.d", "value")

        assert "a" in data
        assert isinstance(data.to_dict()["a"], dict)
        assert "b" in data.to_dict()["a"]
        assert data.get("a.b.c.d") == "value"

    def test_set_replaces_non_dict_with_dict(self):
        """Test that set replaces non-dict values when creating nested paths."""
        data = NitroDataStore({"site": "string_value"})
        data.set("site.name", "New Site")

        assert isinstance(data.to_dict()["site"], dict)
        assert data.get("site.name") == "New Site"

    def test_set_various_types(self):
        """Test setting various value types."""
        data = NitroDataStore()
        data.set("string", "text")
        data.set("number", 42)
        data.set("float", 3.14)
        data.set("bool", True)
        data.set("list", [1, 2, 3])
        data.set("dict", {"nested": "value"})

        assert data.get("string") == "text"
        assert data.get("number") == 42
        assert data.get("float") == 3.14
        assert data.get("bool") is True
        assert data.get("list") == [1, 2, 3]
        assert data.get("dict") == {"nested": "value"}


class TestNitroDataStoreDelete:
    """Test delete operations."""

    def test_delete_simple_key(self):
        """Test deleting a simple key."""
        data = NitroDataStore({"name": "Test", "other": "value"})
        result = data.delete("name")
        assert result is True
        assert "name" not in data

    def test_delete_nested_key(self):
        """Test deleting nested key."""
        data = NitroDataStore({"site": {"name": "Test", "url": "example.com"}})
        result = data.delete("site.name")
        assert result is True
        assert data.get("site.name") is None
        assert data.get("site.url") == "example.com"

    def test_delete_missing_key_returns_false(self):
        """Test deleting non-existent key returns False."""
        data = NitroDataStore({"name": "Test"})
        result = data.delete("missing")
        assert result is False

    def test_delete_missing_nested_key_returns_false(self):
        """Test deleting non-existent nested key returns False."""
        data = NitroDataStore({"site": {"name": "Test"}})
        result = data.delete("site.missing")
        assert result is False
        result = data.delete("missing.nested.key")
        assert result is False

    def test_delete_already_deleted_returns_false(self):
        """Test deleting already deleted key returns False."""
        data = NitroDataStore({"name": "Test"})
        assert data.delete("name") is True
        assert data.delete("name") is False


class TestNitroDataStoreHas:
    """Test has (existence check) operations."""

    def test_has_simple_key_exists(self):
        """Test checking simple key that exists."""
        data = NitroDataStore({"name": "Test"})
        assert data.has("name") is True

    def test_has_simple_key_missing(self):
        """Test checking simple key that doesn't exist."""
        data = NitroDataStore({"name": "Test"})
        assert data.has("missing") is False

    def test_has_nested_key_exists(self):
        """Test checking nested key that exists."""
        data = NitroDataStore({"site": {"name": "Test"}})
        assert data.has("site.name") is True

    def test_has_nested_key_missing(self):
        """Test checking nested key that doesn't exist."""
        data = NitroDataStore({"site": {"name": "Test"}})
        assert data.has("site.missing") is False
        assert data.has("missing.nested.key") is False

    def test_has_deeply_nested(self):
        """Test checking deeply nested keys."""
        data = NitroDataStore({"a": {"b": {"c": {"d": "value"}}}})
        assert data.has("a.b.c.d") is True
        assert data.has("a.b.c.missing") is False


class TestNitroDataStoreIteration:
    """Test iteration methods."""

    def test_keys(self):
        """Test keys() method."""
        data = NitroDataStore({"a": 1, "b": 2, "c": 3})
        keys = list(data.keys())
        assert set(keys) == {"a", "b", "c"}

    def test_values(self):
        """Test values() method."""
        data = NitroDataStore({"a": 1, "b": 2, "c": 3})
        values = list(data.values())
        assert set(values) == {1, 2, 3}

    def test_items(self):
        """Test items() method."""
        data = NitroDataStore({"a": 1, "b": 2})
        items = list(data.items())
        assert set(items) == {("a", 1), ("b", 2)}

    def test_iteration_with_for_loop(self):
        """Test that datastore is iterable."""
        data = NitroDataStore({"a": 1, "b": 2, "c": 3})
        keys = []
        for key in data.keys():
            keys.append(key)
        assert set(keys) == {"a", "b", "c"}


class TestNitroDataStoreDictAccess:
    """Test dictionary-style access."""

    def test_getitem(self):
        """Test __getitem__ (data['key'])."""
        data = NitroDataStore({"name": "Test", "count": 42})
        assert data["name"] == "Test"
        assert data["count"] == 42

    def test_getitem_missing_raises_keyerror(self):
        """Test __getitem__ with missing key raises KeyError."""
        data = NitroDataStore({"name": "Test"})
        with pytest.raises(KeyError):
            _ = data["missing"]

    def test_getitem_returns_wrapped_dict(self):
        """Test __getitem__ wraps nested dicts in NitroDataStore."""
        data = NitroDataStore({"site": {"name": "Test"}})
        site = data["site"]
        assert isinstance(site, NitroDataStore)
        assert site["name"] == "Test"

    def test_getitem_chaining(self):
        """Test chaining __getitem__ calls."""
        data = NitroDataStore({"site": {"config": {"theme": "dark"}}})
        assert data["site"]["config"]["theme"] == "dark"

    def test_setitem(self):
        """Test __setitem__ (data['key'] = value)."""
        data = NitroDataStore()
        data["name"] = "Test"
        assert data["name"] == "Test"

    def test_setitem_overwrites(self):
        """Test __setitem__ overwrites existing values."""
        data = NitroDataStore({"name": "Old"})
        data["name"] = "New"
        assert data["name"] == "New"

    def test_delitem(self):
        """Test __delitem__ (del data['key'])."""
        data = NitroDataStore({"name": "Test", "other": "value"})
        del data["name"]
        assert "name" not in data
        assert data["other"] == "value"

    def test_delitem_missing_raises_keyerror(self):
        """Test __delitem__ with missing key raises KeyError."""
        data = NitroDataStore({"name": "Test"})
        with pytest.raises(KeyError):
            del data["missing"]

    def test_contains(self):
        """Test __contains__ ('key' in data)."""
        data = NitroDataStore({"name": "Test", "count": 42})
        assert "name" in data
        assert "count" in data
        assert "missing" not in data


class TestNitroDataStoreDotAccess:
    """Test dot notation access."""

    def test_getattr(self):
        """Test __getattr__ (data.key)."""
        data = NitroDataStore({"name": "Test", "count": 42})
        assert data.name == "Test"
        assert data.count == 42

    def test_getattr_missing_raises_attributeerror(self):
        """Test __getattr__ with missing key raises AttributeError."""
        data = NitroDataStore({"name": "Test"})
        with pytest.raises(AttributeError):
            _ = data.missing

    def test_getattr_returns_wrapped_dict(self):
        """Test __getattr__ wraps nested dicts in NitroDataStore."""
        data = NitroDataStore({"site": {"name": "Test"}})
        site = data.site
        assert isinstance(site, NitroDataStore)
        assert site.name == "Test"

    def test_getattr_chaining(self):
        """Test chaining __getattr__ calls."""
        data = NitroDataStore({"site": {"config": {"theme": "dark"}}})
        assert data.site.config.theme == "dark"

    def test_getattr_private_attributes(self):
        """Test that private attributes work normally."""
        data = NitroDataStore({"name": "Test"})
        assert isinstance(data._data, dict)

    def test_setattr(self):
        """Test __setattr__ (data.key = value)."""
        data = NitroDataStore()
        data.name = "Test"
        assert data.name == "Test"

    def test_setattr_overwrites(self):
        """Test __setattr__ overwrites existing values."""
        data = NitroDataStore({"name": "Old"})
        data.name = "New"
        assert data.name == "New"

    def test_setattr_private_attributes(self):
        """Test that private attributes can be set normally."""
        data = NitroDataStore()
        data._custom = "value"
        assert data._custom == "value"


class TestNitroDataStoreMagicMethods:
    """Test other magic methods."""

    def test_len(self):
        """Test __len__ (len(data))."""
        data = NitroDataStore({"a": 1, "b": 2, "c": 3})
        assert len(data) == 3

    def test_len_empty(self):
        """Test __len__ with empty datastore."""
        data = NitroDataStore()
        assert len(data) == 0

    def test_len_nested_counts_top_level_only(self):
        """Test that __len__ only counts top-level keys."""
        data = NitroDataStore(
            {
                "site": {"name": "Test", "url": "example.com"},
                "config": {"theme": "dark"},
            }
        )
        assert len(data) == 2

    def test_repr(self):
        """Test __repr__."""
        data = NitroDataStore({"name": "Test"})
        repr_str = repr(data)
        assert "NitroDataStore" in repr_str
        assert "name" in repr_str
        assert "Test" in repr_str

    def test_str(self):
        """Test __str__."""
        data = NitroDataStore({"name": "Test", "count": 42})
        str_output = str(data)
        parsed = json.loads(str_output)
        assert parsed == {"name": "Test", "count": 42}

    def test_str_formatted(self):
        """Test __str__ produces formatted JSON."""
        data = NitroDataStore({"site": {"name": "Test"}})
        str_output = str(data)
        assert "\n" in str_output
