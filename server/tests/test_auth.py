"""Tests for /api/auth: signup, login, refresh, me."""
import pytest
from fastapi.testclient import TestClient


def test_signup_returns_tokens(client: TestClient, unique_email: str):
    """Signup returns 201 with access_token and refresh_token."""
    r = client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "testpass123"},
    )
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in data
    assert data["email"] == unique_email
    assert data["user_id"] is not None


def test_login_returns_tokens(client: TestClient, unique_email: str):
    """After signup, login returns 200 with access_token and refresh_token."""
    client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "pass123"},
    )
    r = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "pass123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == unique_email


def test_login_invalid_password(client: TestClient, unique_email: str):
    """Login with wrong password returns 401."""
    client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "correct12"},
    )
    r = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "wrongpass"},
    )
    assert r.status_code == 401


def test_me_without_token(client: TestClient):
    """GET /api/auth/me without Authorization returns 401."""
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_token(client: TestClient, unique_email: str):
    """GET /api/auth/me with valid token returns 200 and user."""
    signup = client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "pass123"},
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] is not None
    assert "email" not in data  # UserResponse has id, first_name, etc.; email is on auth


def test_refresh_returns_new_tokens(client: TestClient, unique_email: str):
    """POST /api/auth/refresh with valid refresh_token returns new access_token and refresh_token."""
    signup = client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "pass123"},
    )
    assert signup.status_code == 201
    refresh_token = signup.json()["refresh_token"]
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token  # rotation: new token


def test_refresh_invalid_token(client: TestClient):
    """POST /api/auth/refresh with invalid token returns 401."""
    r = client.post("/api/auth/refresh", json={"refresh_token": "invalid-token"})
    assert r.status_code == 401
