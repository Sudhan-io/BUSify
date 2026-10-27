import pytest
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.plan import Plan
from backend.app.models.bus import Bus
from backend.app.models.stop import Stop
from backend.app.models.student_attendance import StudentAttendance
from backend.app.api.routes_workflow import _get_all_stops_cached, invalidate_stops_cache

client = TestClient(app)


def test_stops_caching_eliminates_n_plus_one_queries():
    """
    DATA-006 (H-10): Verify Stop query caching avoids querying DB on every profile lookup,
    and invalidate_stops_cache properly clears the cache.
    """
    with SessionLocal() as db:
        # Initial load populates cache
        invalidate_stops_cache()
        stops1 = _get_all_stops_cached(db)
        assert len(stops1) > 0

        # Second call returns identical cached objects
        stops2 = _get_all_stops_cached(db)
        assert stops1 is stops2

        # Cache invalidation clears memory
        invalidate_stops_cache()
        stops3 = _get_all_stops_cached(db)
        assert len(stops3) == len(stops1)


def test_student_profile_fields_and_unapproved_plan_state():
    """
    SEC-002 & STUDENT-001: When no approved dispatch plan exists for the date,
    student profile returns provisional estimates, is_approved_dispatch=False,
    and plan_status='PENDING_APPROVAL'.
    """
    test_date = "2026-11-20"
    with SessionLocal() as db:
        db.query(Plan).filter(Plan.date == test_date).delete()
        db.commit()

    res = client.get(f"/api/workflow/student-profile?roll_no=21CS104&date={test_date}")
    assert res.status_code == 200
    data = res.json()

    assert data["student_roll"] == "21CS104"
    assert data["student_name"] == "K. Vignesh"
    assert "student_hash" in data
    assert "assigned_stop" in data
    assert "assigned_bus_code" in data
    assert "seat_number" in data
    assert data["seat_guarantee"] == "CONFIRMED_NO_STANDING"
    assert data["is_approved_dispatch"] is False
    assert data["plan_status"] == "PENDING_APPROVAL"
    assert data["service_status"] in ["ON_SCHEDULE", "SCHEDULE_TIGHT", "ABSENCE_RECORDED"]
    assert "pickup_time" in data
    assert "occupancy_pct" in data


def test_student_profile_sources_from_approved_plan():
    """
    STUDENT-001 & ALLOC-002: When an approved plan exists in the database,
    the student's profile consumes the authoritative assigned vehicle and driver.
    """
    test_date = "2026-11-21"
    with SessionLocal() as db:
        db.query(Plan).filter(Plan.date == test_date).delete()

        # Seed an approved plan with a distinct route
        route_data = {
            "bus_code": "BUS-05",
            "driver_name": "R. Murugan (Official)",
            "driver_phone": "+91 94433 99999",
            "capacity": 55,
            "allocated_riders": 45,
            "departure_time": "07:10 AM",
            "stops_list": ["Karudayampalayam Bus Stop", "VSB College Gate Arch"],
            "stops_detail": [
                {"stop_id": "ST-A01", "name": "Karudayampalayam Bus Stop", "time": "07:25"},
                {"stop_id": "ST-A02", "name": "VSB College Gate Arch", "time": "07:35"},
            ]
        }
        plan = Plan(
            date=test_date,
            slot="morning",
            bus_id="BUS-05",
            area_id="AREA_A",
            scenario="REGULAR",
            status="APPROVED",
            total_riders=45,
            route_json=json.dumps(route_data),
            created_at=datetime.now(timezone.utc),
        )
        db.add(plan)
        db.commit()

    # Query profile for 21CS104 on test_date
    res = client.get(f"/api/workflow/student-profile?roll_no=21CS104&date={test_date}")
    assert res.status_code == 200
    data = res.json()

    assert data["is_approved_dispatch"] is True
    assert data["plan_status"] == "APPROVED"
    assert "driver_name" in data
    assert "driver_phone" in data

    # Cleanup test plan
    with SessionLocal() as db:
        db.query(Plan).filter(Plan.date == test_date).delete()
        db.commit()


def test_commuter_enumeration_protection():
    """
    NAV-003 & SEC-002: Unknown or unauthenticated roll numbers are rejected with 404,
    preventing user enumeration over the student population.
    """
    res = client.get("/api/workflow/student-profile?roll_no=FAKE_ROLL_123")
    assert res.status_code == 404
    assert "not a registered commuter" in res.json()["detail"]

    opt_out_res = client.post("/api/workflow/student-opt-out", json={
        "student_roll": "FAKE_ROLL_123",
        "traveling_today": False
    })
    assert opt_out_res.status_code == 404


def test_student_attendance_opt_out_updates_profile():
    """
    Verify toggling opt-out updates the student's status, occupancy, and service_status.
    """
    roll = "22ME045"
    test_date = "2026-11-22"

    # 1. Opt out
    res1 = client.post("/api/workflow/student-opt-out", json={
        "student_roll": roll,
        "traveling_today": False,
        "date": test_date
    })
    assert res1.status_code == 200
    assert res1.json()["traveling_today"] is False

    # 2. Check profile reflects absence
    prof1 = client.get(f"/api/workflow/student-profile?roll_no={roll}&date={test_date}").json()
    assert prof1["traveling_today"] is False
    assert prof1["service_status"] == "ABSENCE_RECORDED"
    assert prof1["crowd_level"] == "LOW"

    # 3. Re-confirm
    res2 = client.post("/api/workflow/student-opt-out", json={
        "student_roll": roll,
        "traveling_today": True,
        "date": test_date
    })
    assert res2.status_code == 200
    assert res2.json()["traveling_today"] is True

    # 4. Check profile reflects traveling
    prof2 = client.get(f"/api/workflow/student-profile?roll_no={roll}&date={test_date}").json()
    assert prof2["traveling_today"] is True
    assert prof2["service_status"] != "ABSENCE_RECORDED"
