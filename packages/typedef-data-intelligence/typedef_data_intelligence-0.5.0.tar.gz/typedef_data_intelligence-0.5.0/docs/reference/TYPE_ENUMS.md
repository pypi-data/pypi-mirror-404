# Type-Safe Backend Enums

This document explains the type-safe enum system for backend types.

## Overview

To prevent typos and improve type safety, all backend types are defined as enums:

- **`LineageStorageType`** - For lineage metadata storage (FalkorDB, FalkorDBLite)
- **`DataBackendType`** - For data warehouse queries (DuckDB, Snowflake, etc.)

## LineageStorageType

Located in `src/lineage/backends/types.py`

### Available Types

```python
from lineage.backends.types import LineageStorageType

LineageStorageType.FALKORDB       # "falkordb" - FalkorDB (production)
LineageStorageType.FALKORDBLITE   # "falkordblite" - FalkorDBLite (default, embedded)
```

### Usage

**With Factory Functions:**

```python
from lineage.backends.lineage.factory import create_storage
from lineage.backends.types import LineageStorageType

# Using enum (type-safe, IDE autocomplete)
storage = create_storage(backend=LineageStorageType.FALKORDB)

# Using string (still works, validated at runtime)
storage = create_storage(backend="falkordb")
```

**In Config Files:**

```yaml
# Use the string value in YAML
backend: falkordb
host: localhost
port: 6379
```

**Getting All Types:**

```python
from lineage.backends.types import LineageStorageType

# List all backend types
backends = LineageStorageType.list_values()
# Returns: ['falkordb', 'falkordblite']

# Convert string to enum (with validation)
backend = LineageStorageType.from_string("falkordb")
# Returns: LineageStorageType.FALKORDB

# Invalid backend raises helpful error
backend = LineageStorageType.from_string("invalid")
# Raises: ValueError: Unknown lineage storage type: 'invalid'.
#         Valid types: falkordb, falkordblite
```

### Type Safety Benefits

**Before (string literals, error-prone):**

```python
# Easy to make typos
storage = create_storage(backend="flakordb")  # Typo! Runtime error

# No IDE autocomplete
backend = "falkord"  # Typo! Won't catch until runtime

# Hard to discover valid backends
# (have to read docs or source code)
```

**After (type-safe enums):**

```python
from lineage.backends.types import LineageStorageType

# IDE autocomplete shows all options
storage = create_storage(backend=LineageStorageType.FALKORDB)

# Type checker catches typos at development time
backend = LineageStorageType.FLAKORDB  # AttributeError in IDE!

# Easy to discover valid backends
backends = LineageStorageType.list_values()
```

## DataBackendType

Located in `src/lineage/backends/types.py`

### Available Types

```python
from lineage.backends.types import DataBackendType

DataBackendType.DUCKDB      # "duckdb" - DuckDB (default)
DataBackendType.SNOWFLAKE   # "snowflake" - Snowflake
DataBackendType.BIGQUERY    # "bigquery" - BigQuery (future)
```

### Usage

**With Data Backend:**

```python
from lineage.backends.types import DataBackendType
from lineage.backends.data_query.duckdb_backend import DuckDBBackend

# Type-safe backend type
backend = DuckDBBackend(
    db_path="data.duckdb",
    backend_type=DataBackendType.DUCKDB  # Optional, inferred
)

# Or just use string
backend_type_str = "duckdb"
```

**Getting All Types:**

```python
from lineage.backends.types import DataBackendType

# List all data backend types
backends = DataBackendType.list_values()
# Returns: ['duckdb', 'snowflake', 'bigquery']

# Convert string to enum (with validation)
backend = DataBackendType.from_string("duckdb")
# Returns: DataBackendType.DUCKDB
```

## Implementation Details

### String Enum Inheritance

Both enums inherit from `str` and `Enum`:

```python
class LineageStorageType(str, Enum):
    FALKORDB = "falkordb"
```

This allows:

- **Direct string comparisons**: `backend == "falkordb"` works
- **JSON serialization**: Enums serialize to strings automatically
- **Type safety**: IDE and type checkers understand the type
- **Backwards compatibility**: Can accept either enum or string

### Validation

All enum values are validated:

```python
# In config.py
backend_type = LineageStorageType.from_string(backend_str)
# Raises helpful ValueError if invalid

# In get_default_config()
backend_type = LineageStorageType.from_string(str(backend))
# Validates before creating config
```

### Error Messages

Enums provide helpful error messages:

```python
>>> LineageStorageType.from_string("invalid")
ValueError: Unknown lineage storage type: 'invalid'.
Valid types: falkordb, falkordblite

>>> DataBackendType.from_string("invalid")
ValueError: Unknown data backend type: 'invalid'.
Valid types: duckdb, snowflake, bigquery
```

## Migration Guide

### Existing Code

No changes required! Existing string-based code continues to work:

```python
# Still works (validated at runtime)
storage = create_storage(backend="falkordb")
```

### New Code

Use enums for type safety:

```python
from lineage.backends.lineage.factory import create_storage
from lineage.backends.types import LineageStorageType

# Recommended: Use enum
storage = create_storage(backend=LineageStorageType.FALKORDB)

# Gets IDE autocomplete, type checking, and validation
```

### Config Files

Config files still use strings (no changes needed):

```yaml
# config.yml
backend: falkordb # String value (not enum)
host: localhost
port: 6379
```

## Benefits

### 1. Type Safety

- **IDE Autocomplete**: See all available backends
- **Type Checking**: Catch typos before runtime
- **Refactoring**: Rename safely across codebase

### 2. Validation

- **Early Error Detection**: Invalid backends caught immediately
- **Helpful Error Messages**: Shows valid options
- **Single Source of Truth**: All backends defined in one place

### 3. Discoverability

```python
# Easy to discover what's available
from lineage.backends.types import LineageStorageType

print(LineageStorageType.list_values())
# ['falkordb', 'falkordblite']
```

### 4. Documentation

```python
# Self-documenting with docstrings
LineageStorageType.FALKORDB  # Hover in IDE shows: "FalkorDB - Redis-based graph database"
```

## Examples

### CLI with Enum

```python
import click
from lineage.backends.types import LineageStorageType

@click.command()
@click.option(
    "--backend",
    type=click.Choice([b.value for b in LineageStorageType]),
    default=LineageStorageType.FALKORDBLITE.value,
    help="Lineage storage backend"
)
def my_command(backend: str):
    # Validate to enum
    backend_type = LineageStorageType.from_string(backend)

    # Use with factory
    storage = create_storage(backend=backend_type)
```

### Type Hints

```python
from lineage.backends.types import LineageStorageType
from lineage.backends.lineage.protocol import LineageStorage

def initialize_backend(
    backend: LineageStorageType | str
) -> LineageStorage:
    """Initialize storage backend.

    Args:
        backend: Backend type (enum or string)

    Returns:
        Initialized storage adapter
    """
    # Convert to enum if string
    if isinstance(backend, str):
        backend = LineageStorageType.from_string(backend)

    return create_storage(backend=backend)
```

### Testing All Backends

```python
import pytest
from lineage.backends.types import LineageStorageType
from lineage.backends.lineage.factory import create_storage

@pytest.mark.parametrize("backend", LineageStorageType)
def test_all_backends(backend):
    """Test works with all backend types."""
    storage = create_storage(backend=backend)
    # ... test logic
```

## Future Enhancements

### Adding New Backend Types

1. Add to enum in `types.py`:

   ```python
   class LineageStorageType(str, Enum):
       # ... existing
       NEW_BACKEND = "new-backend"
       """NewBackend - Description"""
   ```

2. Add to config.py (imports automatically validated)

3. Add to factory.py

4. **That's it!** All validation, error messages, and documentation update automatically.

## Summary

- **`LineageStorageType`** - Type-safe enum for lineage storage backends (FalkorDB, FalkorDBLite)
- **`DataBackendType`** - Type-safe enum for data warehouse backends
- **Backwards compatible** - Strings still work, but enums preferred
- **Better DX** - IDE autocomplete, type checking, validation
- **Self-documenting** - Discover backends via `list_values()`

Use enums in new code for the best developer experience!
