# BUSify: Sprint 3 Formal Audit & Verification Report

**Date of Audit**: 2026-10-12  
**Audit Scope**: Sprint 3 (FastAPI REST Orchestration Layer, Endpoints & Integration Test Suite)  
**Overall Result**: **100% PASSED (11 / 11 API Tests Passing | 21 / 21 Cumulative Tests Passing)**

---

## 1. Executive Summary

Sprint 3 delivered the production-ready REST orchestration layer connecting the data models, LightGBM forecasting, OR-Tools CP-SAT fleet allocation, Capacitated VRP routing, and the transit simulator to web clients. All 8 endpoints are documented with interactive OpenAPI Swagger docs at `/docs` and verified against automated integration test suites.

---

## 2. API Endpoints Verified

| HTTP Method | Route | Description | Response Status | Verification Output |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Root system metadata | `200 OK` | `status: OPERATIONAL` |
| `GET` | `/api/health` | Service health & DB connection | `200 OK` | `status: HEALTHY` |
| `GET` | `/api/stops` | All 47 transit stops & coordinates | `200 OK` | 47 stops returned |
| `GET` | `/api/buses` | Fleet inventory (50 vehicles) | `200 OK` | 50 buses returned |
| `GET` | `/api/forecast` | $p50$ and $p90$ quantile demand | `200 OK` | 5 areas, $p90 \ge p50$ |
| `GET` | `/api/allocation` | OR-Tools CP-SAT fleet distribution | `200 OK` | `OPTIMAL`, $\sum n_a \le 50$ |
| `GET` | `/api/routes` | Capacitated VRP stop sequences | `200 OK` | Turn-by-turn itineraries |
| `GET` | `/api/crowding` | Real-time student crowd badge | `200 OK` | Low/Moderate/Busy/Overcrowded |
| `POST` | `/api/simulate` | Historical backtesting benchmark | `200 OK` | Comparative KPI matrix |
| `GET` | `/api/routes` (Invalid) | 400 error handling on bad zone | `400 Bad Request` | Handled with detail |
| `GET` | `/api/crowding` (Invalid) | 404 error handling on unknown bus | `404 Not Found` | Handled with detail |

---

## 3. Incident, Failure & Improvement Audit

1. **`DEV-LOG-008` (FastAPI TestClient httpx 0.28 Incompatibility):**
   - **Root Cause:** Starlette 0.27 passed deprecated `app` parameter to `httpx.Client`.
   - **Resolution:** Upgraded `starlette>=0.37.0` and `fastapi>=0.110.0` via pip.
2. **`DEV-LOG-009` (Fallback Bin-Packing Overload):**
   - **Root Cause:** In tight combinatorial circumstances, fallback router forced overflow onto least-loaded vehicle (`load = 60 > 55`).
   - **Resolution:** Implemented capacity-capped placement where vehicles only absorb load up to `avail = bus_capacity - bus_loads[b_idx]`, cascading remainder to subsequent vehicles.

---

## 4. Cumulative Regression Audit

The full regression test suite covering Sprint 1, Sprint 2, and Sprint 3 was executed:

```text
backend/app/tests/test_sprint1_data.py::test_student_anonymization_determinism_and_length PASSED
backend/app/tests/test_sprint1_data.py::test_database_stops_count_and_coordinates PASSED
backend/app/tests/test_sprint1_data.py::test_database_fleet_size_and_capacity PASSED
backend/app/tests/test_sprint1_data.py::test_student_registrations_volume_and_integrity PASSED
backend/app/tests/test_sprint1_data.py::test_historical_demand_observations_presence PASSED
backend/app/tests/test_sprint2_algorithms.py::test_demand_forecasting_training_and_quantiles PASSED
backend/app/tests/test_sprint2_algorithms.py::test_area_to_stop_demand_disaggregation PASSED
backend/app/tests/test_sprint2_algorithms.py::test_fleet_allocation_solver_optimality PASSED
backend/app/tests/test_sprint2_algorithms.py::test_capacitated_vehicle_routing_execution PASSED
backend/app/tests/test_sprint2_algorithms.py::test_transit_simulator_backtest PASSED
backend/app/tests/test_sprint3_api.py::test_api_root_endpoint PASSED
backend/app/tests/test_sprint3_api.py::test_api_health_check PASSED
backend/app/tests/test_sprint3_api.py::test_api_get_stops PASSED
backend/app/tests/test_sprint3_api.py::test_api_get_buses PASSED
backend/app/tests/test_sprint3_api.py::test_api_get_forecast PASSED
backend/app/tests/test_sprint3_api.py::test_api_get_allocation PASSED
backend/app/tests/test_sprint3_api.py::test_api_get_routes PASSED
backend/app/tests/test_sprint3_api.py::test_api_get_crowding PASSED
backend/app/tests/test_sprint3_api.py::test_api_simulate PASSED
backend/app/tests/test_sprint3_api.py::test_api_error_handling_invalid_area PASSED
backend/app/tests/test_sprint3_api.py::test_api_error_handling_nonexistent_bus PASSED

======================= 21 passed in 7.04s (100% PASS RATE) =======================
```

---

## 5. Milestone Sign-Off

* **Sprint 3 (FastAPI REST Orchestration Layer):** **APPROVED & SEALED**
