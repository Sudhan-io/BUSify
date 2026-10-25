"""
conftest.py — shared pytest fixtures.

Auth-gated endpoints (campus registration, campus switching, stop import) now
require a Transport Officer / Admin bearer token, so tests exercising them must
present credentials rather than relying on the endpoints being public.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_headers(client):
    """Authorisation header for an Admin-role token, obtained via the real login route."""
    response = client.post(
        "/api/auth/token",
        json={"username": "admin", "password": settings.ADMIN_PASSWORD},
    )
    assert response.status_code == 200, (
        f"Admin login failed ({response.status_code}): {response.text}"
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}