"""Tests for /api/users: dashboard, saved-searches, alerts (all require auth)."""
import pytest
from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, unique_email: str, password: str = "pass123"):
    """Sign up and return Authorization headers. Use unique_email so tests don't conflict on Postgres."""
    r = client.post("/api/auth/signup", json={"email": unique_email, "password": password})
    assert r.status_code == 201, r.json()
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_without_auth(client: TestClient):
    """GET /api/users/dashboard without token returns 401."""
    r = client.get("/api/users/dashboard")
    assert r.status_code == 401


def test_dashboard_with_auth(client: TestClient, unique_email: str):
    """GET /api/users/dashboard with valid token returns 200 and counts."""
    headers = _auth_headers(client, unique_email)
    r = client.get("/api/users/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "saved_searches_count" in data
    assert "active_alerts_count" in data
    assert "recent_saved_searches" in data
    assert "recent_alerts" in data
    assert data["saved_searches_count"] == 0
    assert data["active_alerts_count"] == 0


def test_create_and_list_saved_searches(client: TestClient, unique_email: str):
    """POST saved search then GET list returns it."""
    headers = _auth_headers(client, unique_email)
    r = client.post(
        "/api/users/saved-searches",
        json={"search_query": "laptop", "filters_json": None},
        headers=headers,
    )
    assert r.status_code == 201
    created = r.json()
    assert created["search_query"] == "laptop"
    search_id = created["id"]

    r2 = client.get("/api/users/saved-searches", headers=headers)
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) >= 1
    assert any(s["id"] == search_id and s["search_query"] == "laptop" for s in items)


def test_delete_saved_search(client: TestClient, unique_email: str):
    """DELETE saved search returns 204 and removes it from list."""
    headers = _auth_headers(client, unique_email)
    r = client.post(
        "/api/users/saved-searches",
        json={"search_query": "phone"},
        headers=headers,
    )
    assert r.status_code == 201
    search_id = r.json()["id"]

    r_del = client.delete(f"/api/users/saved-searches/{search_id}", headers=headers)
    assert r_del.status_code == 204

    r_list = client.get("/api/users/saved-searches", headers=headers)
    assert r_list.status_code == 200
    ids = [s["id"] for s in r_list.json()]
    assert search_id not in ids


def test_list_alerts_with_auth(client: TestClient, unique_email: str):
    """GET /api/users/alerts with valid token returns 200 and list (may be empty)."""
    headers = _auth_headers(client, unique_email)
    r = client.get("/api/users/alerts", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
