# Phase 1 Architecture Notes — Prabhu AI Studio

## Overview

Phase 1 establishes the foundational architecture for the entire application.
Every decision made here is designed to support 10 future phases without major refactoring.

---

## Backend Architecture

### Layer Separation

```
HTTP Request
    │
    ▼
Controller (FastAPI Router)
    │   - Input validation (Pydantic schemas)
    │   - HTTP status codes
    │   - Error translation to HTTP responses
    ▼
Service Layer
    │   - Business logic
    │   - Orchestrates multiple repositories
    │   - Raises domain exceptions (never HTTP exceptions)
    ▼
Repository Layer
    │   - Data access only
    │   - No business logic
    │   - Returns ORM models or None
    ▼
Database (PostgreSQL via SQLAlchemy)
```

### Why This Separation?

**Controller** knows about HTTP. It converts domain exceptions into HTTP responses.
**Service** knows about business rules. It has no idea HTTP exists.
**Repository** knows about SQL. It has no idea business rules exist.

This means:
- Services can be unit tested without a database.
- Repositories can be swapped (e.g., from PostgreSQL to MongoDB) without changing services.
- Controllers can be swapped (e.g., from FastAPI to gRPC) without changing services.

---

## AI Provider Abstraction

All AI providers follow a Protocol/ABC interface:

```python
class LLMProvider(Protocol):
    async def generate(self, prompt: str, **kwargs) -> str: ...

class GemmaProvider(LLMProvider):
    ...

class LlamaProvider(LLMProvider):
    ...
```

A factory reads the `LLM_PROVIDER` environment variable and returns the correct implementation.
Switching from Gemma to Llama requires only a `.env` change — zero code changes.

---

## Database Design Decisions

### UUID Primary Keys
All tables use UUID v4 primary keys instead of sequential integers.
- Prevents enumeration attacks
- Safe to generate client-side if needed
- Works correctly in distributed systems

### Timestamp Mixin
`created_at` and `updated_at` are added to every table automatically.
`updated_at` uses `onupdate=func.now()` for automatic tracking.

### Soft Delete
`deleted_at` column enables soft deletion.
Records are never physically deleted — they get a `deleted_at` timestamp.
This preserves the audit trail for a media-generation application.

---

## Security Architecture

### Password Security
- bcrypt with salt (via passlib)
- bcrypt is deliberately slow — brute force resistant
- Never store plain text

### JWT Design
- Two-token pattern: short-lived access token + long-lived refresh token
- Access token: 60 minutes (configurable)
- Refresh token: 30 days (configurable)
- Token type claim prevents refresh token from being used as access token
- All tokens validated on every request

### Request Tracing
Every request gets a UUID `X-Request-ID` injected by middleware.
This ID appears in all log lines for that request, enabling full request tracing.

---

## Configuration Architecture

All settings use `pydantic-settings` with environment variable binding.
- Type-safe — wrong types fail at startup, not at runtime
- Cached with `@lru_cache` — parsed once per process
- Hierarchical — sub-settings are composed from the root `Settings` class
- Environment-aware — different defaults per environment

---

## Frontend Architecture

### Why Next.js App Router?
- Server Components reduce JavaScript bundle size
- Streaming and Suspense boundaries for AI-heavy operations
- Built-in image optimization for AI-generated content
- File-system routing matches the application's feature areas

### State Management Strategy
- **Server state** (API data): TanStack Query with automatic caching/invalidation
- **Auth state**: TanStack Query + cookies (no Zustand needed for Phase 1)
- **UI state**: React local state (useState/useReducer)

### API Client Design
- Single Axios instance with interceptors
- Automatic token injection on every request
- Transparent token refresh on 401 — the caller never sees the refresh happen
- Request queuing during refresh prevents multiple simultaneous refresh calls
