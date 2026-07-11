# Boilerworks CherryPy Micro -- Memory

This file is the **AI context seed** for this edition. It captures decisions, constraints, and non-obvious facts that are not derivable from reading the code.

For conventions and patterns, see [`bootstrap.md`](bootstrap.md).

---

## Platform purpose

Pure-Python API microservice edition of the Boilerworks family: CherryPy + SQLAlchemy + Alembic + Postgres, API-key auth only. No frontend, no sessions, no async stack. Each Boilerworks edition is a ground-up build for its stack -- shared principles, no shared code.

---

## Key architectural decisions

| Decision | Why |
|---|---|
| CherryPy's built-in HTTP server | Zero extra processes for a micro service; no WSGI gateway, no reverse proxy needed for dev |
| API-key auth, SHA256-hashed | Machine-to-machine service; plaintext keys are never stored, only printed once at seed time |
| Per-key scopes (`events.read`, `events.write`, `keys.manage`, `*`) | Least-privilege keys without a user/role model |
| CherryPy tools (`api_key`, `require_scope`), not middleware | Idiomatic CherryPy for cross-cutting concerns; scope checks live on individual handlers |
| Migrations run on app startup | No separate migration container or deploy step for a micro service |
| Soft deletes on events (`deleted_at`) | Consistent with the rest of the fleet; never hard-delete business objects |
| UUID primary keys | Internal IDs are never exposed |
| Integration tests against a real server + real Postgres | `tests/conftest.py` boots CherryPy on a random port in a background thread; no mocking of the HTTP or DB layer |

---

## Things that bite newcomers

- **Port split between local dev and Docker**: `app/config.py`, `.env.example`, and `tests/conftest.py` default to Postgres on `localhost:5440` and app port `8083`; `docker-compose.yml` publishes Postgres on host `5432` and the API on `8000` (container port 8080). To run `make test` against the compose Postgres, set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/boilerworks`.
- **The seed key is idempotent and printed only once** -- `app/seed.py` skips creation if the hash already exists, so the "Plaintext key" log line only appears on first boot with a given `API_KEY_SEED`. The compose file pins it to `bw_seed_key_change_me_in_production`.
- **All responses are wrapped** in `{ok, data, message, errors}` -- including errors, via the custom JSON error page in `app/tools.py`.
- **Trailing slashes are load-bearing** -- CherryPy URLs use them consistently (`/events/`, not `/events`).
- **`uv.lock` is tracked but not consumed** -- CI, Makefile, and Dockerfile all install with pip from `pyproject.toml`'s `>=` ranges (see issue #15).

---

## Test fixtures

`tests/conftest.py` seeds four fixed keys per session (admin `*`, read-only, no-scope, keys-manage) after wiping `api_keys` and `events`; an autouse fixture wipes events before each test. Tests hit the live server with `requests`.
