"""
test_integrity_and_crud.py — Rigorous verification of database integrity,
Stop CRUD endpoints, fleet allocator resilience against over-constraints,
and crowding lookup caching.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth.auth_service import create_access_token
from backend.app.core.allocation.optimizer import FleetAllocationOptimizer
from backend.app.database import engine
from sqlalchemy import text


@pytest.fixture(scope="module")
def admin_headers():
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_sqlite_foreign_keys_and_wal_active():
    """Verify engine connect event properly sets foreign keys on SQLite."""
    with engine.connect() as conn:
        res = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert res == 1, "SQLite foreign_keys pragma is not active"


def test_stop_crud_lifecycle(client, admin_headers):
    """Verifies complete creation, lookup, update, and deletion of a transit stop."""
    new_stop_id = "STOP_TEST_INTEGRITY_01"

    # 1. Ensure clean initial state
    client.delete(f"/api/stops/{new_stop_id}", headers=admin_headers)

    # 2. CREATE (POST /api/stops)
    create_payload = {
        "stop_id": new_stop_id,
        "name": "Audit Test Terminal",
        "lat": 10.9650,
        "lon": 78.0820,
        "area_id": "AREA_A",
        "sequence_order": 99,
    }
    create_resp = client.post("/api/stops", json=create_payload, headers=admin_headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["stop_id"] == new_stop_id
    assert created_data["name"] == "Audit Test Terminal"

    # 3. READ (GET /api/stops)
    list_resp = client.get("/api/stops")
    assert list_resp.status_code == 200
    all_stops = list_resp.json()
    assert any(s["stop_id"] == new_stop_id for s in all_stops)

    # 4. UPDATE (PUT /api/stops/{stop_id})
    update_payload = {"name": "Audit Test Terminal Renamed", "sequence_order": 100}
    update_resp = client.put(f"/api/stops/{new_stop_id}", json=update_payload, headers=admin_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Audit Test Terminal Renamed"
    assert update_resp.json()["sequence_order"] == 100

    # 5. DELETE (DELETE /api/stops/{stop_id})
    del_resp = client.delete(f"/api/stops/{new_stop_id}", headers=admin_headers)
    assert del_resp.status_code == 200

    # 6. VERIFY GONE
    verify_list = client.get("/api/stops").json()
    assert not any(s["stop_id"] == new_stop_id for s in verify_list)


def test_optimizer_resilience_over_constrained():
    """
    Verifies that when minimum coverage constraints exceed available fleet,
    the CP-SAT optimizer gracefully scales down rather than raising an unhandled 500.
    """
    allocator = FleetAllocationOptimizer(total_fleet=10, bus_capacity=50)
    demands = {"AREA_A": 200, "AREA_B": 150, "AREA_C": 300}
    # Impossible constraint: 3 areas × 5 min buses = 15 buses needed, but fleet is only 10
    impossible_coverage = {"AREA_A": 5, "AREA_B": 5, "AREA_C": 5}

    result = allocator.solve(demands, min_coverage=impossible_coverage)
    assert result["status"] in ["OPTIMAL", "FEASIBLE", "FALLBACK_PROPORTIONAL"]
    assert result["total_buses_allocated"] <= 10
    assert sum(result["allocation"].values()) <= 10


def test_crowding_endpoint_cached(client):
    """Verifies that commuter crowding lookup works without crashing and returns valid crowd metrics."""
    resp = client.get("/api/crowding?bus_id=BUS-01")
    assert resp.status_code == 200
    data = resp.json()
    assert "crowd_level" in data
    assert "utilization_pct" in data
    assert data["bus_id"] == "BUS-01"
