# Nitro DataStore

A flexible, schema-free data store for JSON in Python. Access nested data with dot notation, dictionary style, or path strings.

```python
from nitro_datastore import NitroDataStore

data = NitroDataStore({'site': {'name': 'Nitro', 'url': 'https://nitro.sh'}})

data.site.name              # Dot notation
data['site']['name']        # Dictionary style
data.get('site.name')       # Path-based with defaults
```

No more `config.get('site', {}).get('theme', {}).get('color', '#000')`. Just `config.get('site.theme.color', '#000')`.

## Installation

```bash
pip install nitro-datastore
```

For AI coding assistants (Claude Code, etc.):

```bash
npx skills add nitrosh/nitro-datastore
```

## Quick Start

### Creating a DataStore

```python
# From a dictionary
data = NitroDataStore({'title': 'Hello', 'settings': {'theme': 'dark'}})

# From a JSON file
data = NitroDataStore.from_file('config.json')

# From a directory (auto-merges all JSON files alphabetically)
data = NitroDataStore.from_directory('data/')
```

### Reading & Writing

```python
# Get with defaults
name = data.get('user.name', 'Anonymous')

# Set (creates intermediate dicts automatically)
data.set('config.cache.ttl', 3600)

# Check existence
if data.has('user.email'):
    email = data.get('user.email')

# Delete
data.delete('user.temp_token')

# Merge another datastore
data.merge(other_data)
```

### Saving

```python
data.save('output.json', indent=2)
plain_dict = data.to_dict()
```

## Query Builder

Filter and transform collections with a chainable API:

```python
data = NitroDataStore({
    'posts': [
        {'title': 'Python Tips', 'views': 150, 'published': True},
        {'title': 'Web Dev', 'views': 200, 'published': True},
        {'title': 'Draft', 'views': 0, 'published': False}
    ]
})

# Filter, sort, limit
results = (data.query('posts')
    .where(lambda p: p.get('published'))
    .sort(key=lambda p: p.get('views'), reverse=True)
    .limit(10)
    .execute())

# Utilities
count = data.query('posts').where(lambda p: p.get('published')).count()
titles = data.query('posts').pluck('title')
by_category = data.query('posts').group_by('category')
first = data.query('posts').first()
```

## Path Discovery

Explore unknown data structures:

```python
# List all paths
paths = data.list_paths()

# Glob patterns (* = single segment, ** = any depth)
titles = data.find_paths('posts.*.title')
urls = data.find_paths('**.url')

# Find all occurrences of a key
all_urls = data.find_all_keys('url')

# Find values by predicate
emails = data.find_values(lambda v: isinstance(v, str) and '@' in v)
```

## Bulk Operations

```python
# Update all matching values
count = data.update_where(
    condition=lambda path, value: 'http://' in str(value),
    transform=lambda value: value.replace('http://', 'https://')
)

# Clean up
data.remove_nulls()
data.remove_empty()
```

## Transformations

Transformations return new instances (immutable):

```python
# Transform all values
upper = data.transform_all(lambda path, v: v.upper() if isinstance(v, str) else v)

# Transform all keys (e.g., kebab-case to snake_case)
snake = data.transform_keys(lambda k: k.replace('-', '_'))
```

## Comparison

```python
data1.equals(data2)  # True/False

diff = old.diff(new)
# {'added': {...}, 'removed': {...}, 'changed': {...}}
```

## Security

Built-in protections for file operations:

```python
# Path traversal protection
data = NitroDataStore.from_file(user_path, base_dir='/safe/directory')

# File size limits
data = NitroDataStore.from_file(path, max_size=10*1024*1024)
```

Also includes: path validation, circular reference detection.

## Common Gotchas

| Issue | Solution |
|-------|----------|
| Kebab-case keys (`user-name`) | Use `data['user-name']` instead of dot notation |
| Keys with dots (`key.name`) | Use `data['key.name']` - path methods treat dots as separators |
| Transform doesn't mutate | Assign the result: `data = data.transform_keys(...)` |

## Examples

See the [examples/](examples/) directory for comprehensive demos:

- `01_basic_operations.py` - Access patterns and CRUD
- `02_file_operations.py` - Load, save, directory merging
- `03_querying.py` - Query builder usage
- `04_path_operations.py` - Path discovery and patterns
- `05_bulk_operations.py` - Batch updates and cleanup
- `06_data_introspection.py` - describe(), stats(), flatten()
- `07_comparison.py` - diff() and equals()
- `08_comprehensive_example.py` - Real-world workflow
- `09_security_features.py` - Security protections

## Ecosystem

- **[nitro-ui](https://github.com/nitrosh/nitro-ui)** - Programmatic HTML generation
- **[nitro-cli](https://github.com/nitrosh/nitro-cli)** - Static site generator
- **[nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)** - Plugin system
- **[nitro-validate](https://github.com/nitrosh/nitro-validate)** - Data validation

## License

MIT License. See [LICENSE](LICENSE) for details.
