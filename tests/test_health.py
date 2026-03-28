import requests


def test_health_no_auth(base_url):
    """Health endpoint requires no auth and returns status ok."""
    resp = requests.get(f"{base_url}/health/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
