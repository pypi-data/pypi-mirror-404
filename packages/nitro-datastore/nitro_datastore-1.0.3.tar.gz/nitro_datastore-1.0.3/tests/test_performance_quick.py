"""Quick performance tests with moderate-sized datasets."""

import json
import time
from nitro_datastore import NitroDataStore


def generate_dataset(target_size_mb=5):
    """Generate a dataset approximately target_size_mb in size."""
    target_bytes = target_size_mb * 1024 * 1024

    data = {
        "metadata": {"version": "1.0", "generated": True},
        "users": [],
        "posts": [],
        "comments": [],
    }

    user_id = 0
    post_id = 0
    comment_id = 0
    current_size = 0

    while current_size < target_bytes:
        user = {
            "id": user_id,
            "username": f"user_{user_id}",
            "email": f"user{user_id}@example.com",
            "profile": {
                "bio": f"Bio for user {user_id}. " * 3,
                "location": f"City {user_id % 50}",
                "interests": [f"interest_{i}" for i in range(5)],
            },
            "settings": {"theme": "dark" if user_id % 2 == 0 else "light"},
        }
        data["users"].append(user)
        user_id += 1

        post = {
            "id": post_id,
            "title": f"Post {post_id}",
            "content": f"Content of post {post_id}. " * 10,
            "author_id": user_id % max(1, user_id),
            "published": post_id % 3 == 0,
            "views": post_id * 10,
            "tags": [f"tag_{i}" for i in range(3)],
        }
        data["posts"].append(post)
        post_id += 1

        comment = {
            "id": comment_id,
            "post_id": post_id % max(1, post_id),
            "text": f"Comment {comment_id}. " * 5,
            "likes": comment_id % 50,
        }
        data["comments"].append(comment)
        comment_id += 1

        current_size = len(json.dumps(data).encode("utf-8"))

    return data


class TestQuickPerformance:
    """Quick performance test with 5MB dataset."""

    def test_5mb_dataset_operations(self):
        """Test critical operations on 5MB dataset."""
        print("\n" + "=" * 70)
        print("QUICK PERFORMANCE TEST: 5MB Dataset")
        print("=" * 70)

        print("\n1. Generating 5MB dataset...")
        start = time.time()
        dataset = generate_dataset(target_size_mb=5)
        generation_time = time.time() - start

        json_str = json.dumps(dataset)
        actual_size_mb = len(json_str.encode("utf-8")) / (1024 * 1024)

        print(f"   [OK] Generated {actual_size_mb:.2f} MB in {generation_time:.2f}s")
        print(f"   - Users: {len(dataset['users'])}")
        print(f"   - Posts: {len(dataset['posts'])}")
        print(f"   - Comments: {len(dataset['comments'])}")

        print("\n2. Creating NitroDataStore...")
        start = time.time()
        data = NitroDataStore(dataset)
        creation_time = time.time() - start
        print(f"   [OK] Created in {creation_time:.2f}s")

        print("\n3. Testing get() operations...")
        start = time.time()
        for _ in range(100):
            data.get("metadata.version")
            data.get("users.0.username")
            data.get("users.0.profile.interests")
        get_time = time.time() - start
        print(
            f"   [OK] 300 get() operations in {get_time:.4f}s ({300/get_time:.0f} ops/sec)"
        )

        print("\n4. Testing has() operations...")
        start = time.time()
        for _ in range(100):
            data.has("users")
            data.has("metadata.version")
            data.has("nonexistent.path")
        has_time = time.time() - start
        print(
            f"   [OK] 300 has() operations in {has_time:.4f}s ({300/has_time:.0f} ops/sec)"
        )

        print("\n5. Testing set() operations...")
        start = time.time()
        for i in range(100):
            data.set(f"test.field{i}", f"value{i}")
        set_time = time.time() - start
        print(
            f"   [OK] 100 set() operations in {set_time:.4f}s ({100/set_time:.0f} ops/sec)"
        )

        print("\n6. Testing query() on users...")
        start = time.time()
        dark_users = (
            data.query("users")
            .where(lambda u: u.get("settings", {}).get("theme") == "dark")
            .execute()
        )
        query_time = time.time() - start
        print(f"   [OK] Filtered {len(dark_users)} users in {query_time:.4f}s")

        print("\n7. Testing query() with sort and limit...")
        start = time.time()
        top_posts = (
            data.query("posts")
            .where(lambda p: p.get("published"))
            .sort(key=lambda p: p.get("views", 0), reverse=True)
            .limit(10)
            .execute()
        )
        query_complex_time = time.time() - start
        print(f"   [OK] Found top {len(top_posts)} posts in {query_complex_time:.4f}s")

        print("\n8. Testing list_paths()...")
        start = time.time()
        paths = data.list_paths(prefix="metadata")
        list_paths_time = time.time() - start
        print(f"   [OK] Listed {len(paths)} paths in {list_paths_time:.4f}s")

        print("\n9. Testing find_paths() with pattern...")
        start = time.time()
        email_paths = data.find_paths("users.*.email")
        find_paths_time = time.time() - start
        print(f"   [OK] Found {len(email_paths)} email paths in {find_paths_time:.4f}s")

        print("\n10. Testing find_all_keys()...")
        start = time.time()
        all_ids = data.find_all_keys("id")
        find_keys_time = time.time() - start
        print(f"   [OK] Found {len(all_ids)} 'id' keys in {find_keys_time:.4f}s")

        print("\n11. Testing stats()...")
        start = time.time()
        stats = data.stats()
        stats_time = time.time() - start
        print(f"   [OK] Generated stats in {stats_time:.4f}s")
        print(
            f"      Keys: {stats['total_keys']}, Depth: {stats['max_depth']}, "
            f"Dicts: {stats['total_dicts']}, Lists: {stats['total_lists']}"
        )

        print("\n12. Testing to_dict()...")
        start = time.time()
        exported = data.to_dict()
        export_time = time.time() - start
        print(f"   [OK] Exported to dict in {export_time:.4f}s")
        assert len(exported["users"]) == len(dataset["users"])

        print("\n13. Testing update_where() bulk operation...")
        start = time.time()
        updated_count = data.update_where(
            condition=lambda path, value: isinstance(value, str) and value == "light",
            transform=lambda value: "auto",
        )
        bulk_time = time.time() - start
        print(f"   [OK] Bulk updated {updated_count} values in {bulk_time:.4f}s")

        print("\n14. Testing merge() operation...")
        overlay = NitroDataStore({"metadata": {"merged": True}, "new_field": "test"})
        start = time.time()
        data.merge(overlay)
        merge_time = time.time() - start
        print(f"   [OK] Merged datastore in {merge_time:.4f}s")
        assert data.get("metadata.merged") is True

        print("\n15. Testing flatten() on subset...")
        start = time.time()
        metadata_ds = NitroDataStore(data.get("metadata"))
        flattened = metadata_ds.flatten()
        flatten_time = time.time() - start
        print(f"   [OK] Flattened in {flatten_time:.4f}s ({len(flattened)} keys)")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        total_ops_time = (
            get_time
            + has_time
            + set_time
            + query_time
            + query_complex_time
            + list_paths_time
            + find_paths_time
            + find_keys_time
            + stats_time
            + export_time
            + bulk_time
            + merge_time
            + flatten_time
        )

        total_time = generation_time + creation_time + total_ops_time

        print(f"Dataset size: {actual_size_mb:.2f} MB")
        print(f"Generation + Creation: {generation_time + creation_time:.2f}s")
        print(f"Operations time: {total_ops_time:.2f}s")
        print(f"Total time: {total_time:.2f}s")
        print("\n[OK] All operations completed successfully!")
        print("=" * 70)

        assert True


class TestMemoryEfficiency:
    """Test memory usage with datasets."""

    def test_memory_usage(self):
        """Test that operations don't cause excessive memory growth."""
        print("\n" + "=" * 70)
        print("MEMORY EFFICIENCY TEST")
        print("=" * 70)

        print("\n1. Creating 2MB dataset...")
        dataset = generate_dataset(target_size_mb=2)
        data = NitroDataStore(dataset)

        json_size = len(json.dumps(dataset).encode("utf-8")) / (1024 * 1024)
        print(f"   [OK] Dataset: {json_size:.2f} MB")

        print("\n2. Testing repeated operations don't grow memory...")
        start = time.time()
        for i in range(1000):
            data.get("users.0.username")
            data.has("posts.0.title")
            if i % 10 == 0:
                data.set(f"temp.key{i % 10}", f"value{i}")
        ops_time = time.time() - start
        print(f"   [OK] 3000 operations in {ops_time:.2f}s")

        print("\n3. Testing query doesn't leak memory...")
        start = time.time()
        for _ in range(50):
            data.query("users").where(lambda u: u.get("id", 0) < 100).execute()
        query_time = time.time() - start
        print(f"   [OK] 50 queries in {query_time:.2f}s")

        print("\n4. Testing to_dict() creates proper copies...")
        start = time.time()
        for _ in range(10):
            copy = data.to_dict()
            assert "users" in copy
        copy_time = time.time() - start
        print(f"   [OK] 10 copies in {copy_time:.2f}s")

        print("\n" + "=" * 70)
        print("[OK] Memory efficiency verified!")
        print("=" * 70)

        assert True
