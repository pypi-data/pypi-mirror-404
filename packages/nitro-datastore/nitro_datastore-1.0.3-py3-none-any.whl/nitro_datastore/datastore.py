"""Flexible data store for managing JSON data files in Nitro projects."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Union

if TYPE_CHECKING:
    from nitro_datastore.query_builder import QueryBuilder

_GLOB_DOUBLE_WILDCARD_PLACEHOLDER = "___DOUBLE_WILDCARD___"
_GLOB_DOUBLE_WILDCARD_PATTERN = "**"
_GLOB_SINGLE_WILDCARD_PATTERN = "*"
_REGEX_DOUBLE_WILDCARD = r".*"
_REGEX_SINGLE_WILDCARD = r"[^.]+"


class NitroDataStore:
    """A flexible data store for accessing and manipulating JSON data.

    Supports multiple access patterns:
    - Dictionary-style: data['site']['name']
    - Dot notation: data.site.name
    - Path-based get: data.get('site.name', default='fallback')
    - Deep operations: set, delete, merge

    Important: Path-based methods (get, set, delete, has) use '.' as a separator.
    If your keys contain dots, use dictionary-style access instead:
        >>> data = NitroDataStore({'key.with.dots': 'value'})
        >>> data['key.with.dots']  # Use this
        'value'
        >>> data.get('key.with.dots')  # This will fail (treats as path)
        None

    Example:
        >>> data = NitroDataStore({'site': {'name': 'My Site', 'url': 'example.com'}})
        >>> data.site.name
        'My Site'
        >>> data['site']['url']
        'example.com'
        >>> data.get('site.name')
        'My Site'
        >>> data.get('missing.key', 'default')
        'default'
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Initialize the data store.

        Args:
            data: Initial data dictionary. Defaults to empty dict.
        """
        self._data = data if data is not None else {}
        self._paths_cache: Dict[tuple, List[str]] = {}

    @classmethod
    def from_file(
        cls,
        file_path: Union[str, Path],
        base_dir: Optional[Union[str, Path]] = None,
        max_size: Optional[int] = None,
    ) -> "NitroDataStore":
        """Load data from a JSON file.

        Args:
            file_path: Path to JSON file
            base_dir: Optional base directory to restrict file access.
                      If provided, file_path must be within this directory.
            max_size: Optional maximum file size in bytes.
                      If provided, rejects files larger than this size.

        Returns:
            NitroDataStore instance with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file_path escapes base_dir (when base_dir is set)
                        or if file exceeds max_size (when max_size is set)
            json.JSONDecodeError: If file contains invalid JSON

        Security:
            When base_dir is provided, validates that the resolved file path
            is within the base directory, preventing path traversal attacks.
            When max_size is provided, prevents loading files that could
            cause out-of-memory errors.

        Example:
            >>> # Without validation (backward compatible)
            >>> data = NitroDataStore.from_file('config.json')

            >>> # With path validation (secure)
            >>> data = NitroDataStore.from_file('config.json', base_dir='/app/data')

            >>> # With size limit (10MB max)
            >>> data = NitroDataStore.from_file('config.json', max_size=10*1024*1024)
        """
        path = Path(file_path)

        if base_dir is not None:
            base_path = Path(base_dir).resolve()
            resolved_path = path.resolve()

            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                raise ValueError(
                    f"Path traversal detected: '{file_path}' resolves to '{resolved_path}' "
                    f"which is outside base directory '{base_path}'"
                )

            path = resolved_path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if max_size is not None:
            file_size = path.stat().st_size
            if file_size > max_size:
                size_mb = file_size / (1024 * 1024)
                limit_mb = max_size / (1024 * 1024)
                raise ValueError(
                    f"File size ({size_mb:.2f} MB) exceeds maximum allowed size ({limit_mb:.2f} MB)"
                )

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(data)

    @classmethod
    def from_directory(
        cls,
        directory: Union[str, Path],
        pattern: str = "*.json",
        base_dir: Optional[Union[str, Path]] = None,
        max_size: Optional[int] = None,
        strict: bool = False,
    ) -> "NitroDataStore":
        """Load and merge all JSON files from a directory.

        Files are merged in alphabetical order. Later files override earlier ones.

        Args:
            directory: Path to directory containing JSON files
            pattern: Glob pattern for JSON files (default: "*.json")
            base_dir: Optional base directory to restrict directory access.
                      If provided, directory must be within this base directory.
            max_size: Optional maximum file size in bytes. If provided, files
                      exceeding this size will raise ValueError.
            strict: If True, raise exceptions for invalid JSON files instead of
                    skipping them silently. Default is False for backward compatibility.

        Returns:
            NitroDataStore instance with merged data

        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If directory escapes base_dir (when base_dir is set) or
                        if any file exceeds max_size (when max_size is set)
            json.JSONDecodeError: If strict=True and a file contains invalid JSON
            IOError: If strict=True and a file cannot be read

        Security:
            - When base_dir is provided, validates that the resolved directory path
              is within the base directory, preventing path traversal attacks.
            - When max_size is provided, validates each file size before loading,
              preventing out-of-memory issues from excessively large files.

        Example:
            >>> # Without validation (backward compatible)
            >>> data = NitroDataStore.from_directory('data/')

            >>> # With path validation (secure)
            >>> data = NitroDataStore.from_directory('configs/', base_dir='/app/data')

            >>> # With size limits (10 MB max per file)
            >>> data = NitroDataStore.from_directory('configs/', max_size=10*1024*1024)

            >>> # Strict mode - fail on invalid JSON
            >>> data = NitroDataStore.from_directory('configs/', strict=True)
        """
        dir_path = Path(directory)

        if base_dir is not None:
            base_path = Path(base_dir).resolve()
            resolved_dir = dir_path.resolve()

            try:
                resolved_dir.relative_to(base_path)
            except ValueError:
                raise ValueError(
                    f"Path traversal detected: '{directory}' resolves to '{resolved_dir}' "
                    f"which is outside base directory '{base_path}'"
                )

            dir_path = resolved_dir

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        merged_data: Dict[str, Any] = {}

        # Sort files for predictable merge order
        json_files = sorted(dir_path.glob(pattern))

        for file_path in json_files:
            try:
                if max_size is not None:
                    file_size = file_path.stat().st_size
                    if file_size > max_size:
                        size_mb = file_size / (1024 * 1024)
                        limit_mb = max_size / (1024 * 1024)
                        raise ValueError(
                            f"File size ({size_mb:.2f} MB) exceeds maximum allowed size "
                            f"({limit_mb:.2f} MB) for file: {file_path}"
                        )

                with open(file_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    merged_data = cls._deep_merge(merged_data, file_data)
            except (json.JSONDecodeError, IOError):
                if strict:
                    raise
                continue

        return cls(merged_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value using dot notation path.

        Args:
            key: Dot-separated path (e.g., 'site.name' or 'settings.theme.color')
            default: Default value if key not found

        Returns:
            The value at the path, or default if not found

        Raises:
            ValueError: If key is empty, whitespace-only, or has empty segments

        Note:
            If your key contains dots (e.g., 'key.with.dots'), use dictionary-style
            access instead: data['key.with.dots']. This method treats dots as path
            separators and cannot access literal keys containing dots.

        Example:
            >>> data = NitroDataStore({'site': {'name': 'My Site'}})
            >>> data.get('site.name')
            'My Site'
            >>> data.get('site.title', 'Untitled')
            'Untitled'
        """
        self._validate_path(key)

        if "." not in key:
            return self._data.get(key, default)

        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a value using dot notation path.

        Creates nested dictionaries as needed.

        Args:
            key: Dot-separated path (e.g., 'site.name')
            value: Value to set

        Raises:
            ValueError: If key is empty, whitespace-only, or has empty segments

        Example:
            >>> data = NitroDataStore()
            >>> data.set('site.name', 'My Site')
            >>> data.get('site.name')
            'My Site'
        """
        self._validate_path(key)

        if "." not in key:
            self._data[key] = value
            self._invalidate_cache()
            return

        keys = key.split(".")
        current = self._data

        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                # Can't traverse non-dict
                current[k] = {}
            current = current[k]

        # Set the final value
        current[keys[-1]] = value
        self._invalidate_cache()

    def delete(self, key: str) -> bool:
        """Delete a value using dot notation path.

        Args:
            key: Dot-separated path

        Returns:
            True if key existed and was deleted, False otherwise

        Raises:
            ValueError: If key is empty, whitespace-only, or has empty segments

        Example:
            >>> data = NitroDataStore({'site': {'name': 'My Site'}})
            >>> data.delete('site.name')
            True
            >>> data.delete('site.name')
            False
        """
        self._validate_path(key)

        if "." not in key:
            if key in self._data:
                del self._data[key]
                self._invalidate_cache()
                return True
            return False

        keys = key.split(".")
        current = self._data

        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]

        # Delete the final key
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            self._invalidate_cache()
            return True

        return False

    def has(self, key: str) -> bool:
        """Check if a key exists using dot notation path.

        Args:
            key: Dot-separated path

        Returns:
            True if key exists, False otherwise

        Raises:
            ValueError: If key is empty, whitespace-only, or has empty segments
        """
        self._validate_path(key)

        if "." not in key:
            return key in self._data

        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False

        return True

    def merge(self, other: Union["NitroDataStore", Dict[str, Any]]) -> None:
        """Deep merge another data store or dictionary into this one.

        Args:
            other: Another NitroDataStore or dict to merge in
        """
        if isinstance(other, NitroDataStore):
            other_data = other._data
        else:
            other_data = other

        self._data = self._deep_merge(self._data, other_data)
        self._invalidate_cache()

    def to_dict(self) -> Dict[str, Any]:
        """Export data as a plain dictionary.

        Returns:
            A deep copy of the internal data dictionary
        """
        return self._deep_copy(self._data)

    def save(self, file_path: Union[str, Path], indent: int = 2) -> None:
        """Save data to a JSON file.

        Args:
            file_path: Path to save JSON file
            indent: JSON indentation (default: 2)
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=indent, ensure_ascii=False)

    def keys(self) -> Iterator[str]:
        """Get top-level keys.

        Returns:
            Iterator of top-level keys
        """
        return iter(self._data.keys())

    def values(self) -> Iterator[Any]:
        """Get top-level values.

        Returns:
            Iterator of top-level values
        """
        return iter(self._data.values())

    def items(self) -> Iterator[tuple]:
        """Get top-level key-value pairs.

        Returns:
            Iterator of (key, value) tuples
        """
        return iter(self._data.items())

    def flatten(self, separator: str = ".") -> Dict[str, Any]:
        """Flatten nested dictionary to dot-notation keys.

        Args:
            separator: Key separator (default: '.')

        Returns:
            Flattened dictionary with dot-notation keys

        Example:
            >>> data = NitroDataStore({'site': {'name': 'My Site', 'settings': {'theme': 'dark'}}})
            >>> data.flatten()
            {'site.name': 'My Site', 'site.settings.theme': 'dark'}
        """

        def _flatten_dict(d: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
            items: List[tuple] = []
            for k, v in d.items():
                new_key = f"{parent_key}{separator}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(_flatten_dict(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        return _flatten_dict(self._data)

    def list_paths(self, prefix: str = "", separator: str = ".") -> List[str]:
        """List all paths in the data structure.

        Args:
            prefix: Optional prefix to filter paths
            separator: Path separator (default: '.')

        Returns:
            List of all paths as dot-notation strings

        Note:
            Results are cached for performance. Cache is invalidated on data mutations.

        Example:
            >>> data = NitroDataStore({'site': {'name': 'Test', 'url': 'example.com'}})
            >>> data.list_paths()
            ['site.name', 'site.url']
        """
        cache_key = (separator, prefix)

        if cache_key in self._paths_cache:
            return self._paths_cache[cache_key].copy()

        paths = []

        def _collect_paths(obj: Any, current_path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = (
                        f"{current_path}{separator}{key}" if current_path else key
                    )
                    paths.append(new_path)
                    _collect_paths(value, new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    new_path = (
                        f"{current_path}{separator}{idx}" if current_path else str(idx)
                    )
                    paths.append(new_path)
                    _collect_paths(item, new_path)

        _collect_paths(self._data)

        if prefix:
            filtered_paths = [p for p in paths if p.startswith(prefix)]
            self._paths_cache[cache_key] = filtered_paths.copy()
            return filtered_paths

        self._paths_cache[cache_key] = paths.copy()
        return paths

    def find_paths(self, pattern: str, separator: str = ".") -> List[str]:
        """Find paths matching a glob-like pattern.

        Supports wildcards:
        - '*' matches any single path segment
        - '**' matches any number of path segments

        Args:
            pattern: Glob pattern (e.g., '*.title', 'posts.*.author')
            separator: Path separator (default: '.')

        Returns:
            List of matching paths

        Example:
            >>> data = NitroDataStore({'posts': [{'title': 'A'}, {'title': 'B'}]})
            >>> data.find_paths('posts.*.title')
            ['posts.0.title', 'posts.1.title']
        """
        import re

        all_paths = self.list_paths(separator=separator)

        regex_pattern = pattern.replace(".", r"\.")
        regex_pattern = regex_pattern.replace(
            _GLOB_DOUBLE_WILDCARD_PATTERN, _GLOB_DOUBLE_WILDCARD_PLACEHOLDER
        )
        regex_pattern = regex_pattern.replace(
            _GLOB_SINGLE_WILDCARD_PATTERN, _REGEX_SINGLE_WILDCARD
        )
        regex_pattern = regex_pattern.replace(
            _GLOB_DOUBLE_WILDCARD_PLACEHOLDER, _REGEX_DOUBLE_WILDCARD
        )
        regex_pattern = f"^{regex_pattern}$"

        regex = re.compile(regex_pattern)
        return [p for p in all_paths if regex.match(p)]

    def get_many(self, paths: List[str]) -> Dict[str, Any]:
        """Get multiple values by their paths.

        Args:
            paths: List of dot-notation paths

        Returns:
            Dictionary mapping paths to values (None if not found)

        Example:
            >>> data = NitroDataStore({'site': {'name': 'Test', 'url': 'example.com'}})
            >>> data.get_many(['site.name', 'site.url', 'missing'])
            {'site.name': 'Test', 'site.url': 'example.com', 'missing': None}
        """
        return {path: self.get(path) for path in paths}

    def find_all_keys(self, key_name: str) -> Dict[str, Any]:
        """Find all occurrences of a key name anywhere in the structure.

        Args:
            key_name: Key name to search for

        Returns:
            Dictionary mapping paths to values for all matching keys

        Example:
            >>> data = NitroDataStore({'site': {'url': 'a.com'}, 'social': {'url': 'b.com'}})
            >>> data.find_all_keys('url')
            {'site.url': 'a.com', 'social.url': 'b.com'}
        """
        results = {}

        def _search(obj: Any, current_path: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_path = f"{current_path}.{k}" if current_path else k
                    if k == key_name:
                        results[new_path] = v
                    _search(v, new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    new_path = f"{current_path}.{idx}" if current_path else str(idx)
                    _search(item, new_path)

        _search(self._data)
        return results

    def find_values(self, predicate: Callable[[Any], bool]) -> Dict[str, Any]:
        """Find all values matching a predicate function.

        Args:
            predicate: Function that takes a value and returns True/False

        Returns:
            Dictionary mapping paths to values for all matching values

        Example:
            >>> data = NitroDataStore({'images': {'hero': 'pic.jpg', 'count': 5}})
            >>> data.find_values(lambda v: isinstance(v, str) and v.endswith('.jpg'))
            {'images.hero': 'pic.jpg'}
        """
        results = {}

        def _search(obj: Any, current_path: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_path = f"{current_path}.{k}" if current_path else k
                    if predicate(v):
                        results[new_path] = v
                    _search(v, new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    new_path = f"{current_path}.{idx}" if current_path else str(idx)
                    if predicate(item):
                        results[new_path] = item
                    _search(item, new_path)

        _search(self._data)
        return results

    def update_where(
        self, condition: Callable[[str, Any], bool], transform: Callable[[Any], Any]
    ) -> int:
        """Update all values matching a condition.

        Args:
            condition: Function(path, value) -> bool
            transform: Function(value) -> new_value

        Returns:
            Number of values updated

        Example:
            >>> data = NitroDataStore({'urls': ['http://a.com', 'https://b.com']})
            >>> count = data.update_where(
            ...     lambda p, v: isinstance(v, str) and 'http://' in v,
            ...     lambda v: v.replace('http://', 'https://')
            ... )
        """
        count = 0

        def _update(obj: Any, current_path: str = "") -> Any:
            nonlocal count
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    new_path = f"{current_path}.{k}" if current_path else k
                    if condition(new_path, v):
                        result[k] = transform(v)
                        count += 1
                    else:
                        result[k] = _update(v, new_path)
                return result
            elif isinstance(obj, list):
                result = []
                for idx, item in enumerate(obj):
                    new_path = f"{current_path}.{idx}" if current_path else str(idx)
                    if condition(new_path, item):
                        result.append(transform(item))
                        count += 1
                    else:
                        result.append(_update(item, new_path))
                return result
            else:
                return obj

        self._data = _update(self._data)
        self._invalidate_cache()
        return count

    def remove_nulls(self) -> int:
        """Remove all None values from the data structure.

        Returns:
            Number of None values removed

        Example:
            >>> data = NitroDataStore({'a': 1, 'b': None, 'c': {'d': None}})
            >>> data.remove_nulls()
            2
            >>> data.to_dict()
            {'a': 1, 'c': {}}
        """
        count = 0

        def _remove(obj: Any) -> Any:
            nonlocal count
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    if v is None:
                        count += 1
                    else:
                        result[k] = _remove(v)
                return result
            elif isinstance(obj, list):
                result = []
                for item in obj:
                    if item is None:
                        count += 1
                    else:
                        result.append(_remove(item))
                return result
            else:
                return obj

        self._data = _remove(self._data)
        self._invalidate_cache()
        return count

    def remove_empty(self) -> int:
        """Remove all empty dicts and lists from the data structure.

        Returns:
            Number of empty containers removed

        Example:
            >>> data = NitroDataStore({'a': {}, 'b': [], 'c': {'d': 1}})
            >>> data.remove_empty()
            2
            >>> data.to_dict()
            {'c': {'d': 1}}
        """
        count = 0

        def _is_empty_container(obj: Any) -> bool:
            return isinstance(obj, (dict, list)) and len(obj) == 0

        def _remove(obj: Any) -> Any:
            nonlocal count
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    cleaned = _remove(v)
                    if _is_empty_container(cleaned):
                        count += 1
                    else:
                        result[k] = cleaned
                return result
            elif isinstance(obj, list):
                result = []
                for item in obj:
                    cleaned = _remove(item)
                    if _is_empty_container(cleaned):
                        count += 1
                    else:
                        result.append(cleaned)
                return result
            else:
                return obj

        self._data = _remove(self._data)
        self._invalidate_cache()
        return count

    def describe(self) -> Dict[str, Any]:
        """Get a structural description of the data.

        Returns:
            Dictionary describing the structure

        Example:
            >>> data = NitroDataStore({'posts': [{'title': 'A'}], 'count': 5})
            >>> data.describe()
            {'posts': {'type': 'list', 'length': 1, 'item_types': ['dict']},
             'count': {'type': 'int', 'value': 5}}
        """

        def _describe_value(obj: Any) -> Dict[str, Any]:
            if isinstance(obj, dict):
                return {
                    "type": "dict",
                    "keys": list(obj.keys()),
                    "structure": {k: _describe_value(v) for k, v in obj.items()},
                }
            elif isinstance(obj, list):
                item_types = list(set(type(item).__name__ for item in obj))
                return {"type": "list", "length": len(obj), "item_types": item_types}
            else:
                return {
                    "type": type(obj).__name__,
                    "value": (
                        obj
                        if not isinstance(obj, (str, int, float, bool))
                        or len(str(obj)) < 50
                        else f"{str(obj)[:47]}..."
                    ),
                }

        return _describe_value(self._data).get("structure", {})

    def stats(self) -> Dict[str, int]:
        """Get statistics about the data structure.

        Returns:
            Dictionary with statistics

        Example:
            >>> data = NitroDataStore({'a': {'b': {'c': 1}}})
            >>> data.stats()
            {'total_keys': 3, 'max_depth': 3, 'total_dicts': 3, 'total_lists': 0, 'total_values': 1}
        """
        stats = {
            "total_keys": 0,
            "max_depth": 0,
            "total_dicts": 0,
            "total_lists": 0,
            "total_values": 0,
        }

        def _analyze(obj: Any, depth: int = 0) -> None:
            stats["max_depth"] = max(stats["max_depth"], depth)

            if isinstance(obj, dict):
                stats["total_dicts"] += 1
                stats["total_keys"] += len(obj)
                for v in obj.values():
                    _analyze(v, depth + 1)
            elif isinstance(obj, list):
                stats["total_lists"] += 1
                for item in obj:
                    _analyze(item, depth + 1)
            else:
                stats["total_values"] += 1

        _analyze(self._data)
        return stats

    def query(self, path: str) -> "QueryBuilder":
        """Start a query builder for filtering and transforming data.

        Args:
            path: Path to the collection to query

        Returns:
            QueryBuilder instance

        Example:
            >>> data = NitroDataStore({'posts': [{'title': 'A', 'published': True}]})
            >>> results = data.query('posts').where(lambda x: x.get('published')).execute()
        """
        from nitro_datastore.query_builder import QueryBuilder

        value = self.get(path)
        return QueryBuilder(value if isinstance(value, list) else [])

    def transform_all(self, transform: Callable[[str, Any], Any]) -> "NitroDataStore":
        """Create a new datastore with all values transformed.

        Args:
            transform: Function(path, value) -> new_value

        Returns:
            New NitroDataStore with transformed values

        Example:
            >>> data = NitroDataStore({'name': 'test', 'title': 'hello'})
            >>> upper = data.transform_all(lambda p, v: v.upper() if isinstance(v, str) else v)
            >>> upper.name
            'TEST'
        """

        def _transform(obj: Any, current_path: str = "") -> Any:
            if isinstance(obj, dict):
                return {
                    k: _transform(v, f"{current_path}.{k}" if current_path else k)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [
                    _transform(
                        item, f"{current_path}.{idx}" if current_path else str(idx)
                    )
                    for idx, item in enumerate(obj)
                ]
            else:
                return transform(current_path, obj)

        return NitroDataStore(_transform(self._data))

    def transform_keys(self, transform: Callable[[str], str]) -> "NitroDataStore":
        """Create a new datastore with all keys transformed.

        Args:
            transform: Function(key) -> new_key

        Returns:
            New NitroDataStore with transformed keys

        Example:
            >>> data = NitroDataStore({'first-name': 'John', 'last-name': 'Doe'})
            >>> snake = data.transform_keys(lambda k: k.replace('-', '_'))
            >>> snake.first_name
            'John'
        """

        def _transform(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {transform(k): _transform(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_transform(item) for item in obj]
            else:
                return obj

        return NitroDataStore(_transform(self._data))

    def diff(self, other: Union["NitroDataStore", Dict[str, Any]]) -> Dict[str, Any]:
        """Compare this datastore with another and return differences.

        Args:
            other: Another NitroDataStore or dict to compare with

        Returns:
            Dictionary with 'added', 'removed', and 'changed' keys

        Example:
            >>> data1 = NitroDataStore({'a': 1, 'b': 2})
            >>> data2 = NitroDataStore({'a': 1, 'b': 3, 'c': 4})
            >>> diff = data1.diff(data2)
            >>> diff['changed']
            {'b': {'old': 2, 'new': 3}}
            >>> diff['added']
            {'c': 4}
        """
        if isinstance(other, NitroDataStore):
            other_data = other._data
        else:
            other_data = other

        added = {}
        removed = {}
        changed = {}

        other_store = NitroDataStore(other_data)

        self_paths = set(self.list_paths())
        other_paths = set(other_store.list_paths())

        for path in other_paths - self_paths:
            added[path] = other_store.get(path)

        for path in self_paths - other_paths:
            removed[path] = self.get(path)

        for path in self_paths & other_paths:
            self_val = self.get(path)
            other_val = other_store.get(path)
            if self_val != other_val:
                changed[path] = {"old": self_val, "new": other_val}

        return {"added": added, "removed": removed, "changed": changed}

    def equals(self, other: Union["NitroDataStore", Dict[str, Any]]) -> bool:
        """Check if this datastore is equal to another.

        Args:
            other: Another NitroDataStore or dict

        Returns:
            True if equal, False otherwise

        Example:
            >>> data1 = NitroDataStore({'a': 1})
            >>> data2 = NitroDataStore({'a': 1})
            >>> data1.equals(data2)
            True
        """
        if isinstance(other, NitroDataStore):
            other_data = other._data
        else:
            other_data = other

        return self._data == other_data

    def __eq__(self, other: Any) -> bool:
        """Equality comparison using == operator.

        Args:
            other: Another NitroDataStore or dict to compare with

        Returns:
            True if equal, False otherwise

        Example:
            >>> data1 = NitroDataStore({'a': 1})
            >>> data2 = NitroDataStore({'a': 1})
            >>> data1 == data2
            True
        """
        if not isinstance(other, (NitroDataStore, dict)):
            return NotImplemented
        return self.equals(other)

    def filter_list(self, path: str, predicate: Callable[[Any], bool]) -> List[Any]:
        """Filter a list at the given path.

        Args:
            path: Path to the list
            predicate: Function(item) -> bool

        Returns:
            Filtered list

        Example:
            >>> data = NitroDataStore({'posts': [{'published': True}, {'published': False}]})
            >>> published = data.filter_list('posts', lambda p: p.get('published'))
            >>> len(published)
            1
        """
        value = self.get(path)
        if not isinstance(value, list):
            return []
        return [item for item in value if predicate(item)]

    def _wrap_value(self, value: Any) -> Any:
        """Wrap dicts in NitroDataStore, including dicts inside lists."""
        if isinstance(value, dict):
            return NitroDataStore(value)
        elif isinstance(value, list):
            return [self._wrap_value(item) for item in value]
        return value

    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access: data['key']"""
        return self._wrap_value(self._data[key])

    def __setitem__(self, key: str, value: Any) -> None:
        """Dictionary-style assignment: data['key'] = value"""
        self._data[key] = value
        self._invalidate_cache()

    def __delitem__(self, key: str) -> None:
        """Dictionary-style deletion: del data['key']"""
        del self._data[key]
        self._invalidate_cache()

    def __contains__(self, key: str) -> bool:
        """'in' operator: 'key' in data"""
        return key in self._data

    def __getattr__(self, name: str) -> Any:
        """Dot notation access: data.key"""
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        if name in self._data:
            return self._wrap_value(self._data[name])

        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Dot notation assignment: data.key = value"""
        if name.startswith("_"):
            # Allow setting private attributes normally
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self._invalidate_cache()

    def __len__(self) -> int:
        """len(data) - returns number of top-level keys"""
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        """Iterate over top-level keys: for key in data"""
        return iter(self._data)

    def __repr__(self) -> str:
        """String representation"""
        return f"NitroDataStore({self._data!r})"

    def __str__(self) -> str:
        """Human-readable string"""
        return json.dumps(self._data, indent=2, ensure_ascii=False)

    def __copy__(self) -> "NitroDataStore":
        """Shallow copy support for copy.copy()"""
        return NitroDataStore(self._data.copy())

    def __deepcopy__(self, memo: Dict[int, Any]) -> "NitroDataStore":
        """Deep copy support for copy.deepcopy()"""
        return NitroDataStore(self._deep_copy(self._data))

    def _invalidate_cache(self) -> None:
        """Invalidate cached paths when data changes."""
        self._paths_cache.clear()

    @staticmethod
    def _validate_path(path: str) -> None:
        """Validate a dot-notation path string.

        Args:
            path: Dot-separated path to validate

        Raises:
            ValueError: If path is invalid (empty, whitespace-only, or has empty segments)

        Examples of invalid paths:
            - '' (empty string)
            - '   ' (whitespace only)
            - '.' (single dot)
            - '..' (double dot)
            - 'foo.' (trailing dot)
            - '.foo' (leading dot)
            - 'foo..bar' (consecutive dots)
        """
        if not path or not path.strip():
            raise ValueError("Path cannot be empty or whitespace-only")

        if "." in path:
            segments = path.split(".")
            for segment in segments:
                if not segment or not segment.strip():
                    raise ValueError(
                        f"Path '{path}' contains empty segments. "
                        "Paths cannot have leading, trailing, or consecutive dots."
                    )

    @staticmethod
    def _deep_merge(
        base: Dict[str, Any],
        overlay: Dict[str, Any],
        seen: Optional[Dict[int, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries with circular reference protection.

        Args:
            base: Base dictionary
            overlay: Dictionary to merge on top
            seen: Dictionary tracking already merged objects by id

        Returns:
            Merged dictionary

        Raises:
            ValueError: If a circular reference is detected
        """
        if seen is None:
            seen = {}

        base_id = id(base)

        if base_id in seen:
            raise ValueError(
                "Circular reference detected in base dictionary during deep merge"
            )

        seen[base_id] = True

        try:
            result = base.copy()

            for key, value in overlay.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = NitroDataStore._deep_merge(result[key], value, seen)
                else:
                    result[key] = value

            del seen[base_id]
            return result
        except Exception:
            if base_id in seen:
                del seen[base_id]
            raise

    @staticmethod
    def _deep_copy(obj: Any, seen: Optional[Dict[int, Any]] = None) -> Any:
        """
        Deep copy an object (dict/list/primitive) with circular reference protection.

        Args:
            obj: Object to copy
            seen: Dictionary tracking already copied objects by id

        Returns:
            Deep copy of the object

        Raises:
            ValueError: If a circular reference is detected
        """
        if seen is None:
            seen = {}

        if isinstance(obj, (dict, list)):
            obj_id = id(obj)

            if obj_id in seen:
                raise ValueError("Circular reference detected during deep copy")

            seen[obj_id] = True

            try:
                if isinstance(obj, dict):
                    result = {
                        k: NitroDataStore._deep_copy(v, seen) for k, v in obj.items()
                    }
                else:
                    result = [NitroDataStore._deep_copy(item, seen) for item in obj]

                del seen[obj_id]
                return result
            except Exception:
                if obj_id in seen:
                    del seen[obj_id]
                raise
        else:
            return obj
