import pytest
from backend.app.core.forecasting.lightgbm_model import forecaster
from backend.app.core.forecasting.disaggregator import disaggregate_area_demand
from backend.app.core.allocation.optimizer import fleet_allocator
from backend.app.core.routing.matrix_service import matrix_service
from backend.app.core.routing.vrp_solver import vrp_solver
from backend.app.core.simulation.simulator import simulator, BASELINE_ALLOCATION

def test_demand_forecasting_training_and_quantiles():
    """Validates LightGBM quantile forecasting model training and predictions."""
    metrics = forecaster.train_and_evaluate()
    assert metrics["lightgbm_p50_wape"] < metrics["baseline_wape"], "LightGBM must beat baseline WAPE"
    assert metrics["wape_improvement_pct"] > 0, "WAPE improvement must be positive"

    pred = forecaster.predict_for_date("2026-10-20", "AREA_A", exam_flag=False)
    assert "p50_demand" in pred
    assert "p90_demand" in pred
    assert pred["p90_demand"] >= pred["p50_demand"], "p90 demand must be >= p50 demand"

def test_area_to_stop_demand_disaggregation():
    """Validates that disaggregated stop ridership closely sums to the area forecast."""
    area_p50 = 350
    area_p90 = 400
    stops = disaggregate_area_demand("AREA_A", area_p50, area_p90)
    assert len(stops) == 10, f"Expected 10 stops for AREA_A, got {len(stops)}"
    
    total_stop_p50 = sum(s["p50_riders"] for s in stops)
    total_stop_p90 = sum(s["p90_riders"] for s in stops)
    
    # Check conservation of demand within small rounding tolerance
    assert abs(total_stop_p50 - area_p50) <= 2
    assert abs(total_stop_p90 - area_p90) <= 2

def test_fleet_allocation_solver_optimality():
    """Validates OR-Tools CP-SAT fleet allocation against constraints."""
    test_demands = {
        "AREA_A": 450,
        "AREA_B": 750,  # High surge
        "AREA_C": 350,
        "AREA_D": 600,
        "AREA_E": 350,
    }
    result = fleet_allocator.solve(test_demands, BASELINE_ALLOCATION)
    assert result["status"] in ["OPTIMAL", "FEASIBLE"]
    assert sum(result["allocation"].values()) <= 50, "Total allocated buses must not exceed 50"
    for a, buses in result["allocation"].items():
        assert buses >= 2, f"Area {a} violates minimum coverage constraint"

def test_capacitated_vehicle_routing_execution():
    """Validates that CVRP generates valid routes without exceeding bus capacity."""
    stops = disaggregate_area_demand("AREA_C", 250, 290)
    routing_res = vrp_solver.solve("AREA_C", stops, num_buses=6)
    assert routing_res["status"] == "SUCCESS"
    assert routing_res["buses_utilized"] > 0
    assert len(routing_res["routes"]) > 0

    for r in routing_res["routes"]:
        assert r["total_riders"] <= 55, f"Bus route exceeded capacity: {r['total_riders']} > 55"
        assert len(r["itinerary"]) >= 3, "Route must contain at least departure, 1 stop, and arrival"

def test_transit_simulator_backtest():
    """Validates that historical backtesting simulation produces sound comparative KPIs."""
    sim_res = simulator.simulate_date_range(sample_days=5)
    assert sim_res["status"] == "SUCCESS"
    kpis = sim_res["summary_kpis"]
    assert "standing_students_reduction_pct" in kpis
    assert "total_students_transported" in kpis
    assert kpis["total_students_transported"] > 0
