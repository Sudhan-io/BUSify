import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.bus import Bus
from backend.app.models.plan import Plan
from backend.app.auth.auth_service import create_access_token

client = TestClient(app)

def _auth_headers(role: str = "transport_officer") -> dict:
    token = create_access_token({"sub": "test_officer", "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_manifest_sources_real_database_buses_and_drivers():
    """Verify that operational manifest routes map to real active DB buses and drivers."""
    res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()
    manifest = data["manifest"]
    assert len(manifest) > 0

    with SessionLocal() as db:
        active_buses = {b.bus_id: b for b in db.query(Bus).filter(Bus.is_active == True).all()}
        for route in manifest:
            bus_code = route["bus_code"]
            assert bus_code in active_buses
            db_bus = active_buses[bus_code]
            expected_driver = db_bus.driver_name or "Assigned College Driver"
            expected_phone = db_bus.driver_phone or "+91 90000 00001"
            assert route["driver_name"] == expected_driver
            assert route["driver_phone"] == expected_phone
            assert route["capacity"] == db_bus.seats


def test_manifest_prevents_duplicate_bus_assignment():
    """Verify that no physical vehicle is assigned to multiple simultaneous routes."""
    res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()
    assigned_bus_codes = [r["bus_code"] for r in data["manifest"] if r["bus_code"] != "UNASSIGNED"]
    assert len(assigned_bus_codes) == len(set(assigned_bus_codes))


def test_manifest_excludes_inactive_buses_from_assignment():
    """Verify that deactivating a bus prevents it from being assigned in the manifest."""
    with SessionLocal() as db:
        target_bus = db.query(Bus).filter(Bus.bus_id == "BUS-01").first()
        orig_active = target_bus.is_active
        try:
            target_bus.is_active = False
            db.commit()

            res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
            assert res.status_code == 200
            assigned_codes = [r["bus_code"] for r in res.json()["manifest"]]
            assert "BUS-01" not in assigned_codes
        finally:
            target_bus.is_active = orig_active
            db.commit()


def test_manifest_detects_insufficient_fleet():
    """Verify that when active fleet is smaller than route requirement, unassigned routes are flagged."""
    with SessionLocal() as db:
        # Deactivate 25 buses so only 25 remain active (fewer than the ~38 routes needed)
        buses_to_deactivate = db.query(Bus).limit(25).all()
        ids = [b.bus_id for b in buses_to_deactivate]
        for b in buses_to_deactivate:
            b.is_active = False
        db.commit()

        try:
            res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
            assert res.status_code == 200
            data = res.json()
            assert data["has_insufficient_fleet"] is True
            unassigned = [r for r in data["manifest"] if r["bus_code"] == "UNASSIGNED"]
            assert len(unassigned) >= 1
            assert unassigned[0]["status"] == "UNASSIGNED_INSUFFICIENT_FLEET"
        finally:
            for b_id in ids:
                db.query(Bus).filter(Bus.bus_id == b_id).update({"is_active": True})
            db.commit()


def test_plan_approval_requires_auth():
    """Verify that unauthenticated callers cannot approve or persist dispatch plans."""
    res = client.post("/api/workflow/plan/approve", json={"date": "2026-10-15", "scenario": "REGULAR"})
    assert res.status_code in (401, 403)


def test_plan_approval_persists_records_and_is_idempotent():
    """Verify that authorized approval creates Plan records and updates manifest status."""
    target_date = "2026-11-05"
    headers = _auth_headers("transport_officer")

    with SessionLocal() as db:
        db.query(Plan).filter(Plan.date == target_date).delete()
        db.commit()

    # 1. Check status is DRAFT before approval
    res_status = client.get(f"/api/workflow/plan/status?date={target_date}")
    assert res_status.status_code == 200
    assert res_status.json()["exists"] is False
    assert res_status.json()["status"] == "DRAFT"

    # 2. Approve plan
    res_approve = client.post(
        "/api/workflow/plan/approve",
        json={"date": target_date, "scenario": "REGULAR", "slot": "morning"},
        headers=headers,
    )
    assert res_approve.status_code == 200
    approve_data = res_approve.json()
    assert approve_data["success"] is True
    assert approve_data["status"] == "APPROVED"
    assert approve_data["total_routes"] > 0

    # 3. Check status is APPROVED after approval
    res_status_after = client.get(f"/api/workflow/plan/status?date={target_date}")
    assert res_status_after.status_code == 200
    assert res_status_after.json()["exists"] is True
    assert res_status_after.json()["status"] == "APPROVED"
    assert res_status_after.json()["total_routes"] == approve_data["total_routes"]

    # 4. Verify manifest reflects persisted plan
    res_manifest = client.get(f"/api/workflow/operational-manifest?scenario=REGULAR&date={target_date}")
    assert res_manifest.status_code == 200
    manifest_data = res_manifest.json()
    assert manifest_data["is_approved"] is True
    assert manifest_data["plan_status"] == "APPROVED"
    for r in manifest_data["manifest"]:
        assert r["status"] == "APPROVED"

    # 5. Repeat approval is idempotent (does not duplicate plan rows)
    res_repeat = client.post(
        "/api/workflow/plan/approve",
        json={"date": target_date, "scenario": "REGULAR", "slot": "morning"},
        headers=headers,
    )
    assert res_repeat.status_code == 200
    with SessionLocal() as db:
        count = db.query(Plan).filter(Plan.date == target_date).count()
        assert count == approve_data["total_routes"]
        db.query(Plan).filter(Plan.date == target_date).delete()
        db.commit()


def test_plan_approval_rejects_insufficient_fleet():
    """Verify that approval is rejected with 422 if fleet cannot service all routes."""
    headers = _auth_headers("transport_officer")
    target_date = "2026-11-06"

    with SessionLocal() as db:
        # Deactivate 25 buses to create a genuine shortage
        buses = db.query(Bus).limit(25).all()
        ids = [b.bus_id for b in buses]
        for b in buses:
            b.is_active = False
        db.commit()

        try:
            res = client.post(
                "/api/workflow/plan/approve",
                json={"date": target_date, "scenario": "REGULAR"},
                headers=headers,
            )
            assert res.status_code == 422
            assert "fleet shortage" in res.json()["detail"].lower()
        finally:
            for b_id in ids:
                db.query(Bus).filter(Bus.bus_id == b_id).update({"is_active": True})
            db.commit()
