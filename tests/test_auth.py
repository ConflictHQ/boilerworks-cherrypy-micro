import requests


def test_missing_api_key_returns_401(base_url):
    """Request without X-API-Key header returns 401."""
    resp = requests.get(f"{base_url}/events/")
    assert resp.status_code == 401


def test_invalid_api_key_returns_401(base_url):
    """Request with wrong API key returns 401."""
    resp = requests.get(f"{base_url}/events/", headers={"X-API-Key": "bw_totally_bogus"})
    assert resp.status_code == 401


def test_valid_api_key_returns_200(base_url, admin_key):
    """Request with valid admin key returns 200."""
    resp = requests.get(f"{base_url}/events/", headers={"X-API-Key": admin_key})
    assert resp.status_code == 200


def test_read_only_blocked_from_write(base_url, read_only_key):
    """Read-only key cannot create events (events.write scope needed)."""
    resp = requests.post(
        f"{base_url}/events/",
        json={"type": "test"},
        headers={"X-API-Key": read_only_key},
    )
    assert resp.status_code == 403


def test_wildcard_grants_all(base_url, admin_key):
    """Admin key with '*' scope can access everything."""
    # events.write
    resp = requests.post(
        f"{base_url}/events/",
        json={"type": "test"},
        headers={"X-API-Key": admin_key},
    )
    assert resp.status_code == 201

    # keys.manage
    resp = requests.get(f"{base_url}/api-keys/", headers={"X-API-Key": admin_key})
    assert resp.status_code == 200
