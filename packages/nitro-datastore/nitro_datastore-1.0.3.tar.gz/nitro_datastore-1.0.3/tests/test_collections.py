"""Tests for collection operations and query builder."""

from nitro_datastore import NitroDataStore


class TestNitroDataStoreQueryBuilder:
    """Test query builder."""

    def test_query_where(self):
        """Test basic where filtering."""
        data = NitroDataStore(
            {
                "posts": [
                    {"title": "A", "published": True},
                    {"title": "B", "published": False},
                    {"title": "C", "published": True},
                ]
            }
        )
        results = data.query("posts").where(lambda x: x.get("published")).execute()
        assert len(results) == 2
        assert all(p["published"] for p in results)

    def test_query_sort(self):
        """Test sorting results."""
        data = NitroDataStore(
            {
                "posts": [
                    {"title": "C", "order": 3},
                    {"title": "A", "order": 1},
                    {"title": "B", "order": 2},
                ]
            }
        )
        results = data.query("posts").sort(key=lambda x: x.get("order")).execute()
        assert results[0]["title"] == "A"
        assert results[1]["title"] == "B"
        assert results[2]["title"] == "C"

    def test_query_sort_reverse(self):
        """Test reverse sorting."""
        data = NitroDataStore(
            {
                "posts": [
                    {"title": "A", "views": 100},
                    {"title": "B", "views": 300},
                    {"title": "C", "views": 200},
                ]
            }
        )
        results = (
            data.query("posts")
            .sort(key=lambda x: x.get("views"), reverse=True)
            .execute()
        )
        assert results[0]["title"] == "B"

    def test_query_limit(self):
        """Test limiting results."""
        data = NitroDataStore({"posts": [{"n": i} for i in range(10)]})
        results = data.query("posts").limit(3).execute()
        assert len(results) == 3

    def test_query_offset(self):
        """Test offsetting results."""
        data = NitroDataStore({"posts": [{"n": i} for i in range(10)]})
        results = data.query("posts").offset(5).execute()
        assert len(results) == 5
        assert results[0]["n"] == 5

    def test_query_chaining(self):
        """Test chaining multiple operations."""
        data = NitroDataStore(
            {
                "posts": [
                    {"title": "A", "published": True, "views": 100},
                    {"title": "B", "published": False, "views": 300},
                    {"title": "C", "published": True, "views": 200},
                    {"title": "D", "published": True, "views": 150},
                ]
            }
        )
        results = (
            data.query("posts")
            .where(lambda x: x.get("published"))
            .sort(key=lambda x: x.get("views"), reverse=True)
            .limit(2)
            .execute()
        )
        assert len(results) == 2
        assert results[0]["title"] == "C"
        assert results[1]["title"] == "D"

    def test_query_count(self):
        """Test counting results."""
        data = NitroDataStore(
            {"posts": [{"published": True}, {"published": False}, {"published": True}]}
        )
        count = data.query("posts").where(lambda x: x.get("published")).count()
        assert count == 2

    def test_query_first(self):
        """Test getting first result."""
        data = NitroDataStore({"posts": [{"title": "A"}, {"title": "B"}]})
        first = data.query("posts").first()
        assert first == {"title": "A"}

    def test_query_first_none(self):
        """Test first on empty results."""
        data = NitroDataStore({"posts": []})
        first = data.query("posts").first()
        assert first is None

    def test_query_pluck(self):
        """Test plucking field values."""
        data = NitroDataStore(
            {"posts": [{"title": "A", "views": 100}, {"title": "B", "views": 200}]}
        )
        titles = data.query("posts").pluck("title")
        assert titles == ["A", "B"]

    def test_query_group_by(self):
        """Test grouping results."""
        data = NitroDataStore(
            {
                "posts": [
                    {"title": "A", "category": "python"},
                    {"title": "B", "category": "web"},
                    {"title": "C", "category": "python"},
                ]
            }
        )
        groups = data.query("posts").group_by("category")
        assert len(groups["python"]) == 2
        assert len(groups["web"]) == 1


class TestNitroDataStoreFilterList:
    """Test filter_list utility."""

    def test_filter_list(self):
        """Test filtering a list."""
        data = NitroDataStore(
            {
                "posts": [
                    {"title": "A", "published": True},
                    {"title": "B", "published": False},
                    {"title": "C", "published": True},
                ]
            }
        )
        published = data.filter_list("posts", lambda p: p.get("published"))
        assert len(published) == 2
        assert all(p["published"] for p in published)

    def test_filter_list_not_list(self):
        """Test filter_list on non-list returns empty."""
        data = NitroDataStore({"value": "not a list"})
        result = data.filter_list("value", lambda x: True)
        assert result == []

    def test_filter_list_missing_path(self):
        """Test filter_list on missing path returns empty."""
        data = NitroDataStore({"other": "value"})
        result = data.filter_list("missing", lambda x: True)
        assert result == []
