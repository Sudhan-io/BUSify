import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.forecasting.disaggregator import (
    disaggregate_area_demand,
    get_stop_weights_for_area,
)
from backend.app.core.data.synthetic_generator import AREAS_CONFIG

client = TestClient(app)

def test_disaggregator_normal_area_with_demand():
    """Verify normal area with multiple stops disaggregates demand proportionally and conserves totals."""
    area_p50 = 350
    area_p90 = 400
    stops = disaggregate_area_demand("AREA_A", area_p50, area_p90)
    assert len(stops) == 10

    total_p50 = sum(s["p50_riders"] for s in stops)
    total_p90 = sum(s["p90_riders"] for s in stops)

    # Demand totals must be conserved within rounding boundaries
    assert abs(total_p50 - area_p50) <= 2
    assert abs(total_p90 - area_p90) <= 2

    # Every stop must have required routing keys
    for s in stops:
        assert s["area_id"] == "AREA_A"
        assert "stop_id" in s
        assert "name" in s
        assert "lat" in s
        assert "lon" in s
        assert "p50_riders" in s
        assert "p90_riders" in s
        assert s["p90_riders"] >= s["p50_riders"]

def test_disaggregator_empty_area_raises_422():
    """Verify that an area with zero associated stops raises HTTPException(422) with a clear message."""
    empty_area_id = "AREA_NONEXISTENT_99"
    with pytest.raises(HTTPException) as exc_info:
        disaggregate_area_demand(empty_area_id, 100, 120)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == f"Area {empty_area_id} has no stops. Cannot disaggregate demand."

def test_disaggregator_zero_demand_handling():
    """Verify that an area with zero demand returns all stops with 0 riders without division errors."""
    stops = disaggregate_area_demand("AREA_A", 0, 0)
    assert len(stops) == 10
    assert sum(s["p50_riders"] for s in stops) == 0
    assert sum(s["p90_riders"] for s in stops) == 0
    for s in stops:
        assert s["p50_riders"] == 0
        assert s["p90_riders"] == 0

def test_disaggregator_zero_registrations_with_positive_demand_raises_422(monkeypatch):
    """Verify that when an area has stops but zero registrations, positive demand cannot be fabricated and raises 422."""
    import pandas as pd
    import backend.app.core.forecasting.disaggregator as disagg_mod

    mock_df = pd.DataFrame([
        {"stop_id": "ST_01", "name": "Stop 1", "lat": 10.9, "lon": 77.9, "sequence_order": 1, "registered_count": 0},
        {"stop_id": "ST_02", "name": "Stop 2", "lat": 10.91, "lon": 77.91, "sequence_order": 2, "registered_count": 0},
    ])

    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: mock_df)

    with pytest.raises(HTTPException) as exc_info:
        disagg_mod.disaggregate_area_demand("AREA_ZERO_REGS", 100, 120)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Area AREA_ZERO_REGS has zero student registrations. Cannot disaggregate positive demand."

def test_disaggregator_zero_registrations_with_zero_demand_conserves_zeros(monkeypatch):
    """Verify that zero registrations with zero demand assigns 0.0 weights and conserves zeros without fabrication."""
    import pandas as pd
    import backend.app.core.forecasting.disaggregator as disagg_mod

    mock_df = pd.DataFrame([
        {"stop_id": "ST_01", "name": "Stop 1", "lat": 10.9, "lon": 77.9, "sequence_order": 1, "registered_count": 0},
        {"stop_id": "ST_02", "name": "Stop 2", "lat": 10.91, "lon": 77.91, "sequence_order": 2, "registered_count": 0},
    ])

    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: mock_df)

    weights = disagg_mod.get_stop_weights_for_area("AREA_ZERO_REGS")
    assert len(weights) == 2
    assert weights[0]["weight"] == 0.0
    assert weights[1]["weight"] == 0.0

    # Run zero-demand disaggregation through mocked zero registrations
    results = disagg_mod.disaggregate_area_demand("AREA_ZERO_REGS", 0, 0)
    assert len(results) == 2
    assert results[0]["p50_riders"] == 0
    assert results[0]["p90_riders"] == 0
    assert results[1]["p50_riders"] == 0
    assert results[1]["p90_riders"] == 0


def test_disaggregator_multiple_areas_isolation():
    """Verify multiple areas disaggregate independently with no cross-area demand contamination."""
    stops_a = disaggregate_area_demand("AREA_A", 200, 250)
    stops_b = disaggregate_area_demand("AREA_B", 0, 0)

    assert len(stops_a) == 10
    assert sum(s["p50_riders"] for s in stops_a) == 200
    assert all(s["area_id"] == "AREA_A" for s in stops_a)

    assert len(stops_b) == 11
    assert sum(s["p50_riders"] for s in stops_b) == 0
    assert all(s["area_id"] == "AREA_B" for s in stops_b)

    # Empty area alongside valid ones raises 422 cleanly
    with pytest.raises(HTTPException) as exc_info:
        disaggregate_area_demand("AREA_GHOST", 100, 150)
    assert exc_info.value.status_code == 422

def test_disaggregator_negative_demand_raises_422():
    """Verify that negative demand inputs raise HTTPException(422) as unprocessable entities."""
    with pytest.raises(HTTPException) as exc_info:
        disaggregate_area_demand("AREA_A", -10, 50)
    assert exc_info.value.status_code == 422
    assert "Area demand cannot be negative" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        disaggregate_area_demand("AREA_A", 50, -20)
    assert exc_info.value.status_code == 422
    assert "Area demand cannot be negative" in exc_info.value.detail

def test_disaggregator_deterministic_execution():
    """Verify repeated execution produces identical deterministic stop outputs."""
    run_1 = disaggregate_area_demand("AREA_C", 180, 220)
    run_2 = disaggregate_area_demand("AREA_C", 180, 220)

    assert len(run_1) == len(run_2)
    for s1, s2 in zip(run_1, run_2):
        assert s1["stop_id"] == s2["stop_id"]
        assert s1["p50_riders"] == s2["p50_riders"]
        assert s1["p90_riders"] == s2["p90_riders"]

def test_api_routes_area_with_no_stops_returns_422(monkeypatch):
    """Verify GET /api/routes returns 422 when an area has no stops in DB."""
    import backend.app.core.forecasting.disaggregator as disagg_mod
    monkeypatch.setattr(disagg_mod, "get_stop_weights_for_area", lambda area_id: [])

    res = client.get("/api/routes?area_id=AREA_A")
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert "Area AREA_A has no stops. Cannot disaggregate demand." in data["detail"]
