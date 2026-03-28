import requests


def test_create_event(base_url, admin_key):
    """POST /events/ creates an event and returns 201."""
    resp = requests.post(
        f"{base_url}/events/",
        json={"type": "order.placed", "payload": {"order_id": 42}},
        headers={"X-API-Key": admin_key},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["type"] == "order.placed"
    assert body["data"]["payload"] == {"order_id": 42}
    assert body["data"]["status"] == "pending"


def test_list_events(base_url, admin_key):
    """GET /events/ lists events."""
    # Create two events
    requests.post(f"{base_url}/events/", json={"type": "a"}, headers={"X-API-Key": admin_key})
    requests.post(f"{base_url}/events/", json={"type": "b"}, headers={"X-API-Key": admin_key})

    resp = requests.get(f"{base_url}/events/", headers={"X-API-Key": admin_key})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 2


def test_filter_events_by_type(base_url, admin_key):
    """GET /events/?type=x filters by type."""
    requests.post(f"{base_url}/events/", json={"type": "order.placed"}, headers={"X-API-Key": admin_key})
    requests.post(f"{base_url}/events/", json={"type": "user.signup"}, headers={"X-API-Key": admin_key})

    resp = requests.get(f"{base_url}/events/?type=order.placed", headers={"X-API-Key": admin_key})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["type"] == "order.placed"


def test_get_event_by_id(base_url, admin_key):
    """GET /events/{id} returns a single event."""
    create_resp = requests.post(
        f"{base_url}/events/",
        json={"type": "test.detail"},
        headers={"X-API-Key": admin_key},
    )
    event_id = create_resp.json()["data"]["id"]

    resp = requests.get(f"{base_url}/events/{event_id}", headers={"X-API-Key": admin_key})
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == event_id


def test_get_event_not_found(base_url, admin_key):
    """GET /events/{id} with bogus UUID returns 404."""
    resp = requests.get(
        f"{base_url}/events/00000000-0000-0000-0000-000000000000",
        headers={"X-API-Key": admin_key},
    )
    assert resp.status_code == 404


def test_soft_delete_event(base_url, admin_key):
    """DELETE /events/{id} soft-deletes and excludes from list."""
    create_resp = requests.post(
        f"{base_url}/events/",
        json={"type": "to.delete"},
        headers={"X-API-Key": admin_key},
    )
    event_id = create_resp.json()["data"]["id"]

    del_resp = requests.delete(f"{base_url}/events/{event_id}", headers={"X-API-Key": admin_key})
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "Event deleted"

    # Should not appear in list
    list_resp = requests.get(f"{base_url}/events/", headers={"X-API-Key": admin_key})
    ids = [e["id"] for e in list_resp.json()["data"]]
    assert event_id not in ids

    # Should not appear in detail
    detail_resp = requests.get(f"{base_url}/events/{event_id}", headers={"X-API-Key": admin_key})
    assert detail_resp.status_code == 404
