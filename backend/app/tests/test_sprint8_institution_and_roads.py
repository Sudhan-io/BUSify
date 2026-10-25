import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.routing.road_geometry_service import road_geometry_service

client = TestClient(app)

def test_institutions_list_and_active():
    """Verify listing institutions and active institution retrieval."""
    res_list = client.get("/api/institutions")
    assert res_list.status_code == 200
    data = res_list.json()
    institutions = data["institutions"]
    assert len(institutions) >= 1
    
    # Verify default active institution
    res_active = client.get("/api/institutions/active")
    assert res_active.status_code == 200
    active = res_active.json()
    assert active["id"] == "VSB_KARUR"
    assert "VSB" in active["name"]
    assert "campus_lat" in active
    assert "campus_lng" in active

def test_switch_active_institution(admin_headers):
    """Verify switching active campus changes the system configuration."""
    # First create a second campus to test switching
    payload = {
        "name": "Kongu Engineering College",
        "campus_code": "KEC-PER",
        "city": "Perundurai",
        "district": "Erode",
        "campus_lat": 11.2743,
        "campus_lng": 77.6070,
        "total_fleet_size": 30,
        "default_capacity": 55
    }
    res_create = client.post("/api/institutions", json=payload, headers=admin_headers)
    assert res_create.status_code == 200
    created_id = res_create.json()["institution"]["id"]

    res_switch = client.post(
        "/api/institutions/active",
        json={"institution_id": created_id},
        headers=admin_headers,
    )
    assert res_switch.status_code == 200
    data = res_switch.json()
    assert data["active_institution"]["id"] == created_id
    
    # Confirm active endpoint reflects switch
    res_active = client.get("/api/institutions/active")
    assert res_active.json()["id"] == created_id
    
    # Switch back to VSB_KARUR
    client.post(
        "/api/institutions/active",
        json={"institution_id": "VSB_KARUR"},
        headers=admin_headers,
    )

def test_campus_mutation_requires_officer_auth():
    """Campus registration and switching must reject unauthenticated callers."""
    payload = {
        "name": "Unauthorized College",
        "city": "Nowhere",
        "campus_lat": 10.0,
        "campus_lng": 77.0,
    }
    assert client.post("/api/institutions", json=payload).status_code == 401
    assert client.post(
        "/api/institutions/active", json={"institution_id": "VSB_KARUR"}
    ).status_code == 401

def test_create_custom_institution(admin_headers):
    """Verify dynamic creation of a new college campus with custom fleet size."""
    payload = {
        "name": "Coimbatore Institute of Technology",
        "campus_code": "CIT-CBE",
        "city": "Coimbatore",
        "campus_lat": 11.0287,
        "campus_lng": 77.0270,
        "total_fleet_size": 14,
        "default_capacity": 55
    }
    res = client.post("/api/institutions", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    created = data["institution"]
    assert created["campus_code"] == "CIT-CBE"
    assert created["campus_lat"] == 11.0287
    assert created["total_fleet_size"] == 14

def test_road_geometry_service_fallback_and_caching():
    """Verify road geometry service smoothly handles waypoints and returns coordinates."""
    waypoints = [
        {"lat": 10.9601, "lon": 78.0766},
        {"lat": 10.8284, "lon": 78.6856},
    ]
    coords = road_geometry_service.get_road_geometry(waypoints)
    assert isinstance(coords, list)
    assert len(coords) >= 2
    # Verify first coordinate format [lat, lon]
    assert len(coords[0]) == 2
    assert abs(coords[0][0] - 10.9601) < 0.05 or abs(coords[0][0] - 10.8284) < 0.05
