import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_workflow_operational_manifest_regular_scenario():
    """Verify operational manifest generation for regular academic day."""
    response = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "REGULAR"
    assert data["total_active_buses"] > 0
    assert data["total_seats_deployed"] > 0
    assert len(data["manifest"]) > 0
    
    first_bus = data["manifest"][0]
    assert "bus_code" in first_bus
    assert "driver_name" in first_bus
    assert "driver_phone" in first_bus
    assert "departure_time" in first_bus
    assert "stops_list" in first_bus
    assert first_bus["capacity"] == 55

def test_workflow_operational_manifest_surge_scenario():
    """Verify operational manifest dynamically recalibrates under monsoon rain surge."""
    res_regular = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    res_surge = client.get("/api/workflow/operational-manifest?scenario=MONSOON_RAIN&date=2026-10-15")
    
    assert res_regular.status_code == 200
    assert res_surge.status_code == 200
    
    data_regular = res_regular.json()
    data_surge = res_surge.json()
    
    assert data_surge["scenario"] == "MONSOON_RAIN"
    assert data_surge["total_expected_riders"] > data_regular["total_expected_riders"]

def test_workflow_student_profile_lookup():
    """Verify student profile lookup by roll number returns confirmed seat and bus assignment."""
    response = client.get("/api/workflow/student-profile?roll_no=21CS104&date=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["student_roll"] == "21CS104"
    assert "assigned_bus_code" in data
    assert "seat_number" in data
    assert "Seat #" in data["seat_number"]
    assert "driver_name" in data
    assert "driver_phone" in data
    assert "pickup_time" in data
    assert data["campus_arrival"] == "08:30 AM"
    assert data["seat_guarantee"] == "CONFIRMED_NO_STANDING"

def test_workflow_student_roster_is_the_source_of_truth():
    """The commuter roster is served by the API so the frontend need not duplicate it."""
    response = client.get("/api/workflow/students")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == len(data["students"]) >= 1
    rolls = [s["roll_no"] for s in data["students"]]
    assert "21CS104" in rolls
    for student in data["students"]:
        assert {"roll_no", "name", "department"} <= set(student)


def test_student_endpoints_reject_unknown_roll_numbers():
    """
    Roll numbers outside the roster must 404 on both student endpoints.

    Previously any string was accepted, which let an unauthenticated caller
    enumerate the full 2,200-student body and flip any student's travel flag.
    """
    unknown = "99ZZ999"

    profile = client.get(f"/api/workflow/student-profile?roll_no={unknown}")
    assert profile.status_code == 404

    opt_out = client.post("/api/workflow/student-opt-out", json={
        "student_roll": unknown,
        "traveling_today": False,
    })
    assert opt_out.status_code == 404


def test_known_roster_students_all_resolve():
    """Every roster entry must return a usable profile."""
    roster = client.get("/api/workflow/students").json()["students"]
    for student in roster:
        res = client.get(f"/api/workflow/student-profile?roll_no={student['roll_no']}")
        assert res.status_code == 200, student["roll_no"]
        assert res.json()["student_roll"] == student["roll_no"]


def test_workflow_student_opt_out_and_reconfirm():
    """Verify real-time attendance opt-out and seat release workflow."""
    roll = "21CS104"
    
    # 1. Opt out
    res_opt_out = client.post("/api/workflow/student-opt-out", json={
        "student_roll": roll,
        "traveling_today": False
    })
    assert res_opt_out.status_code == 200
    data_opt_out = res_opt_out.json()
    assert data_opt_out["traveling_today"] is False
    assert "released" in data_opt_out["message"].lower()
    
    # Check profile reflects opt out
    res_prof = client.get(f"/api/workflow/student-profile?roll_no={roll}&date=2026-10-15")
    assert res_prof.json()["traveling_today"] is False
    
    # 2. Re-confirm
    res_reconfirm = client.post("/api/workflow/student-opt-out", json={
        "student_roll": roll,
        "traveling_today": True
    })
    assert res_reconfirm.status_code == 200
    data_reconfirm = res_reconfirm.json()
    assert data_reconfirm["traveling_today"] is True
    assert "re-confirmed" in data_reconfirm["message"].lower()

def test_workflow_template_csv_download():
    """Verify admin CSV template download endpoint returns valid CSV text and headers."""
    response = client.get("/api/workflow/template-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    content = response.text
    assert "stop_name" in content
    assert "student_count" in content
    assert "suggested_bus_code" in content

def test_workflow_upload_stops_csv_with_auto_geocoding(admin_headers):
    """
    Suggestion 1 Verification:
    Verify CSV ingestion auto-geocodes stops with missing coordinates into realistic GPS coordinates.
    """
    sample_csv = (
        "stop_name,zone,student_count,suggested_bus_code,latitude,longitude\n"
        "Central Cantonment,AREA_E,25,BUS-01,10.8284,78.6856\n"
        "Chatram Station,AREA_E,30,BUS-01,,\n"
        "Srirangam Temple,AREA_A,40,BUS-02,,\n"
    )
    response = client.post(
        "/api/workflow/upload-stops-csv",
        data={"csv_text": sample_csv},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_stops_imported"] == 3
    assert data["auto_geocoded_count"] == 2
    
    # Confirm geocoded stops have valid lat/lng around Trichy campus
    for st in data["stops"]:
        assert 10.0 <= st["latitude"] <= 12.0
        assert 77.0 <= st["longitude"] <= 79.5
        if st["stop_name"] == "Central Cantonment":
            assert st["auto_geocoded"] is False
        else:
            assert st["auto_geocoded"] is True

def test_workflow_upload_stops_csv_benchmark_comparison(admin_headers):
    """
    Suggestion 2 Verification:
    Verify comparative benchmark accurately calculates manual overcapacity vs.
    BUSify guaranteed zero-standing optimization and distance/diesel savings.
    """
    # Overloaded scenario: 70 students on BUS-01 (15 standing) and 30 on BUS-02
    sample_csv = (
        "stop_name,zone,student_count,suggested_bus_code,latitude,longitude\n"
        "Stop Alpha,AREA_A,35,BUS-01,10.92,78.71\n"
        "Stop Beta,AREA_A,35,BUS-01,10.94,78.73\n"
        "Stop Gamma,AREA_A,30,BUS-02,10.91,78.69\n"
    )
    response = client.post(
        "/api/workflow/upload-stops-csv",
        data={"csv_text": sample_csv},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    benchmark = data["benchmark"]
    
    # Manual static route has 15 standing students (70 - 55 = 15)
    assert benchmark["manual"]["standing_passengers"] == 15
    assert benchmark["manual"]["overloaded_buses"] == 1
    
    # BUSify optimized strictly eliminates standing
    assert benchmark["optimized"]["standing_passengers"] == 0
    assert benchmark["optimized"]["overloaded_buses"] == 0
    
    # Financial/operational savings are calculated
    savings = benchmark["savings"]
    assert savings["standing_reduced"] == 15
    assert "annual_savings_inr" in savings
    assert "km_saved_daily" in savings

