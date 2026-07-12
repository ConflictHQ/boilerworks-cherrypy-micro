# Calliope — Boilerworks CherryPy Micro
<!-- Agent shim for https://github.com/calliopeai/calliope-cli -->

Primary conventions doc: [`bootstrap.md`](bootstrap.md)
Context seed: [`memory.md`](memory.md)

Read both before writing any code.

---

## Project-specific notes

- Python 3.12+ / CherryPy 18+ — API-only microservice, REST with JSON responses.
- SQLAlchemy 2.0 (`mapped_column` style) + Alembic migrations; API-key auth (SHA256-hashed, per-key scopes) on all endpoints except `/health/`.
- UUID primary keys, never expose internal IDs; soft deletes on events (`deleted_at`).
- Scopes: `events.read`, `events.write`, `keys.manage`, `*`. All responses wrapped in `{ok, data, message, errors}`.
- CherryPy URLs use trailing slashes; cross-cutting concerns via CherryPy tools, not middleware.
- Commands via `make`: `up`/`down`/`build`/`test`/`lint`/`migrate` (tests need Postgres).
