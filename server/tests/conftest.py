"""
Pytest configuration. Tests run against your PostgreSQL database (same .env).
Uses unique emails per test so runs don't conflict with existing or previous data.
"""
import os
import sys
import uuid

# Ensure server app is on path when running from project root or server/
_server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient; uses PostgreSQL from .env."""
    return TestClient(app)


@pytest.fixture
def unique_email():
    """Return a unique email for signup so tests don't conflict."""
    return f"test-{uuid.uuid4().hex[:12]}@example.com"
