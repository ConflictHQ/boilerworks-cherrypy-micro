# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Boilerworks, please report it responsibly.

**Do not open a public issue.**

Instead, email **security@weareconflict.com** with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge your report within 48 hours and aim to release a fix within 7 days for critical issues.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| latest  | Yes       |

## Security Best Practices

When deploying Boilerworks:

- Rotate the seed API key: set `API_KEY_SEED` to a strong random value (never ship `bw_seed_key_change_me_in_production`), then mint scoped keys via `/api-keys/` and revoke the seed key
- Change the default Postgres credentials in `docker-compose.yml` / `DATABASE_URL`
- Serve over HTTPS via a reverse proxy (nginx, Caddy, or a load balancer) — CherryPy's built-in server listens on plain HTTP
- Grant keys the narrowest scopes that work (`events.read`, `events.write`, `keys.manage`); reserve `*` for administration
- Do not expose the Postgres port to the public internet
