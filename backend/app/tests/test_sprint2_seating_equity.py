import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.allocation.equity import compute_seating_equity

client = TestClient(app)

def test_seating_equity_known_values_variance():
    """Verify that multiple valid areas with known, different utilization produce exact expected variance and equity."""
    # Area A: 80 / 100 = 0.80; Area B: 60 / 100 = 0.60
    # Mean = 0.70
    # Diffs = (+0.10, -0.10) -> squared diffs = (0.01, 0.01)
    # Variance = 0.01 / 2 = 0.010000
    # Std = 0.10
    # CV = 0.10 / 0.70 = 0.142857...
    # Consistency = (1 - 0.142857...) * 100 = 85.714...% -> rounded to 85.7%
    metrics = {
        "AREA_A": {"riders": 80, "capacity": 100},
        "AREA_B": {"riders": 60, "capacity": 100},
    }
    res = compute_seating_equity(metrics)
    assert res["equity_status"] == "VALID"
    assert res["area_utilization_variance"] == 0.01
    assert res["area_utilization_std"] == 0.1
    assert res["seating_equity_pct"] == 85.7
    assert res["mean_area_utilization_pct"] == 70.0
    assert res["measured_areas_count"] == 2
    assert res["per_area_utilization_pct"] == {"AREA_A": 80.0, "AREA_B": 60.0}

def test_seating_equity_equal_utilization_zero_variance():
    """Verify that multiple valid areas with equal non-zero utilization produce zero variance and 100% consistency."""
    metrics = {
        "AREA_A": {"riders": 45, "capacity": 50},
        "AREA_B": {"riders": 90, "capacity": 100},
        "AREA_C": {"riders": 135, "capacity": 150},
    }
    # All areas have utilization 0.90 (90%)
    res = compute_seating_equity(metrics)
    assert res["equity_status"] == "VALID"
    assert res["area_utilization_variance"] == 0.0
    assert res["area_utilization_std"] == 0.0
    assert res["seating_equity_pct"] == 100.0
    assert res["mean_area_utilization_pct"] == 90.0
    assert res["measured_areas_count"] == 3

def test_seating_equity_zero_demand_across_all_areas():
    """Verify that when every area has 0 riders, score is None (not a fabricated 100%) and status is ZERO_DEMAND."""
    metrics = {
        "AREA_A": {"riders": 0, "capacity": 50},
        "AREA_B": {"riders": 0, "capacity": 50},
    }
    res = compute_seating_equity(metrics)
    assert res["equity_status"] == "ZERO_DEMAND"
    assert res["seating_equity_pct"] is None
    assert res["area_utilization_variance"] == 0.0
    assert res["area_utilization_std"] == 0.0
    assert res["mean_area_utilization_pct"] == 0.0
    assert res["measured_areas_count"] == 2
    assert res["per_area_utilization_pct"] == {"AREA_A": 0.0, "AREA_B": 0.0}

def test_seating_equity_empty_dataset():
    """Verify empty dataset returns None score and UNAVAILABLE status."""
    empty_res = compute_seating_equity({})
    assert empty_res["equity_status"] == "UNAVAILABLE"
    assert empty_res["seating_equity_pct"] is None
    assert empty_res["area_utilization_variance"] is None
    assert empty_res["area_utilization_std"] is None
    assert empty_res["mean_area_utilization_pct"] is None
    assert empty_res["measured_areas_count"] == 0
    assert empty_res["per_area_utilization_pct"] == {}

def test_seating_equity_single_valid_area():
    """Verify exactly one valid area cannot establish cross-corridor consistency (returns None, INSUFFICIENT_AREAS)."""
    single_res = compute_seating_equity({"AREA_A": {"riders": 40, "capacity": 50}})
    assert single_res["equity_status"] == "INSUFFICIENT_AREAS"
    assert single_res["seating_equity_pct"] is None
    assert single_res["area_utilization_variance"] is None
    assert single_res["measured_areas_count"] == 1
    assert single_res["mean_area_utilization_pct"] == 80.0
    assert single_res["per_area_utilization_pct"] == {"AREA_A": 80.0}

def test_seating_equity_invalid_and_missing_data_handling():
    """Verify non-numeric, negative, None, or zero-capacity records are safely excluded."""
    metrics = {
        "AREA_VALID_1": {"riders": 50, "capacity": 100},       # 50%
        "AREA_ZERO_CAP": {"riders": 20, "capacity": 0},        # zero cap -> exclude
        "AREA_NEG_CAP": {"riders": 20, "capacity": -50},       # negative cap -> exclude
        "AREA_NONE_CAP": {"riders": 20, "capacity": None},      # None cap -> exclude
        "AREA_STR_CAP": {"riders": 20, "capacity": "invalid"},  # non-numeric cap -> exclude
        "AREA_NEG_RIDERS": {"riders": -5, "capacity": 50},     # negative riders -> exclude
        "AREA_STR_RIDERS": {"riders": "bad", "capacity": 50},  # non-numeric riders -> exclude
        "AREA_VALID_2": {"riders": 50, "capacity": 100},       # 50%
    }
    res = compute_seating_equity(metrics)
    assert res["equity_status"] == "VALID"
    assert res["measured_areas_count"] == 2
    assert "AREA_VALID_1" in res["per_area_utilization_pct"]
    assert "AREA_VALID_2" in res["per_area_utilization_pct"]
    assert "AREA_ZERO_CAP" not in res["per_area_utilization_pct"]
    assert res["area_utilization_variance"] == 0.0
    assert res["seating_equity_pct"] == 100.0

def test_seating_equity_deduplicates_vehicles_preventing_capacity_inflation():
    """Verify bus allocations deduplicate by bus ID so duplicate route assignments do not inflate capacity."""
    metrics = {
        "AREA_A": {
            "riders": 40,
            "buses": [
                {"bus_id": "BUS-01", "seats": 50},
                {"bus_id": "BUS-01", "seats": 50},  # duplicate leg for same physical bus
            ]
        },
        "AREA_B": {
            "riders": 40,
            "buses": [
                {"bus_id": "BUS-02", "seats": 50},
            ]
        }
    }
    # Without deduplication, Area A would have 100 seats (40% util) vs Area B 50 seats (80% util).
    # With deduplication, Area A has 50 seats (80% util) == Area B 50 seats (80% util).
    res = compute_seating_equity(metrics)
    assert res["equity_status"] == "VALID"
    assert res["measured_areas_count"] == 2
    assert res["per_area_utilization_pct"]["AREA_A"] == 80.0
    assert res["per_area_utilization_pct"]["AREA_B"] == 80.0
    assert res["area_utilization_variance"] == 0.0
    assert res["seating_equity_pct"] == 100.0

def test_seating_equity_asymmetric_zero_demand():
    """Verify that when one area has demand and another has zero demand, equity penalizes the imbalance."""
    metrics = {
        "AREA_A": {"riders": 100, "capacity": 100},  # 100%
        "AREA_B": {"riders": 0, "capacity": 100},    # 0%
    }
    # Mean = 0.50, Variance = 0.25, Std = 0.50, CV = 1.0, Equity = 0.0%
    res = compute_seating_equity(metrics)
    assert res["equity_status"] == "VALID"
    assert res["area_utilization_variance"] == 0.25
    assert res["seating_equity_pct"] == 0.0

def test_api_operational_manifest_includes_equity_metrics():
    """Verify that GET /api/workflow/operational-manifest exposes seating equity and status fields."""
    res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()

    assert "seating_equity_pct" in data
    assert isinstance(data["seating_equity_pct"], (int, float))
    assert 0.0 <= data["seating_equity_pct"] <= 100.0

    assert "area_utilization_variance" in data
    assert isinstance(data["area_utilization_variance"], float)
    assert data["area_utilization_variance"] >= 0.0

    assert "per_area_utilization_pct" in data
    assert isinstance(data["per_area_utilization_pct"], dict)
    for area_id in ["AREA_A", "AREA_B", "AREA_C", "AREA_D", "AREA_E"]:
        assert area_id in data["per_area_utilization_pct"]
        assert 0.0 <= data["per_area_utilization_pct"][area_id] <= 200.0

    assert "equity_status" in data
    assert data["equity_status"] == "VALID"
    assert data["seating_equity_pct"] > 90.0

def test_api_manifest_surge_scenario_equity_computation():
    """Verify seating equity recalibrates under surge conditions."""
    res = client.get("/api/workflow/operational-manifest?scenario=MONSOON_RAIN&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()

    assert data["seating_equity_pct"] > 0.0
    assert data["area_utilization_variance"] >= 0.0
    assert data["equity_status"] == "VALID"
