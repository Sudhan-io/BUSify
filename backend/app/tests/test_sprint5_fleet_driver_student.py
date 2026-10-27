"""
test_sprint5_fleet_driver_student.py — Verification suite for Sprint 5:
- Bus fleet CRUD and validation (seats bounds 10–120, unique bus ID, valid area)
- Bus deletion safeguard against corruption of approved dispatch plans (HTTP 409)
- Driver conflict prevention (same driver cannot be on multiple active buses)
- Dedicated driver roster endpoint (/api/buses/drivers)
- Stop endpoint returns authoritative student registration counts (totaling 2,200)
- Student registrations endpoint with pagination and SHA-256 masking
- Area demand summary endpoint
- Student opt-out plan locking preservation
- Upload CSV rejects binary .xlsx with clear error (Resolves M-10)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.bus import Bus
from backend.app.models.stop import Stop
from backend.app.models.registration import Registration
from backend.app.models.plan import Plan
from backend.app.auth.auth_service import create_access_token


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def admin_headers():
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clean_test_buses_and_plans():
    """Ensure test entities are removed after each test."""
    yield
    db: Session = SessionLocal()
    try:
        db.query(Plan).filter(Plan.date == "2026-11-20").delete()
        db.query(Bus).filter(Bus.bus_id.like("TEST-BUS-%")).delete()
        # Restore any driver name modifications on BUS-01 / BUS-02
        b1 = db.query(Bus).filter(Bus.bus_id == "BUS-01").first()
        if b1 and b1.driver_name != "R. Murugan":
            b1.driver_name = "R. Murugan"
        b2 = db.query(Bus).filter(Bus.bus_id == "BUS-02").first()
        if b2 and b2.driver_name != "S. Selvaraj":
            b2.driver_name = "S. Selvaraj"
        db.commit()
    finally:
        db.close()


def test_bus_crud_and_validation(client, admin_headers):
    """Verifies complete creation, validation bounds, update, and deletion of a fleet bus."""
    test_bus_id = "TEST-BUS-01"

    # 1. Reject invalid seat bounds
    res_seats_low = client.post(
        "/api/buses",
        json={"bus_id": test_bus_id, "seats": 5, "default_area_id": "AREA_A"},
        headers=admin_headers,
    )
    assert res_seats_low.status_code == 422

    res_seats_high = client.post(
        "/api/buses",
        json={"bus_id": test_bus_id, "seats": 150, "default_area_id": "AREA_A"},
        headers=admin_headers,
    )
    assert res_seats_high.status_code == 422

    # 2. Reject invalid corridor area
    res_bad_area = client.post(
        "/api/buses",
        json={"bus_id": test_bus_id, "seats": 55, "default_area_id": "INVALID_CORRIDOR"},
        headers=admin_headers,
    )
    assert res_bad_area.status_code == 422

    # 3. Create valid bus
    create_res = client.post(
        "/api/buses",
        json={
            "bus_id": test_bus_id,
            "seats": 60,
            "default_area_id": "AREA_A",
            "driver_name": "Test Driver Sprint5",
            "driver_phone": "+91 91234 56789",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["bus_id"] == test_bus_id
    assert created["seats"] == 60
    assert created["driver_name"] == "Test Driver Sprint5"

    # 4. Reject duplicate bus_id
    dup_res = client.post(
        "/api/buses",
        json={"bus_id": test_bus_id, "seats": 55, "default_area_id": "AREA_A"},
        headers=admin_headers,
    )
    assert dup_res.status_code == 400

    # 5. Read / List with filter
    list_res = client.get(f"/api/buses?search={test_bus_id}")
    assert list_res.status_code == 200
    buses = list_res.json()
    assert any(b["bus_id"] == test_bus_id for b in buses)

    # 6. Update bus
    upd_res = client.put(
        f"/api/buses/{test_bus_id}",
        json={"seats": 55, "registration_no": "TN 47 B 9999"},
        headers=admin_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["seats"] == 55
    assert upd_res.json()["registration_no"] == "TN 47 B 9999"

    # 7. Delete bus
    del_res = client.delete(f"/api/buses/{test_bus_id}", headers=admin_headers)
    assert del_res.status_code == 200

    # Verify deleted
    verify_res = client.get(f"/api/buses?search={test_bus_id}")
    assert not any(b["bus_id"] == test_bus_id for b in verify_res.json())


def test_bus_deletion_safeguard_against_plan_corruption(client, admin_headers):
    """Verifies that deleting a bus referenced in approved plans is blocked with HTTP 409."""
    db: Session = SessionLocal()
    test_date = "2026-11-20"
    try:
        # Create an approved plan referencing BUS-01
        plan = Plan(
            date=test_date,
            slot="morning",
            bus_id="BUS-01",
            area_id="AREA_A",
            scenario="REGULAR",
            status="APPROVED",
            total_riders=45,
            route_json="{}",
        )
        db.add(plan)
        db.commit()

        # Attempt to delete BUS-01
        res = client.delete("/api/buses/BUS-01", headers=admin_headers)
        assert res.status_code == 409
        detail = res.json()["detail"].lower()
        assert "cannot delete bus" in detail
        assert "approved dispatch plan" in detail
    finally:
        db.query(Plan).filter(Plan.date == test_date).delete()
        db.commit()
        db.close()


def test_driver_conflict_prevention_across_active_buses(client, admin_headers):
    """Verifies that the same human driver cannot be assigned to two active buses simultaneously."""
    # 1. Update BUS-01 with a specific driver
    upd1 = client.put(
        "/api/buses/BUS-01",
        json={"driver_name": "Unique Driver One", "is_active": True},
        headers=admin_headers,
    )
    assert upd1.status_code == 200

    # 2. Attempt to assign same driver to active BUS-02 -> Must fail with 400
    conflict_res = client.put(
        "/api/buses/BUS-02",
        json={"driver_name": "Unique Driver One", "is_active": True},
        headers=admin_headers,
    )
    assert conflict_res.status_code == 400
    assert "conflicting driver assignment" in conflict_res.json()["detail"].lower()

    # 3. Attempt via POST /api/buses -> Must also fail with 400
    post_conflict = client.post(
        "/api/buses",
        json={
            "bus_id": "TEST-BUS-02",
            "seats": 55,
            "default_area_id": "AREA_A",
            "driver_name": "Unique Driver One",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert post_conflict.status_code == 400
    assert "conflicting driver assignment" in post_conflict.json()["detail"].lower()


def test_driver_roster_endpoint(client):
    """Verifies GET /api/buses/drivers returns the single-source-of-truth roster."""
    res = client.get("/api/buses/drivers")
    assert res.status_code == 200
    data = res.json()
    assert "total_drivers" in data
    assert "drivers" in data
    assert data["total_drivers"] >= 50

    sample_driver = data["drivers"][0]
    assert "driver_name" in sample_driver
    assert "driver_phone" in sample_driver
    assert "assigned_bus_id" in sample_driver
    assert "status" in sample_driver
    assert sample_driver["status"] in ["ACTIVE", "INACTIVE"]

    # Test filtering by active status
    active_res = client.get("/api/buses/drivers?is_active=true")
    assert active_res.status_code == 200
    for d in active_res.json()["drivers"]:
        assert d["is_active"] is True


def test_stops_return_authoritative_student_registration_counts(client):
    """Verifies that GET /api/stops aggregates student registrations from database."""
    res = client.get("/api/stops")
    assert res.status_code == 200
    stops = res.json()
    assert len(stops) == 47

    # Verify every stop has student_count populated
    total_registered = sum(s.get("student_count", 0) for s in stops)
    assert total_registered == 2200, f"Expected 2200 total registered students, found {total_registered}"

    # Verify a specific known stop
    st_a01 = next((s for s in stops if s["stop_id"] == "ST-A01"), None)
    assert st_a01 is not None
    assert st_a01["student_count"] == 62


def test_student_registrations_endpoint_and_privacy_masking(client):
    """Verifies GET /workflow/students/registrations provides paginated data with masked SHA-256."""
    res = client.get("/api/workflow/students/registrations?page=1&page_size=25")
    assert res.status_code == 200
    data = res.json()
    assert data["total_registrations"] == 2200
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert data["total_pages"] == 88
    assert len(data["registrations"]) == 25

    # Check privacy masking
    first_reg = data["registrations"][0]
    assert "masked_student_id" in first_reg
    assert first_reg["masked_student_id"].endswith("...")
    assert len(first_reg["masked_student_id"]) <= 12
    assert "stop_id" in first_reg
    assert "stop_name" in first_reg
    assert "area_id" in first_reg

    # Test area filter
    area_res = client.get("/api/workflow/students/registrations?area_id=AREA_A&page_size=10")
    assert area_res.status_code == 200
    for r in area_res.json()["registrations"]:
        assert r["area_id"] == "AREA_A"


def test_demand_summary_endpoint(client):
    """Verifies GET /workflow/demand-summary aggregates demand and registration counts per corridor."""
    res = client.get("/api/workflow/demand-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_registered_commuters"] == 2200
    assert data["total_stops"] == 47
    assert data["total_zones"] == 5

    area_a = next((a for a in data["areas"] if a["area_id"] == "AREA_A"), None)
    assert area_a is not None
    assert area_a["registered_commuters"] > 0
    assert area_a["stops_count"] == 10
    assert area_a["baseline_buses"] == 10
    assert "p50_demand" in area_a
    assert "p90_demand" in area_a


def test_student_opt_out_preserves_approved_plan_locking(client):
    """Verifies that opt-out preference updates do not corrupt or invalidate an approved plan."""
    db: Session = SessionLocal()
    test_date = "2026-11-20"
    try:
        # Create an approved plan for this date
        plan = Plan(
            date=test_date,
            slot="morning",
            bus_id="BUS-01",
            area_id="AREA_A",
            scenario="REGULAR",
            status="APPROVED",
            total_riders=45,
            route_json="{}",
        )
        db.add(plan)
        db.commit()

        # Student opts out for this date
        res = client.post(
            "/api/workflow/student-opt-out",
            json={
                "student_roll": "21CS104",
                "traveling_today": False,
                "date": test_date,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["plan_locked"] is True
        assert "locked" in data["message"].lower()

        # The approved plan in database remains intact and APPROVED
        db_plan = db.query(Plan).filter(Plan.date == test_date).first()
        assert db_plan is not None
        assert db_plan.status == "APPROVED"
    finally:
        db.query(Plan).filter(Plan.date == test_date).delete()
        db.commit()
        db.close()


def test_upload_csv_rejects_binary_xlsx(client, admin_headers):
    """Verifies that uploading an Excel binary workbook (.xlsx) returns clear HTTP 400 (Resolves M-10)."""
    # Send fake PK zip file header
    fake_xlsx_bytes = b"PK\x03\x04\x14\x00\x06\x00binarycontentfake"
    files = {"file": ("corridor_stops.xlsx", fake_xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res = client.post("/api/workflow/upload-stops-csv", files=files, headers=admin_headers)
    assert res.status_code == 400
    assert "binary workbook (.xlsx/.xls) is not supported" in res.json()["detail"].lower()
