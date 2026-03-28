import requests


def test_create_api_key(base_url, admin_key):
    """POST /api-keys/ creates a new API key."""
    resp = requests.post(
        f"{base_url}/api-keys/",
        json={"name": "test-key", "scopes": ["events.read"]},
        headers={"X-API-Key": admin_key},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["name"] == "test-key"
    assert "key" in body["data"]  # plaintext key returned once
    assert body["data"]["key"].startswith("bw_")


def test_list_api_keys(base_url, admin_key):
    """GET /api-keys/ lists active keys."""
    resp = requests.get(f"{base_url}/api-keys/", headers={"X-API-Key": admin_key})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1  # at least the test keys


def test_revoke_api_key(base_url, admin_key):
    """DELETE /api-keys/{id} revokes a key."""
    # Create a key to revoke
    create_resp = requests.post(
        f"{base_url}/api-keys/",
        json={"name": "to-revoke", "scopes": []},
        headers={"X-API-Key": admin_key},
    )
    key_id = create_resp.json()["data"]["id"]

    del_resp = requests.delete(f"{base_url}/api-keys/{key_id}", headers={"X-API-Key": admin_key})
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "API key revoked"


def test_create_api_key_validation(base_url, admin_key):
    """POST /api-keys/ without name returns 400."""
    resp = requests.post(
        f"{base_url}/api-keys/",
        json={"scopes": ["events.read"]},
        headers={"X-API-Key": admin_key},
    )
    assert resp.status_code == 400


def test_api_keys_require_scope(base_url, read_only_key):
    """API keys endpoints require keys.manage scope."""
    resp = requests.get(f"{base_url}/api-keys/", headers={"X-API-Key": read_only_key})
    assert resp.status_code == 403
