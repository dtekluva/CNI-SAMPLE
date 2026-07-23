import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_returns_ok():
    """First green test — proves the API stack is wired end-to-end."""
    client = APIClient()
    resp = client.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.django_db
def test_authenticated_endpoints_default_to_locked():
    """Least-privilege sanity: an unknown API path is not silently public."""
    client = APIClient()
    resp = client.get("/api/does-not-exist/")
    assert resp.status_code in (401, 403, 404)
