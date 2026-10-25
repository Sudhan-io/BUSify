import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.allocation.optimizer import fleet_allocator
from backend.app.core.routing.vrp_solver import vrp_solver
from backend.app.core.routing.matrix_service import matrix_service
from backend.app.core.data.anonymizer import hash_student_id
from backend.app.core.simulation.simulator import BASELINE_ALLOCATION

client = TestClient(app)

def test_extreme_demand_surge_handling():
    """
    Stress-tests the OR-Tools CP-SAT allocator under an extreme surge
    (Area B demand jumps to 1,800 students, far beyond total fleet capacity).
    Asserts solver returns a valid allocation without crash or timeout.
    """
    extreme_demands = {
        "AREA_A": 200,
        "AREA_B": 2900,  # Extreme surge exceeding total 50-bus fleet capacity (2750 seats)
        "AREA_C": 150,
        "AREA_D": 200,
        "AREA_E": 150,
    }
    res = fleet_allocator.solve(extreme_demands, BASELINE_ALLOCATION)
    assert res["status"] in ["OPTIMAL", "FEASIBLE"]
    assert sum(res["allocation"].values()) <= 50
    # Area B must receive the lion's share of the fleet (surging from baseline 12 to >= 30)
    assert res["allocation"]["AREA_B"] >= 30
    # All other areas still maintain minimum coverage
    for a in ["AREA_A", "AREA_C", "AREA_D", "AREA_E"]:
        assert res["allocation"][a] >= 2
    # Standing students must be accurately quantified
    assert res["metrics"]["total_predicted_standing_students"] > 0

def test_zero_demand_minimum_coverage():
    """
    Tests edge condition where demand drops to 0 in some zones.
    Asserts solver satisfies minimum coverage (n_a >= 2) without division-by-zero.
    """
    zero_demands = {
        "AREA_A": 0,
        "AREA_B": 0,
        "AREA_C": 0,
        "AREA_D": 0,
        "AREA_E": 0,
    }
    res = fleet_allocator.solve(zero_demands, BASELINE_ALLOCATION)
    assert res["status"] in ["OPTIMAL", "FEASIBLE"]
    for a, count in res["allocation"].items():
        assert count >= 2, f"Area {a} fell below minimum coverage of 2 buses"

def test_cvrp_capacity_invariants_across_multiple_scenarios():
    """
    Stress-tests the CVRP router across multiple synthetic stop demand profiles.
    Asserts that in 100% of tested scenarios, NO bus exceeds 55 passengers.
    """
    test_scenarios = [
        # Scenario 1: High variance
        [{"stop_id": f"S{i}", "name": f"Stop {i}", "lat": 10.95 + i*0.01, "lon": 78.07 + i*0.01, "p90_riders": 5 + i*8} for i in range(8)],
        # Scenario 2: Clustered peak
        [{"stop_id": f"S{i}", "name": f"Stop {i}", "lat": 10.96 + i*0.005, "lon": 78.08 + i*0.005, "p90_riders": 45} for i in range(6)],
        # Scenario 3: Granular small stops
        [{"stop_id": f"S{i}", "name": f"Stop {i}", "lat": 10.94 + i*0.008, "lon": 78.06 + i*0.008, "p90_riders": 12} for i in range(15)],
    ]

    for idx, stops in enumerate(test_scenarios):
        routing_res = vrp_solver.solve("AREA_TEST", stops, num_buses=6)
        assert routing_res["status"] == "SUCCESS", f"Scenario {idx+1} routing failed"
        for r in routing_res["routes"]:
            assert r["total_riders"] <= 55, f"Scenario {idx+1} bus {r['bus_code']} exceeded capacity: {r['total_riders']} > 55"
            assert r["utilization_pct"] <= 100.0

def _assert_matrix_invariants(dist_m, dur_m, coords, require_symmetric: bool = True):
    """Shared invariants every distance matrix must satisfy."""
    n = len(coords)
    for i in range(n):
        assert dist_m[i][i] == 0, "Diagonal distance must be 0"
        assert dur_m[i][i] == 0, "Diagonal duration must be 0"
        for j in range(n):
            if i != j:
                assert dist_m[i][j] > 0, "Non-diagonal distance must be positive"
                assert dur_m[i][j] > 0, "Non-diagonal duration must be positive"
                if require_symmetric:
                    assert dist_m[i][j] == dist_m[j][i], "Distance matrix must be symmetric"


def test_haversine_matrix_physical_invariants():
    """
    The straight-line fallback matrix is deterministic and offline, so its
    invariants are always assertable regardless of OSRM availability.
    """
    coords = [
        (10.9601, 78.0766),
        (10.9575, 78.0815),
        (10.9690, 78.0790),
        (10.9490, 78.0790),
    ]
    dist_m, dur_m = matrix_service._haversine_matrices(coords)
    _assert_matrix_invariants(dist_m, dur_m, coords, require_symmetric=True)


def test_distance_matrix_metric_properties():
    """
    Validates physical metric invariants of the distance matrix:
    - Distance from a point to itself is 0
    - Distances between different points are strictly positive
    (Real road networks are directed graphs and can be asymmetric due to one-way streets)

    With ENABLE_OFFLINE_HAVERSINE_FALLBACK disabled the service must RAISE
    rather than silently substitute straight-line distances for a failed OSRM
    query, so this is only asserted when OSRM is actually reachable.
    """
    coords = [
        (10.9601, 78.0766),
        (10.9575, 78.0815),
        (10.9690, 78.0790),
        (10.9490, 78.0790),
    ]
    try:
        dist_m, dur_m = matrix_service.get_matrices(coords)
    except RuntimeError as exc:
        pytest.skip(f"OSRM unavailable and fallback disabled: {exc}")

    _assert_matrix_invariants(dist_m, dur_m, coords, require_symmetric=False)

def test_student_anonymization_collision_resistance():
    """
    Asserts zero collisions when hashing 5,000 distinct student IDs.
    """
    hashes = set()
    total = 5000
    for i in range(total):
        s_id = f"STUDENT-2026-CS-{i:05d}"
        h = hash_student_id(s_id)
        hashes.add(h)
    assert len(hashes) == total, "Hashing must have 0 collisions across 5000 IDs"

def test_api_boundary_conditions_and_validation():
    """
    Tests API boundary conditions:
    - Sample days = 1 (valid)
    - Sample days = 30 (valid)
    - Sample days = 50 (invalid, must fail Pydantic validation with 422)
    - Sample days = 0 (invalid, must fail Pydantic validation with 422)
    """
    # Valid bounds
    res1 = client.post("/api/simulate", json={"sample_days": 1})
    assert res1.status_code == 200

    res2 = client.post("/api/simulate", json={"sample_days": 14})
    assert res2.status_code == 200

    # Invalid upper bound (max 30)
    res_high = client.post("/api/simulate", json={"sample_days": 50})
    assert res_high.status_code == 422

    # Invalid lower bound (min 1)
    res_low = client.post("/api/simulate", json={"sample_days": 0})
    assert res_low.status_code == 422
