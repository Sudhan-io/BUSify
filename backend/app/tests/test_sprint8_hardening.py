"""
test_sprint8_hardening.py — Tests for Sprint 8 Security, Accessibility, and Integration Hardening.

Covers:
- L-01: Security Headers & Content-Security-Policy
- SEC-003: CPU DOS Protection & Concurrency Lock on POST /api/simulate
- Environment & Production Secrets Guard
- L-06: Plan model timezone-aware timestamp
- A11Y-001: Accessibility modal attributes, Escape listeners, and focus styles
- M-05, M-06, M-07: Docker environment consistency & requirements sync
"""

import threading
import pytest
from datetime import timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import Settings
from backend.app.models.plan import Plan
from backend.app.api.routes_simulation import _simulation_lock


@pytest.fixture
def client():
    return TestClient(app)


# ─── L-01: Security Headers & CSP ─────────────────────────────────────────────

def test_security_headers_present_on_api(client):
    """Verify security headers (X-Content-Type-Options, X-Frame-Options, CSP) are injected."""
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "strict-origin-when-cross-origin" in headers.get("referrer-policy", "")
    assert "default-src 'self'" in headers.get("content-security-policy", "")


def test_security_headers_on_root_endpoint(client):
    """Verify root endpoint also returns security headers."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("x-frame-options") == "DENY"
    assert "nosniff" in response.headers.get("x-content-type-options", "")


# ─── SEC-003: Concurrency Guard on /api/simulate ─────────────────────────────

def test_simulation_concurrency_lock_returns_429(client):
    """Verify that concurrent simulation requests receive HTTP 429 Too Many Requests."""
    # Simulate an active ongoing simulation holding the lock
    acquired = _simulation_lock.acquire(blocking=False)
    assert acquired is True, "Failed to acquire simulation lock for test setup"

    try:
        # A concurrent request should immediately be rejected with 429
        response = client.post("/api/simulate", json={"sample_days": 1})
        assert response.status_code == 429
        assert "already running" in response.json().get("detail", "").lower()
    finally:
        _simulation_lock.release()

    # Once lock is freed, simulation executes normally
    response = client.post("/api/simulate", json={"sample_days": 1})
    assert response.status_code == 200
    assert response.json().get("status") == "SUCCESS"


# ─── Environment & Secrets Hardening ──────────────────────────────────────────

def test_production_rejects_sqlite():
    """Verify Settings raises ValueError in production if DATABASE_URL uses SQLite."""
    with pytest.raises(ValueError, match="DATABASE_URL must not use SQLite"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///./busify.db",
            JWT_SECRET="a" * 64,
            STUDENT_HASH_SALT="b" * 32,
            TRANSPORT_OFFICER_PASSWORD="ComplexPassword123!",
            ADMIN_PASSWORD="ComplexPassword123!",
            CORS_ALLOWED_ORIGINS="https://busify.college.edu",
        )


def test_production_rejects_wildcard_cors():
    """Verify Settings raises ValueError in production if CORS allows wildcard '*'."""
    with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS must not allow"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql://user:pass@localhost:5432/busify",
            JWT_SECRET="a" * 64,
            STUDENT_HASH_SALT="b" * 32,
            TRANSPORT_OFFICER_PASSWORD="ComplexPassword123!",
            ADMIN_PASSWORD="ComplexPassword123!",
            CORS_ALLOWED_ORIGINS="*",
        )


def test_production_rejects_weak_jwt_secret():
    """Verify Settings raises ValueError in production if JWT_SECRET is trivial or short."""
    with pytest.raises(ValueError, match="JWT_SECRET must be set and contain at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql://user:pass@localhost:5432/busify",
            JWT_SECRET="short_secret",
            STUDENT_HASH_SALT="b" * 32,
            TRANSPORT_OFFICER_PASSWORD="ComplexPassword123!",
            ADMIN_PASSWORD="ComplexPassword123!",
            CORS_ALLOWED_ORIGINS="https://busify.college.edu",
        )


def test_production_accepts_valid_configuration():
    """Verify Settings initializes cleanly when valid production configuration is provided."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql://user:pass@localhost:5432/busify",
        JWT_SECRET="a" * 64,
        STUDENT_HASH_SALT="b" * 32,
        TRANSPORT_OFFICER_PASSWORD="ComplexPassword123!",
        ADMIN_PASSWORD="ComplexPassword123!",
        CORS_ALLOWED_ORIGINS="https://busify.college.edu",
    )
    assert prod_settings.ENVIRONMENT == "production"


# ─── L-06: Plan Model Timezone Awareness ──────────────────────────────────────

def test_plan_created_at_timezone():
    """Verify Plan model created_at default produces timezone-aware UTC datetime."""
    col = Plan.__table__.c.created_at
    assert col.type.timezone is True
    default_val = col.default.arg(None)
    assert default_val.tzinfo == timezone.utc


# ─── A11Y-001 & Docker Consistency Verification ───────────────────────────────

def test_accessibility_attributes_present_in_source():
    """Verify that dialog roles and focus styles are embedded in frontend source."""
    with open("frontend/src/components/Navbar.jsx", "r", encoding="utf-8") as f:
        navbar_src = f.read()
    assert 'role="dialog"' in navbar_src
    assert 'aria-modal="true"' in navbar_src
    assert 'id="register-college-title"' in navbar_src
    assert 'htmlFor="inst-name"' in navbar_src

    with open("frontend/src/pages/office/FleetAndDrivers.jsx", "r", encoding="utf-8") as f:
        fleet_src = f.read()
    assert 'role="dialog"' in fleet_src
    assert 'aria-modal="true"' in fleet_src
    assert 'id="bus-modal-title"' in fleet_src
    assert 'htmlFor="bus-code-input"' in fleet_src

    with open("frontend/src/index.css", "r", encoding="utf-8") as f:
        css_src = f.read()
    assert ":focus-visible" in css_src


def test_docker_and_requirements_consistency():
    """Verify M-05, M-06, and M-07 requirements and path consistency."""
    with open("backend/Dockerfile", "r", encoding="utf-8") as f:
        b_df = f.read()
    assert "/app/data/busify.db" in b_df

    with open("frontend/Dockerfile", "r", encoding="utf-8") as f:
        f_df = f.read()
    assert "VITE_API_BASE_URL" in f_df
    assert "VITE_API_URL" in f_df

    with open("requirements.txt", "r", encoding="utf-8") as f1, open("backend/requirements.txt", "r", encoding="utf-8") as f2:
        assert f1.read() == f2.read(), "backend/requirements.txt is out of sync with root requirements.txt"
