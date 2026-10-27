import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.allocation.equity import compute_seating_equity

client = TestClient(app)

def test_seating_equity_known_values_variance():
    """Verify that known area utilization values produce exact expected variance and equity."""
    # Area A: 80 / 100 = 0.80; Area B: 60 / 100 = 0.60
    # Mean = 0.70
    # Diffs = (+0.10, -0.10) -> squared diffs = (0.01, 0.01)
    # Variance = 0.01 / 2 = 0.010000
    # Std = 0.10
    # CV = 0.10 / 0.70 = 0.142857...
    # Equity = (1 - 0.142857...) * 100 = 85.714...% -> rounded to 85.7%
    metrics = {
        "AREA_A": {"riders": 80, "capacity": 100},
        "AREA_B": {"riders": 60, "capacity": 100},
    }
    res = compute_seating_equity(metrics)
    assert res["area_utilization_variance"] == 0.01
    assert res["area_utilization_std"] == 0.1
    assert res["seating_equity_pct"] == 85.7
    assert res["mean_area_utilization_pct"] == 70.0
    assert res["measured_areas_count"] == 2
    assert res["per_area_utilization_pct"] == {"AREA_A": 80.0, "AREA_B": 60.0}

def test_seating_equity_equal_utilization_zero_variance():
    """Verify that equal utilization across all areas produces zero variance and 100% equity."""
    metrics = {
        "AREA_A": {"riders": 45, "capacity": 50},
        "AREA_B": {"riders": 90, "capacity": 100},
        "AREA_C": {"riders": 135, "capacity": 150},
    }
    # All areas have utilization 0.90 (90%)
    res = compute_seating_equity(metrics)
    assert res["area_utilization_variance"] == 0.0
    assert res["area_utilization_std"] == 0.0
    assert res["seating_equity_pct"] == 100.0
    assert res["mean_area_utilization_pct"] == 90.0
    assert res["measured_areas_count"] == 3

def test_seating_equity_empty_and_single_area():
    """Verify edge cases for empty input and single-area input."""
    # Empty
    empty_res = compute_seating_equity({})
    assert empty_res["seating_equity_pct"] == 0.0
    assert empty_res["area_utilization_variance"] == 0.0
    assert empty_res["measured_areas_count"] == 0

    # Single area (no cross-area disparity possible)
    single_res = compute_seating_equity({"AREA_A": {"riders": 40, "capacity": 50}})
    assert single_res["seating_equity_pct"] == 100.0
    assert single_res["area_utilization_variance"] == 0.0
    assert single_res["measured_areas_count"] == 1
    assert single_res["per_area_utilization_pct"] == {"AREA_A": 80.0}

def test_seating_equity_handles_zero_capacity_safely():
    """Verify areas with zero capacity are safely excluded from division without throwing ZeroDivisionError."""
    metrics = {
        "AREA_A": {"riders": 50, "capacity": 100},  # 50%
        "AREA_B": {"riders": 0, "capacity": 0},     # inactive area
        "AREA_C": {"riders": 50, "capacity": 100},  # 50%
    }
    res = compute_seating_equity(metrics)
    assert res["measured_areas_count"] == 2
    assert "AREA_B" not in res["per_area_utilization_pct"]
    assert res["area_utilization_variance"] == 0.0
    assert res["seating_equity_pct"] == 100.0

def test_seating_equity_zero_demand_with_capacity():
    """Verify area with zero demand and positive capacity pulls down equity (unbalanced load)."""
    metrics = {
        "AREA_A": {"riders": 100, "capacity": 100},  # 1.0 (100%)
        "AREA_B": {"riders": 0, "capacity": 100},    # 0.0 (0%)
    }
    # Mean = 0.50, Variance = (0.5^2 + (-0.5)^2)/2 = 0.25, Std = 0.50, CV = 1.0, Equity = 0.0%
    res = compute_seating_equity(metrics)
    assert res["area_utilization_variance"] == 0.25
    assert res["area_utilization_std"] == 0.50
    assert res["seating_equity_pct"] == 0.0

def test_api_operational_manifest_includes_equity_metrics():
    """Verify that GET /api/workflow/operational-manifest exposes seating equity fields (DATA-003)."""
    res = client.get("/api/workflow/operational-manifest?scenario=REGULAR&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()

    # Field presence and types
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

    # Under REGULAR scenario, optimizer balances fleet closely (~98% equity)
    assert data["seating_equity_pct"] > 90.0

def test_api_manifest_surge_scenario_equity_computation():
    """Verify seating equity recalibrates under surge conditions."""
    res = client.get("/api/workflow/operational-manifest?scenario=MONSOON_RAIN&date=2026-10-15")
    assert res.status_code == 200
    data = res.json()

    assert data["seating_equity_pct"] > 0.0
    assert data["area_utilization_variance"] >= 0.0
