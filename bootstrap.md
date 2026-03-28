# Boilerworks CherryPy Micro -- Bootstrap

> Python microservice with CherryPy, SQLAlchemy, Alembic, and API-key authentication.
> No frontend, no sessions -- pure API service.

## Architecture

```
Caller (service, cron, webhook sender)
  |
  v (HTTP + X-API-Key header)
  |
CherryPy (built-in HTTP server)
  |-- SQLAlchemy ORM (Postgres 16)
  +-- JSON API responses
```

## Conventions

### Auth
- All endpoints require `X-API-Key` header except `/health/`
- Keys are SHA256-hashed before storage -- plaintext never stored
- Per-key scopes: `events.read`, `events.write`, `keys.manage`, `*`
- `api_key` CherryPy tool validates key and stores on `cherrypy.request`
- `require_scope` CherryPy tool checks scope on individual handlers

### Models
- UUID primary keys (`gen_random_uuid()`)
- Snake_case table and column names
- Audit fields: `created_at`, `updated_at`
- Soft deletes: `deleted_at` field, queries filter automatically

### API
- All responses wrapped in `{ok, data, message, errors}`
- JSON request bodies parsed manually from `cherrypy.request.body`
- Validation errors return 400 with details in `errors` array
- CherryPy URLs use trailing slashes consistently

### Database
- SQLAlchemy 2.0 with `mapped_column` style models
- Alembic for migrations (run on startup)
- Migrations in `migrations/versions/`

### Docker
- `docker compose up -d --build` starts API + Postgres
- Migrations run on app startup (no separate migration container)
- Seed creates admin key with `['*']` scopes (logged to stdout once)
- API exposed on host port 8083, Postgres on 5440

### Seed API Key
On first boot, check container logs for the plaintext key:
```bash
docker compose logs api | grep "Plaintext key"
```

### Testing
- Integration tests use requests against a real CherryPy server + Postgres
- Server starts on a random port in a background thread
- Default test DATABASE_URL: `postgresql://postgres:postgres@localhost:5440/boilerworks`
