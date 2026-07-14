# Database Architecture

## Technology Choices

| Concern | Choice | Why |
|---|---|---|
| Database | PostgreSQL 16 | UUID support, JSON, pg_trgm full-text search |
| ORM | SQLAlchemy 2 (async) | Type-safe, async-native, Alembic integration |
| Driver | asyncpg | Fastest async PostgreSQL driver for Python |
| Migrations | Alembic | Code-first schema versioning |
| Caching | Redis 7 | Celery broker + result backend + rate limiting |

---

## Schema Design Decisions

### UUID Primary Keys
Every table uses `uuid_generate_v4()` for primary keys.

**Why UUIDs instead of SERIAL integers?**
- Prevents enumeration attacks (attacker can't guess `/projects/1`, `/projects/2`)
- Safe to generate client-side when needed
- Works correctly in eventual multi-service architectures
- No INSERT ordering requirements

### Universal Mixins

Every model inherits these mixins:

| Mixin | Fields | Why |
|---|---|---|
| `UUIDMixin` | `id UUID PK` | Consistent primary key |
| `TimestampMixin` | `created_at`, `updated_at` | Audit trail for every record |
| `SoftDeleteMixin` | `deleted_at` | Never lose data |

### Soft Delete
Records are never physically deleted. Instead, `deleted_at` is set to now.

**Why soft delete?**
- Media files can be large — we delete files separately from DB records
- Preserves audit trail for AI generation history
- Allows "undo" functionality in future versions
- `deleted_at IS NULL` filter is fast with an index

### Status Columns
Generation-related models (Video, Image, AudioClip, GenerationJob) use a
string `status` column instead of an Enum.

**Why string instead of PostgreSQL ENUM?**
- Adding a new status value requires a migration for ENUM
- String columns can be altered without a lock
- More flexible for future pipeline states

---

## Connection Pool Configuration

```python
create_async_engine(
    DATABASE_URL,
    pool_size=10,       # Keep 10 connections open
    max_overflow=20,    # Allow 20 extra connections under load
    pool_timeout=30,    # Wait max 30s for a connection
    pool_pre_ping=True, # Validate connection before using
)
```

`pool_pre_ping=True` prevents the "server closed the connection unexpectedly" error
that occurs when PostgreSQL closes idle connections.

---

## Alembic Migration Strategy

- Migrations live in `alembic/versions/`
- Named as `NNNN_description.py` for chronological ordering
- Each migration has both `upgrade()` and `downgrade()`
- `alembic upgrade head` applies all pending migrations
- `alembic downgrade -1` rolls back the last migration

**Running migrations:**
```bash
make migrate          # Apply all pending
make rollback         # Rollback one step
alembic history       # Show migration history
alembic current       # Show current revision
```

---

## Redis Usage

| Use Case | Key Pattern | TTL |
|---|---|---|
| Celery task queue | `celery-task-meta-{task_id}` | 24 hours |
| Rate limit counters | `LIMITER/{ip}/{endpoint}` | 60 seconds |
| (Future) Session cache | `session:{user_id}` | 5 minutes |

Redis is configured with `maxmemory 512mb` and `allkeys-lru` eviction.
This means Redis will evict least-recently-used keys if it runs out of memory,
which is safe for all current use cases (caching/queuing, not source of truth).
