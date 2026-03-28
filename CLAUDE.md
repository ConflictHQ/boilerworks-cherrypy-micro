# Claude -- Boilerworks CherryPy Micro

Primary conventions doc: [`bootstrap.md`](bootstrap.md)

Read it before writing any code.

## Stack

- **Backend**: Python 3.12+ (CherryPy 18+)
- **Frontend**: None (API-only microservice)
- **API**: REST with JSON responses
- **ORM**: SQLAlchemy 2.0 (mapped_column style)
- **Migrations**: Alembic
- **Auth**: API-key (SHA256 hashed, per-key scopes)

## Quick Reference

| Endpoint | URL |
|----------|-----|
| Health | http://localhost:8083/health/ |
| Events | http://localhost:8083/events/ |
| API Keys | http://localhost:8083/api-keys/ |

## Commands

```bash
make up        # Start Docker services
make down      # Stop services
make build     # Install deps
make test      # Run tests (needs Postgres)
make lint      # Ruff check + format
make migrate   # Run Alembic migrations
make logs      # Tail container logs
```

## Structure

```
app/
  __init__.py       -- entry point, create_app(), main()
  __main__.py       -- python -m app support
  config.py         -- Config from env (DATABASE_URL, PORT, API_KEY_SEED)
  database.py       -- SQLAlchemy engine + session factory + Alembic runner
  models.py         -- ApiKey, Event SQLAlchemy models
  tools.py          -- CherryPy tools: api_key, require_scope + JSON error page
  seed.py           -- Seed script for initial API key
  api/
    health.py       -- GET /health/
    events.py       -- POST/GET/DELETE /events/
    api_keys.py     -- POST/GET/DELETE /api-keys/
migrations/
  env.py            -- Alembic config
  versions/
    001_init.py     -- Initial migration
tests/
  conftest.py       -- Fixtures: test server, seed keys, cleanup
  test_health.py    -- Health endpoint (1 test)
  test_auth.py      -- Auth + scope checks (5 tests)
  test_events.py    -- Events CRUD (6 tests)
  test_api_keys.py  -- API keys CRUD (5 tests)
```

## Rules

- API-key auth on all endpoints except /health/
- UUID primary keys, never expose internal IDs
- Soft deletes on events (deleted_at field)
- Scopes: `events.read`, `events.write`, `keys.manage`, `*` (wildcard)
- All responses wrapped in `{ok, data, message, errors}`
- CherryPy URLs use trailing slashes
- CherryPy tools for cross-cutting concerns (not middleware)
