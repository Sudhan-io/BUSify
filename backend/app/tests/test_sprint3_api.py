import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_root_endpoint():
    """Validates the root metadata endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "version" in data

def test_api_health_check():
    """Validates system health and database connectivity."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["database_connected"] is True
    assert data["total_fleet_size"] == 50

def test_api_get_stops():
    """Validates the transit stops listing endpoint."""
    response = client.get("/api/stops")
    assert response.status_code == 200
    stops = response.json()
    assert len(stops) == 47
    assert all("lat" in s and "lon" in s and "area_id" in s for s in stops)

def test_api_get_buses():
    """Validates the fleet listing endpoint."""
    response = client.get("/api/buses")
    assert response.status_code == 200
    buses = response.json()
    assert len(buses) == 50
    assert all(b["seats"] == 55 for b in buses)

def test_api_get_forecast():
    """Validates demand forecasting endpoint for p50 and p90 quantiles."""
    response = client.get("/api/forecast?date=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-10-15"
    assert len(data["areas"]) == 5
    assert data["total_p90_demand"] >= data["total_p50_demand"]
    assert data["total_p50_demand"] > 0

def test_api_get_allocation():
    """Validates OR-Tools CP-SAT fleet allocation endpoint."""
    response = client.get("/api/allocation?date=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["OPTIMAL", "FEASIBLE"]
    assert sum(data["optimized_allocation"].values()) <= 50
    assert len(data["per_area_details"]) == 5

def test_api_get_routes():
    """Validates Capacitated VRP route generation for an area."""
    response = client.get("/api/routes?area_id=AREA_A")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["buses_utilized"] > 0
    assert len(data["routes"]) > 0
    first_route = data["routes"][0]
    assert "itinerary" in first_route
    assert first_route["total_riders"] <= 55

def test_api_get_crowding():
    """Validates student crowding advisory endpoint for a bus."""
    response = client.get("/api/crowding?bus_id=BUS-01")
    assert response.status_code == 200
    data = response.json()
    assert data["bus_id"] == "BUS-01"
    assert data["crowd_level"] in ["LOW", "MODERATE", "BUSY", "OVERCROWDED"]
    assert "utilization_pct" in data
    assert "advisory_message" in data

def test_api_simulate():
    """Validates backtesting simulation endpoint."""
    response = client.post("/api/simulate", json={"sample_days": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "summary_kpis" in data
    assert "daily_records" in data

def test_api_error_handling_invalid_area():
    """Validates that requests with an invalid area ID return 400 Bad Request."""
    response = client.get("/api/routes?area_id=INVALID_ZONE_99")
    assert response.status_code == 400
    assert "detail" in response.json()

def test_api_error_handling_nonexistent_bus():
    """Validates that requests for a nonexistent bus return 404 Not Found."""
    response = client.get("/api/crowding?bus_id=BUS-9999")
    assert response.status_code == 404
    assert "detail" in response.json()

def test_workflow_manifest_uses_canonical_baseline():
    """Validates ALLOC-001: Manifest endpoint uses canonical BASELINE_ALLOCATION."""
    from backend.app.core.simulation.simulator import BASELINE_ALLOCATION
    response = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["baseline_allocation"] == BASELINE_ALLOCATION
    assert sum(data["baseline_allocation"].values()) == 50

def test_upload_stops_csv_size_limit_rejection(admin_headers):
    """Validates endpoint security: CSV file upload exceeding 5MB returns 413."""
    large_payload = b"stop_name,zone,student_count,suggested_bus_code,latitude,longitude\n" + (b"Stop,AREA_A,10,BUS-01,10.9,78.0\n" * 180000)
    assert len(large_payload) > 5 * 1024 * 1024
    response = client.post(
        "/api/workflow/upload-stops-csv",
        files={"file": ("large_stops.csv", large_payload, "text/csv")},
        headers=admin_headers,
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()

def test_bus_registration_rejects_non_positive_seats(admin_headers):
    """Validates bus creation rejects seats < 10 with 422 to prevent ZeroDivision in crowding."""
    response = client.post(
        "/api/buses",
        json={"bus_id": "BUS-INVALID-0", "seats": 0, "default_area_id": "AREA_A"},
        headers=admin_headers,
    )
    assert response.status_code == 422
