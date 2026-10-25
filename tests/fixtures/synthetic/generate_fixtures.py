"""
Deterministic Synthetic Fixture Generator for BUSify Route Optimization.
Creates isolated scenarios testing various corridor topologies, capacity limits,
asymmetric road costs, and invalid edge cases.
"""

import json
import os
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = FIXTURES_DIR / "scenarios"
SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

VSB_CAMPUS = {
    "name": "VSB Engineering College Campus Hub",
    "lat": 10.9322,
    "lon": 78.0744,
}

SCENARIOS = {
    "01_corridor_linear_5stops.json": {
        "scenario_id": "SC-01",
        "description": "Standard linear 5-stop corridor along Karur Road with moderate demand within fleet capacity.",
        "depot": VSB_CAMPUS,
        "bus_capacity": 55,
        "num_buses": 3,
        "target_arrival_time": "08:30",
        "stops": [
            {"stop_id": "SYN_A1", "name": "Karur Bus Stand Central", "lat": 10.9601, "lon": 78.0766, "sequence_order": 1, "p90_riders": 35},
            {"stop_id": "SYN_A2", "name": "Vengamedu Junction", "lat": 10.9712, "lon": 78.0811, "sequence_order": 2, "p90_riders": 20},
            {"stop_id": "SYN_A3", "name": "Gandhigramam South", "lat": 10.9834, "lon": 78.0855, "sequence_order": 3, "p90_riders": 40},
            {"stop_id": "SYN_A4", "name": "Pasupathipalayam Bypass", "lat": 10.9950, "lon": 78.0920, "sequence_order": 4, "p90_riders": 25},
            {"stop_id": "SYN_A5", "name": "Thanthonimalai Ring", "lat": 11.0080, "lon": 78.1010, "sequence_order": 5, "p90_riders": 15},
        ]
    },
    "02_corridor_asymmetric_costs.json": {
        "scenario_id": "SC-02",
        "description": "Corridor with asymmetric travel times due to one-way bridges and morning express lanes.",
        "depot": VSB_CAMPUS,
        "bus_capacity": 55,
        "num_buses": 2,
        "target_arrival_time": "08:30",
        "stops": [
            {"stop_id": "SYN_ASYM_1", "name": "North One-Way Toll Plaza", "lat": 10.9850, "lon": 78.0700, "sequence_order": 1, "p90_riders": 30},
            {"stop_id": "SYN_ASYM_2", "name": "Industrial Estate Flyover", "lat": 10.9980, "lon": 78.0820, "sequence_order": 2, "p90_riders": 25},
            {"stop_id": "SYN_ASYM_3", "name": "River Bridge Return Loop", "lat": 11.0120, "lon": 78.0950, "sequence_order": 3, "p90_riders": 20},
            {"stop_id": "SYN_ASYM_4", "name": "Bypass Cross Junction", "lat": 11.0250, "lon": 78.1050, "sequence_order": 4, "p90_riders": 15},
        ],
        # Custom asymmetric duration matrix: depot (0), stop 1 (1), stop 2 (2), stop 3 (3), stop 4 (4)
        "duration_matrix": [
            [0, 600, 950, 1400, 1800],
            [900, 0, 320, 750, 1100],   # returning to depot takes 900s vs 600s forward due to one-way
            [1300, 480, 0, 400, 800],
            [1800, 900, 520, 0, 420],
            [2300, 1300, 950, 500, 0],
        ]
    },
    "03_oversized_stop_split.json": {
        "scenario_id": "SC-03",
        "description": "Single high-density transit junction whose ridership (125) exceeds physical bus capacity (50).",
        "depot": VSB_CAMPUS,
        "bus_capacity": 50,
        "num_buses": 4,
        "target_arrival_time": "08:30",
        "stops": [
            {"stop_id": "SYN_MEGA_1", "name": "Central Railway Junction Hub", "lat": 10.9650, "lon": 78.0800, "sequence_order": 1, "p90_riders": 125},
            {"stop_id": "SYN_NORM_2", "name": "South Bus Stand Feeder", "lat": 10.9780, "lon": 78.0880, "sequence_order": 2, "p90_riders": 35},
        ]
    },
    "04_infeasible_tight_windows.json": {
        "scenario_id": "SC-04",
        "description": "Perimeter stops 90km away with an impossible arrival deadline (06:30) violating the 06:00 earliest departure floor.",
        "depot": VSB_CAMPUS,
        "bus_capacity": 55,
        "num_buses": 2,
        "target_arrival_time": "06:15",
        "stops": [
            {"stop_id": "SYN_DISTANT_1", "name": "Namakkal Far Border", "lat": 11.2189, "lon": 78.1674, "sequence_order": 1, "p90_riders": 25},
            {"stop_id": "SYN_DISTANT_2", "name": "Rasipuram Outpost", "lat": 11.4633, "lon": 78.1818, "sequence_order": 2, "p90_riders": 20},
        ]
    },
    "05_duplicate_and_invalid_stops.json": {
        "scenario_id": "SC-05",
        "description": "Robustness test with duplicate coordinates, zero demand, and negative passenger loads.",
        "depot": VSB_CAMPUS,
        "bus_capacity": 55,
        "num_buses": 2,
        "target_arrival_time": "08:30",
        "stops": [
            {"stop_id": "SYN_VALID_1", "name": "Legitimate Stop Alpha", "lat": 10.9500, "lon": 78.0700, "sequence_order": 1, "p90_riders": 30},
            {"stop_id": "SYN_DUP_1", "name": "Duplicate of Alpha", "lat": 10.9500, "lon": 78.0700, "sequence_order": 2, "p90_riders": 0},
            {"stop_id": "SYN_ZERO", "name": "Zero Demand Dormant Stop", "lat": 10.9620, "lon": 78.0750, "sequence_order": 3, "p90_riders": 0},
            {"stop_id": "SYN_NEG", "name": "Negative Demand Invalid Stop", "lat": 10.9700, "lon": 78.0800, "sequence_order": 4, "p90_riders": -5},
            {"stop_id": "SYN_VALID_2", "name": "Legitimate Stop Beta", "lat": 10.9850, "lon": 78.0900, "sequence_order": 5, "p90_riders": 25},
        ]
    }
}

EXPECTED_RESULTS = {
    "SC-01": {
        "min_active_buses": 2,
        "max_active_buses": 3,
        "total_demand": 135,
        "max_bus_load": 55,
        "requires_monotonic_sequence": True,
        "expected_schedule_feasible": True,
    },
    "SC-02": {
        "min_active_buses": 2,
        "max_active_buses": 2,
        "total_demand": 90,
        "max_bus_load": 55,
        "supports_asymmetric_matrix": True,
        "expected_schedule_feasible": True,
    },
    "SC-03": {
        "total_demand": 160,
        "max_bus_load": 50,
        "expected_virtual_splits": True,
        "max_single_pickup_load": 50,
        "min_active_buses": 4,
    },
    "SC-04": {
        "expected_schedule_feasible": False,
        "clamps_to_earliest_departure": True,
        "earliest_departure_floor": "06:00",
    },
    "SC-05": {
        "filtered_valid_stops_count": 2,
        "total_valid_demand": 55,
        "max_bus_load": 55,
        "sanitizer_discards_invalid": True,
    }
}


def generate_all():
    for filename, payload in SCENARIOS.items():
        filepath = SCENARIOS_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Generated: {filepath}")

    expected_path = FIXTURES_DIR / "expected_results.json"
    with open(expected_path, "w", encoding="utf-8") as f:
        json.dump(EXPECTED_RESULTS, f, indent=2)
    print(f"Generated expectations: {expected_path}")


if __name__ == "__main__":
    generate_all()
