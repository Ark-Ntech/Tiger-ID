# Database Setup Guide

Tiger ID uses **SQLite with sqlite-vec** for all data storage and vector similarity search. No external database server required.

## Quick Start

```bash
# Install sqlite-vec (required)
pip install sqlite-vec

# Set database path (optional, defaults to data/tiger_id.db)
export DATABASE_URL=sqlite:///data/tiger_id.db

# Initialize database
python -c "from backend.database import init_db; init_db()"

# Start backend
cd backend && uvicorn main:app --reload --port 8000
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///data/tiger_id.db` | SQLite database path |

The database URL must be a SQLite connection string starting with `sqlite:///`.

### Docker Configuration

```yaml
services:
  api:
    environment:
      - DATABASE_URL=sqlite:///app/data/tiger_id.db
    volumes:
      - ./data:/app/data  # Persist database file
```

## Vector Search with sqlite-vec

Tiger ID uses the `sqlite-vec` extension for fast approximate nearest neighbor search on tiger embeddings.

### Installation

```bash
pip install sqlite-vec>=0.1.6
```

### How It Works

1. **sqlite-vec** creates a virtual table `vec_embeddings` for storing embedding vectors
2. Embeddings are stored as normalized float32 blobs
3. KNN search uses cosine distance for similarity matching

### Performance

| Gallery Size | Search Time | Memory Usage |
|-------------|-------------|--------------|
| 1,000 images | ~10-20ms | ~50MB |
| 5,000 images | ~15-25ms | ~200MB |
| 10,000 images | ~20-35ms | ~400MB |

Performance is suitable for galleries up to 10k+ tigers.

### Fallback Mode

If sqlite-vec is not available, the system falls back to Python-based cosine similarity (slower but functional):

```python
# Fallback uses scipy for cosine distance
from scipy.spatial.distance import cosine
```

## Database Initialization

### Automatic Initialization

The database is automatically initialized when the API starts:

1. Creates all tables defined in SQLAlchemy models
2. Creates the `vec_embeddings` virtual table for vector search
3. Loads sqlite-vec extension with WAL mode enabled

### Manual Initialization

```bash
# Initialize database schema
python -c "from backend.database import init_db; init_db()"

# Populate with tiger data (if available)
python scripts/init_db.py
```

### Docker Initialization

The Docker container runs initialization automatically via `entrypoint-sqlite.sh`:

1. Initializes database schema
2. Creates admin user (username: `admin`, password: `admin`)
3. Starts the API server

## Database Schema

### Core Tables (29 total)

| Table | Description |
|-------|-------------|
| `users` | User accounts and authentication |
| `tigers` | Tiger records and identification |
| `tiger_images` | Tiger images with metadata |
| `vec_embeddings` | Vector embeddings (virtual table) |
| `facilities` | Facility information |
| `investigations` | Investigation records |
| `evidence` | Evidence items |
| `audit_logs` | System audit trail |

### SQLite-Specific Features

- **WAL mode**: Enabled for better concurrent read performance
- **Foreign keys**: Enforced via PRAGMA
- **UUIDs**: Stored as 36-character strings (UUID format)
- **JSON data**: Stored as TEXT and parsed in Python
- **Timestamps**: Use `CURRENT_TIMESTAMP` server default

## Data Types

SQLAlchemy models use SQLite-compatible types:

| Python Type | SQLite Type | Notes |
|-------------|-------------|-------|
| `UUID` | `String(36)` | Stored as hyphenated string |
| `JSON` | `Text` | Serialized/deserialized in Python |
| `Enum` | `String(50)` | Stored as string value |
| `DateTime` | `DateTime` | SQLite datetime format |
| `Vector` | `BLOB` | Via sqlite-vec virtual table |

## Backup and Restore

### Backup

```bash
# Simple file copy (ensure no writes during backup)
cp data/tiger_id.db data/tiger_id.db.backup

# With timestamp
cp data/tiger_id.db "data/backups/tiger_id_$(date +%Y%m%d_%H%M%S).db"
```

### Restore

```bash
# Stop the application first
cp data/tiger_id.db.backup data/tiger_id.db
```

### WAL Mode Considerations

When using WAL mode, also backup the WAL file if it exists:

```bash
cp data/tiger_id.db data/backups/
cp data/tiger_id.db-wal data/backups/  # If exists
cp data/tiger_id.db-shm data/backups/  # If exists
```

## Troubleshooting

### sqlite-vec Not Loading

1. Verify installation:
   ```bash
   pip show sqlite-vec
   python -c "import sqlite_vec; print('OK')"
   ```

2. Check Python version (requires 3.9+)

3. The system automatically falls back to Python-based search

### Database Locked Errors

SQLite has limited concurrent write support. If you see "database is locked":

1. Ensure only one write operation at a time
2. Check for long-running transactions
3. Consider increasing busy timeout:
   ```python
   engine = create_engine(url, connect_args={"timeout": 30})
   ```

### Database Corruption

If the database becomes corrupted:

1. Try the integrity check:
   ```bash
   sqlite3 data/tiger_id.db "PRAGMA integrity_check;"
   ```

2. Restore from backup if needed

3. Re-initialize if no backup available:
   ```bash
   rm data/tiger_id.db*
   python -c "from backend.database import init_db; init_db()"
   ```

### Missing Tables

If tables are missing:

```bash
# Re-run initialization
python -c "from backend.database import init_db; init_db()"
```

## Migration from Previous Versions

If migrating from an older PostgreSQL-based version:

1. Export data from PostgreSQL:
   ```bash
   pg_dump --data-only -f data_export.sql old_database
   ```

2. Convert SQL to SQLite-compatible format

3. Import into new SQLite database

4. Re-generate embeddings (different storage format)

## Performance Tuning

### Recommended PRAGMA Settings

These are automatically set by the application:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
```

### Connection Pool

SQLAlchemy connection pool settings:

```python
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
```

## Additional Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [sqlite-vec GitHub](https://github.com/asg017/sqlite-vec)
- [SQLAlchemy SQLite Dialect](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)
