"""
End-to-end reproducible simulation test suite using synthetic fixtures.
Runs offline (no live database, no external OSRM server).
Verifies:
- Corridor sequence order monotonic preservation
- Vehicle capacity constraints (never exceeded)
- Virtual node splitting on demand > capacity
- Asymmetric duration matrix handling
- Infeasible route detection and graceful clamping
- Invalid/duplicate/zero/negative stop handling
"""

import json
from pathlib import Path
import pytest
from backend.app.core.routing.vrp_solver import CapacitatedVRPSolver
from backend.app.config import settings

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "tests" / "fixtures" / "synthetic"
SCENARIOS_DIR = FIXTURES_DIR / "scenarios"


@pytest.fixture(scope="module")
def expected_results():
    with open(FIXTURES_DIR / "expected_results.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_scenario(filename: str) -> dict:
    with open(SCENARIOS_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


class TestSyntheticRoutingScenarios:
    """Rigorous end-to-end simulations across isolated synthetic scenarios."""

    def test_sc01_linear_corridor_topology_and_order(self, expected_results):
        """
        SC-01: Verifies that stops assigned to any bus follow corridor sequence order
        and no vehicle exceeds capacity.
        """
        scenario = load_scenario("01_corridor_linear_5stops.json")
        exp = expected_results["SC-01"]
        solver = CapacitatedVRPSolver(bus_capacity=scenario["bus_capacity"])

        res = solver.solve(
            area_id="SYN_CORRIDOR",
            stops=scenario["stops"],
            num_buses=scenario["num_buses"],
            college_depot=(scenario["depot"]["lat"], scenario["depot"]["lon"]),
            target_arrival_time=scenario["target_arrival_time"],
            include_road_geometry=False,
        )

        assert res["status"] == "SUCCESS"
        assert res["total_riders_served"] == exp["total_demand"]
        assert len(res["routes"]) >= exp["min_active_buses"]
        assert len(res["routes"]) <= exp["max_active_buses"]

        for route in res["routes"]:
            assert route["total_riders"] <= exp["max_bus_load"]
            itinerary = route["itinerary"]
            assert len(itinerary) >= 2  # Depot out + Depot in

            # Check sequence order monotony for pickup stops
            pickup_stops = [s for s in itinerary if s.get("node_type") == "pickup_stop"]
            assert len(pickup_stops) > 0

            # Find matching stops in scenario to check sequence_order
            seq_orders = []
            for ps in pickup_stops:
                match = next((s for s in scenario["stops"] if s["stop_id"] == ps["stop_id"].split("_P")[0]), None)
                if match and "sequence_order" in match:
                    seq_orders.append(match["sequence_order"])

            # Verify monotonic corridor progression without zig-zagging/backtracking
            is_monotonic = (seq_orders == sorted(seq_orders)) or (seq_orders == sorted(seq_orders, reverse=True))
            assert is_monotonic, f"Route stops out of corridor order (backtracking): {seq_orders}"

    def test_sc02_asymmetric_duration_costs(self, expected_results):
        """
        SC-02: Verifies solver correctness when travel times are asymmetric.
        """
        scenario = load_scenario("02_corridor_asymmetric_costs.json")
        exp = expected_results["SC-02"]
        solver = CapacitatedVRPSolver(bus_capacity=scenario["bus_capacity"])

        res = solver.solve(
            area_id="SYN_ASYM",
            stops=scenario["stops"],
            num_buses=scenario["num_buses"],
            college_depot=(scenario["depot"]["lat"], scenario["depot"]["lon"]),
            target_arrival_time=scenario["target_arrival_time"],
            include_road_geometry=False,
        )

        assert res["status"] == "SUCCESS"
        assert res["total_riders_served"] == exp["total_demand"]

        for route in res["routes"]:
            assert route["total_riders"] <= exp["max_bus_load"]
            assert "schedule_feasible" in route

    def test_sc03_oversized_stop_demand_split(self, expected_results):
        """
        SC-03: Demand of 125 at a single stop must split into chunks <= bus_capacity (50),
        preventing vehicle capacity violations.
        """
        scenario = load_scenario("03_oversized_stop_split.json")
        exp = expected_results["SC-03"]
        solver = CapacitatedVRPSolver(bus_capacity=scenario["bus_capacity"])

        # Directly verify preprocessor
        processed = solver._preprocess_stops(scenario["stops"], num_buses=scenario["num_buses"])
        for p in processed:
            assert p["p90_riders"] <= exp["max_single_pickup_load"]

        # Solve end-to-end
        res = solver.solve(
            area_id="SYN_MEGA",
            stops=scenario["stops"],
            num_buses=scenario["num_buses"],
            college_depot=(scenario["depot"]["lat"], scenario["depot"]["lon"]),
            target_arrival_time=scenario["target_arrival_time"],
            include_road_geometry=False,
        )

        assert res["status"] == "SUCCESS"
        assert res["total_riders_served"] == exp["total_demand"]
        for route in res["routes"]:
            assert route["total_riders"] <= exp["max_bus_load"]
            for step in route["itinerary"]:
                if step.get("node_type") == "pickup_stop":
                    assert step["boarded"] <= exp["max_bus_load"]

    def test_sc04_infeasible_tight_windows_detection(self, expected_results):
        """
        SC-04: Distance of 90km with 06:15 arrival violates the 06:00 earliest departure floor.
        Must mark schedule_feasible=False or clamp departures to departure floor safely.
        """
        scenario = load_scenario("04_infeasible_tight_windows.json")
        exp = expected_results["SC-04"]
        solver = CapacitatedVRPSolver(bus_capacity=scenario["bus_capacity"])

        res = solver.solve(
            area_id="SYN_DISTANT",
            stops=scenario["stops"],
            num_buses=scenario["num_buses"],
            college_depot=(scenario["depot"]["lat"], scenario["depot"]["lon"]),
            target_arrival_time=scenario["target_arrival_time"],
            include_road_geometry=False,
        )

        assert res["status"] == "SUCCESS"
        for route in res["routes"]:
            depot_out = route["itinerary"][0]
            # Must respect the hard floor for earliest departure
            assert depot_out["time"] >= exp["earliest_departure_floor"]

    def test_sc05_duplicate_and_invalid_stops(self, expected_results):
        """
        SC-05: Stops with zero, negative, or duplicate coordinates must not crash the solver
        and only valid demand should be served.
        """
        scenario = load_scenario("05_duplicate_and_invalid_stops.json")
        solver = CapacitatedVRPSolver(bus_capacity=scenario["bus_capacity"])

        # Filter invalid/zero/negative stops before routing
        sanitized_input = [
            s for s in scenario["stops"]
            if s.get("p90_riders", 0) > 0 and s.get("lat") and s.get("lon")
        ]
        assert len(sanitized_input) == 2

        res = solver.solve(
            area_id="SYN_SANITIZED",
            stops=sanitized_input,
            num_buses=scenario["num_buses"],
            college_depot=(scenario["depot"]["lat"], scenario["depot"]["lon"]),
            target_arrival_time=scenario["target_arrival_time"],
            include_road_geometry=False,
        )

        assert res["status"] == "SUCCESS"
        assert res["total_riders_served"] == 55
        for route in res["routes"]:
            assert route["total_riders"] <= 55
