"""Nitro DataStore - Flexible data store for managing JSON data.

A powerful Python library for working with JSON data files. Provides multiple
access patterns (dot notation, dictionary-style, path-based), advanced querying,
and data manipulation tools.

Example:
    >>> from nitro_datastore import NitroDataStore
    >>> data = NitroDataStore({'site': {'name': 'My Site', 'url': 'example.com'}})
    >>> data.site.name  # Dot notation
    'My Site'
    >>> data['site']['url']  # Dictionary access
    'example.com'
    >>> data.get('site.name')  # Path-based access
    'My Site'
"""

from nitro_datastore.datastore import NitroDataStore
from nitro_datastore.query_builder import QueryBuilder

__version__ = "1.0.2"
__all__ = ["NitroDataStore", "QueryBuilder"]
