import pytest
import re
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.routing.vrp_solver import vrp_solver
from backend.app.models.institution import DEFAULT_VSB_CORRIDORS, seed_default_institutions, Institution
from backend.app.database import SessionLocal

client = TestClient(app)

TIME_REGEX = re.compile(r"^\d{2}:\d{2}$")


def test_vrp_solver_emits_arrival_time_and_cumulative_passengers_morning():
    """
    MAP-001 & MAP-002: Ensure VRP solver returns arrival_time matching time,
    and cumulative_passengers rolling sum for morning pickup.
    """
    stops = [
        {"stop_id": "ST-01", "name": "Stop Alpha", "lat": 10.95, "lon": 78.07, "p90_riders": 15, "registered_count": 20},
        {"stop_id": "ST-02", "name": "Stop Beta", "lat": 10.96, "lon": 78.08, "p90_riders": 25, "registered_count": 30},
        {"stop_id": "ST-03", "name": "Stop Gamma", "lat": 10.97, "lon": 78.09, "p90_riders": 10, "registered_count": 12},
    ]

    res = vrp_solver.solve("AREA_A", stops, num_buses=2, direction="MORNING_PICKUP")
    assert res["status"] == "SUCCESS"
    assert len(res["routes"]) > 0

    for route in res["routes"]:
        itinerary = route["itinerary"]
        assert len(itinerary) >= 2  # depot out, at least one stop, depot in
        
        last_cum = 0
        for step in itinerary:
            # MAP-001: arrival_time exists and matches time
            assert "arrival_time" in step, "Each step must have 'arrival_time'"
            assert "time" in step, "Each step must have 'time'"
            assert step["arrival_time"] == step["time"]
            assert TIME_REGEX.match(step["arrival_time"]), f"Invalid format {step['arrival_time']}"

            # MAP-002: cumulative_passengers rolling counter
            assert "cumulative_passengers" in step, "Step must have 'cumulative_passengers'"
            cum = step["cumulative_passengers"]
            assert cum >= last_cum, "Morning cumulative passengers must be monotonically non-decreasing"
            last_cum = cum

            # MAP-002: stop details preserved
            if step["node_type"] == "pickup_stop":
                assert "registered_count" in step
                assert "p90_riders" in step
                assert step["registered_count"] in (20, 30, 12)


def test_vrp_solver_emits_arrival_time_and_cumulative_passengers_evening():
    """
    MAP-001 & MAP-002: Ensure VRP solver evening dropoff starts with full bus load
    and cumulative_passengers decrements towards terminal.
    """
    stops = [
        {"stop_id": "ST-01", "name": "Stop Alpha", "lat": 10.95, "lon": 78.07, "p90_riders": 15, "registered_count": 20},
        {"stop_id": "ST-02", "name": "Stop Beta", "lat": 10.96, "lon": 78.08, "p90_riders": 20, "registered_count": 25},
    ]

    res = vrp_solver.solve("AREA_A", stops, num_buses=2, direction="EVENING_DROP")
    assert res["status"] == "SUCCESS"

    for route in res["routes"]:
        itinerary = route["itinerary"]
        assert len(itinerary) >= 2
        # Departure at 16:30
        assert itinerary[0]["time"] == "16:30"
        assert itinerary[0]["arrival_time"] == "16:30"
        assert itinerary[0]["node_type"] == "depot_departure"
        assert itinerary[0]["cumulative_passengers"] == route.get("route_load", route.get("total_riders"))

        # Terminal arrival
        assert itinerary[-1]["node_type"] == "depot_arrival"
        assert itinerary[-1]["cumulative_passengers"] == 0

        # Steps must have valid arrival_time
        for step in itinerary:
            assert "arrival_time" in step
            assert step["arrival_time"] == step["time"]
            assert TIME_REGEX.match(step["arrival_time"])


def test_api_routes_endpoint_includes_map_and_time_fields():
    """
    MAP-001: GET /api/routes must return itineraries with arrival_time and cumulative_passengers.
    """
    response = client.get("/api/routes?area_id=AREA_A")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "routes" in data
    assert len(data["routes"]) > 0

    for route in data["routes"]:
        for step in route["itinerary"]:
            assert "arrival_time" in step
            assert "time" in step
            assert step["arrival_time"] == step["time"]
            assert "cumulative_passengers" in step


def test_zone_metadata_cardinal_directions_consistency():
    """
    M-01: Ensure zone metadata is consistent across default VSB corridors and institutions.
    AREA_A is West, AREA_B is South, AREA_C is South-East, AREA_D is North, AREA_E is North-West.
    """
    corridor_map = {c["id"]: c["name"] for c in DEFAULT_VSB_CORRIDORS}

    assert "West" in corridor_map["AREA_A"]
    assert "South" in corridor_map["AREA_B"]
    assert "South-East" in corridor_map["AREA_C"]
    assert "North" in corridor_map["AREA_D"]
    assert "North-West" in corridor_map["AREA_E"]

    with SessionLocal() as db:
        seed_default_institutions(db)
        inst = db.query(Institution).filter(Institution.id == "VSB_KARUR").first()
        assert inst is not None
        inst_dict = inst.to_dict()
        inst_corridors = {c["id"]: c["name"] for c in inst_dict["corridors"]}
        assert "West" in inst_corridors["AREA_A"]
        assert "South" in inst_corridors["AREA_B"]
        assert "South-East" in inst_corridors["AREA_C"]
        assert "North" in inst_corridors["AREA_D"]
        assert "North-West" in inst_corridors["AREA_E"]
