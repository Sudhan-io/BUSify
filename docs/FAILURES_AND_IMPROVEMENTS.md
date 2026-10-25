# BUSify: Development Failures, Root Cause Analyses & Improvements Log

This log actively tracks issues, bugs, solver failures, performance bottlenecks, and design edge cases encountered during the development of BUSify, along with root causes, architectural pivots, and applied improvements.

---

## Log Schema

Every entry adheres to the following structure:
* **Log ID**: `DEV-LOG-###`
* **Date / Timestamp**: When the issue was identified and resolved
* **Component / Phase**: Module involved (e.g., `Data Pipeline`, `Forecasting`, `Allocation IP`, `Routing CVRP`, `API`, `Frontend`)
* **Symptom / Failure Description**: What went wrong or what anomaly occurred
* **Root Cause Analysis (RCA)**: Why the problem happened
* **Resolution & Applied Improvement**: What fix or architectural change was made
* **Verification & Prevention**: How the solution was validated to prevent recurrence

---

## Historical & Architectural Pivot Logs

### [DEV-LOG-001] | Sparse Stop-Level Ridership vs. Area Aggregation
* **Date**: 2026-10-12
* **Component**: Demand Forecasting Engine (`core/forecasting`)
* **Symptom / Potential Failure**: High variance and near-zero count sparsity when attempting to train ML regression models directly on individual stops (e.g., individual bus stops with 0-4 students per day).
* **Root Cause Analysis**: At individual stop granularity, attendance fluctuations and random student absence create zero-inflated, noisy distributions where tree-based models fail to generalize.
* **Resolution & Applied Improvement**: 
  - Aggregated demand forecasting to the **Area/Zone level** (40–300 students per area).
  - Implemented an analytical **Area-to-Stop Disaggregator** that splits area forecast down to stops proportionally based on baseline student registration weights.
* **Verification**: Greatly reduces forecast variance and allows LightGBM quantile regression ($p50, p90$) to learn robust macro-calendar patterns (weekdays, exams, weather).

---

### [DEV-LOG-002] | Fleet Allocation Volatility & Daily Schedule Churn
* **Date**: 2026-10-12
* **Component**: Fleet Allocation (`core/allocation`)
* **Symptom / Potential Failure**: Unconstrained Integer Programming optimizes purely for capacity fit, which causes radical day-to-day shifts in bus assignments (e.g., Area A having 5 buses on Monday and 14 on Tuesday), confusing drivers and students.
* **Root Cause Analysis**: The objective function lacked a regularization term penalizing deviations from the operational baseline schedule ($n_{\text{current}, a}$).
* **Resolution & Applied Improvement**: 
  - Added a churn penalty parameter $\mu \sum d_a$ to the CP-SAT objective:
    $$\min \sum s_a + \lambda \sum e_a + \mu \sum |n_a - n_{\text{current}, a}|$$
  - Calibrated $\mu$ to ensure the optimizer only reallocates buses when demand spikes strictly warrant it, preserving day-to-day route stability.
* **Verification**: Formulated in OR-Tools unit tests with controlled synthetic scenarios to confirm schedule dampening behavior.

---

### [DEV-LOG-003] | External OSRM Network Fragility in Local Development
* **Date**: 2026-10-12
* **Component**: Routing Engine (`core/routing/matrix_service`)
* **Symptom / Potential Failure**: Complete breakdown of the vehicle routing pipeline if the public OSRM server is rate-limited, offline, or if local Docker OSRM is not yet booted.
* **Root Cause Analysis**: Hard dependency on external network HTTP routing services introduces a single point of failure during offline development and continuous integration testing.
* **Resolution & Applied Improvement**: 
  - Built a resilient **Dual-Mode Matrix Service**:
    1. Tries local/configured OSRM instance.
    2. Gracefully falls back to a calibrated Haversine distance calculator multiplied by an empirical road-curvature factor (1.32x) and average urban bus velocity curve.
  - Implemented an in-memory & file-based matrix cache (`.matrix_cache/`) keyed by stop coordinate hashes.
* **Verification**: Routing tests run completely offline and deterministically without network calls.

---

## Active Development Incident Log

*(New entries are appended below as coding progresses through each phase)*

| Log ID | Date | Component | Issue Summary | Status |
| :--- | :--- | :--- | :--- | :--- |
| `DEV-LOG-001` | 2026-10-12 | Forecasting | Data sparsity at stop level addressed via area aggregation | **Resolved** |
| `DEV-LOG-002` | 2026-10-12 | Allocation | Operational churn dampened with penalty term $\mu$ | **Resolved** |
| `DEV-LOG-003` | 2026-10-12 | Routing | OSRM offline fragility solved via Haversine fallback & caching | **Resolved** |
| `DEV-LOG-004` | 2026-10-12 | Config & Setup | ModuleNotFoundError: No module named 'pydantic_settings' | **Resolved** |
| `DEV-LOG-005` | 2026-10-12 | Routing CVRP | Infeasible CVRP solution when single-stop demand exceeds vehicle capacity (55) | **Resolved** |

---

### [DEV-LOG-004] | Missing `pydantic_settings` Package in Pydantic V2
* **Date**: 2026-10-12
* **Component**: Configuration & Setup (`backend/app/config.py`)
* **Symptom / Failure Description**: When running `python -m backend.app.core.data.synthetic_generator`, Python raised `ModuleNotFoundError: No module named 'pydantic_settings'`.
* **Root Cause Analysis**: In Pydantic v2, `BaseSettings` was factored out of the core `pydantic` package into a standalone package `pydantic-settings`.
* **Resolution & Applied Improvement**:
  - Installed `pydantic-settings>=2.0.0` via pip.
  - Updated `backend/requirements.txt` to explicitly include `pydantic-settings>=2.0.0`.
  - Added fallback exception handling in `config.py` to support standard `pydantic.BaseModel` if `pydantic_settings` is absent.
* **Verification & Prevention**: Verified import in Python and re-ran data generation pipeline.

---

| `DEV-LOG-005` | 2026-10-12 | Routing CVRP | Infeasible CVRP solution when single-stop demand exceeds vehicle capacity (55) | **Resolved** |
| `DEV-LOG-006` | 2026-10-12 | Routing CVRP | SyntaxError: leading zeros in decimal integer literals in Python 3.12 | **Resolved** |
| `DEV-LOG-007` | 2026-10-12 | Routing CVRP | Bin-Packing combinatorial infeasibility in Area C route packing | **Resolved** |
| `DEV-LOG-008` | 2026-10-12 | API Testing | TestClient TypeError with httpx 0.28 due to Starlette version lag | **Resolved** |
| `DEV-LOG-009` | 2026-10-12 | Routing CVRP | Overflow load (60 > 55) in fallback bin-packing placement | **Resolved** |
| `DEV-LOG-010` | 2026-10-12 | Frontend | Tailwind CSS v4 PostCSS plugin relocation error during Vite build | **Resolved** |


---

### [DEV-LOG-005] | CVRP Infeasibility on High-Density Stop Demand (> 55 Students)
* **Date**: 2026-10-12
* **Component**: Capacitated Routing (`backend/app/core/routing/vrp_solver.py`)
* **Symptom / Failure Description**: When testing `CapacitatedVRPSolver` on Area A, the solver returned `status: INFEASIBLE` and raised a `KeyError`.
* **Root Cause Analysis**: High-traffic hub stops (such as Central Bus Stand with 56 students and Vengamedu Junction with 57 students) had demands strictly exceeding the individual vehicle seating capacity ($C_{\text{bus}} = 55$). In classical Capacitated Vehicle Routing, no single vehicle can fulfill a node whose demand exceeds its capacity without split pickups.
* **Resolution & Applied Improvement**:
  - Implemented an automated **Split-Pickup Virtual Node Preprocessor** in `vrp_solver.py`.
  - Any stop having demand $q_i > C_{\text{bus}}$ is partitioned into multiple virtual pickup visits (e.g. Stop Part 1 with 50 students, Stop Part 2 with 7 students) sharing identical coordinates.
  - Re-mapped solution itineraries back to clean human-readable stop names indicating multi-bus service at high-capacity junctions.
* **Verification & Prevention**: Tested on Area A and Area B; solver consistently returned feasible optimal multi-bus routes.

---

### [DEV-LOG-006] | Python 3.12 SyntaxError on Leading Zeros in F-String Literals
* **Date**: 2026-10-12
* **Component**: Capacitated Routing (`backend/app/core/routing/vrp_solver.py`)
* **Symptom / Failure Description**: `SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers` triggered on f-string literal `f"08:{05 + i * 5:02d}"`.
* **Root Cause Analysis**: In Python 3.12, decimal integer literals inside f-string expressions cannot have leading zeros unless octal prefix `0o` is used.
* **Resolution & Applied Improvement**: Replaced `05` with `5` in the arithmetic expression.
* **Verification & Prevention**: Verified with Python 3.12 syntax check and execution test.

---

### [DEV-LOG-007] | Bin-Packing Combinatorial Infeasibility in Area C Route Assignment
* **Date**: 2026-10-12
* **Component**: Capacitated Routing (`backend/app/core/routing/vrp_solver.py`)
* **Symptom / Failure Description**: In `test_capacitated_vehicle_routing_execution`, route load was computed as 75 passengers, violating the 55-seat vehicle capacity assertion (`assert 75 <= 55`).
* **Root Cause Analysis**: Stop demands in Area C were partitioned into large chunks [50, 47, 46, 39, 33, 25, 24, 23, 3]. Although total passenger count (290) was mathematically less than total fleet capacity (6 × 55 = 330), the 1D Bin-Packing Problem could not pack these large chunks into 6 bins without exceeding 55. The OR-Tools solver timed out (`Status: 3 - ROUTING_FAIL_TIMEOUT`), and the previous fallback heuristic used simple modulo clustering which exceeded 55.
* **Resolution & Applied Improvement**:
  - Reduced the target virtual stop pickup chunk size to $\le 30$ passengers (`min(30, int(bus_capacity * 0.60))`), allowing items to be seamlessly packed into 6 bins of size 55.
  - Switched the routing search initial strategy to `PARALLEL_CHEAPEST_INSERTION`.
  - Upgraded the fallback heuristic to a capacity-constrained **First-Fit-Decreasing (FFD) Bin Packer** ensuring no vehicle can ever be assigned $> 55$ passengers under any circumstance.
* **Verification & Prevention**: Re-ran the automated test suite; all 10 unit tests passed with 100% success rate (`10 passed in 4.80s`).

---

### [DEV-LOG-008] | FastAPI TestClient Incompatibility with httpx 0.28
* **Date**: 2026-10-12
* **Component**: API Integration Testing (`backend/app/tests/test_sprint3_api.py`)
* **Symptom / Failure Description**: `TypeError: Client.__init__() got an unexpected keyword argument 'app'` when running pytest on `TestClient(app)`.
* **Root Cause Analysis**: `httpx 0.28.1` removed the deprecated `app` keyword argument in `Client.__init__()`. The older `starlette 0.27.0` still passed `app=...` directly to `httpx.Client`.
* **Resolution & Applied Improvement**: Upgraded `starlette>=0.37.0` and `fastapi>=0.110.0` via pip, ensuring modern compatibility with `httpx >= 0.28`.
* **Verification & Prevention**: TestClient instantiates cleanly and executes HTTP requests against ASGI endpoints without error.

---

### [DEV-LOG-009] | Overflow Load (60 > 55) in Fallback Bin-Packing Placement
* **Date**: 2026-10-12
* **Component**: Capacitated Routing (`backend/app/core/routing/vrp_solver.py`)
* **Symptom / Failure Description**: In `test_api_get_routes`, route load was returned as 60 passengers, failing the assertion `assert 60 <= 55`.
* **Root Cause Analysis**: In `_heuristic_fallback_routes`, if a stop could not be placed in any vehicle without exceeding capacity, it was forcibly placed into the least-loaded vehicle (`min_idx`), pushing that vehicle's load over 55.
* **Resolution & Applied Improvement**: Replaced the placement loop with a capacity-capped allocation: vehicles only absorb passengers up to their remaining capacity `avail = bus_capacity - bus_loads[b_idx]`, and any remaining demand cascades into subsequent available vehicles.
* **Verification & Prevention**: Tested across all 5 areas; maximum route load is mathematically capped at exactly $\le 55$ passengers.

---

### [DEV-LOG-010] | Tailwind CSS v4 PostCSS Plugin Relocation Error
* **Date**: 2026-10-12
* **Component**: Frontend Build (`frontend/src/index.css` & `postcss.config.js`)
* **Symptom / Failure Description**: When running `npm run build`, Vite bundler threw: `Error: [postcss] It looks like you're trying to use 'tailwindcss' directly as a PostCSS plugin. The PostCSS plugin has moved to a separate package, so to continue using Tailwind CSS with PostCSS you'll need to install '@tailwindcss/postcss'`.
* **Root Cause Analysis**: Tailwind CSS v4 separated its PostCSS plugin into `@tailwindcss/postcss` and deprecated `@tailwind base/components/utilities` directives in favor of `@import "tailwindcss"`.
* **Resolution & Applied Improvement**:
  - Installed `@tailwindcss/postcss` via npm.
  - Updated `postcss.config.js` to register `'@tailwindcss/postcss': {}`.
  - Updated `src/index.css` to use `@import "tailwindcss"`.
* **Verification & Prevention**: Verified production build using `npm run build`; compiled `dist/` bundle in 5.5s with zero errors.

---

### [DEV-LOG-011] | Operational Workflow Model Attribute & Solver Keyword Misalignment
* **Date**: 2026-10-12
* **Component**: Workflow Router (`backend/app/api/routes_workflow.py`)
* **Symptom / Failure Description**: When querying `GET /api/workflow/operational-manifest`, the server raised `AttributeError: type object 'Stop' has no attribute 'campus_distance_km'` followed by `TypeError: CapacitatedVRPSolver.solve() got an unexpected keyword argument 'bus_capacity'`.
* **Root Cause Analysis**:
  1. The `Stop` SQLAlchemy model does not store a physical database column `campus_distance_km` (distance to campus is calculated based on `sequence_order` or geographic coordinates).
  2. The `vrp_solver.solve()` method expects positional/keyword arguments `(area_id, stops, num_buses)` where `stops` are pre-disaggregated dictionaries with `p90_riders`, rather than raw `bus_capacity=55` and `max_buses=...`.
* **Resolution & Applied Improvement**:
  - Updated the query in `routes_workflow.py` to order stops by `sequence_order`.
  - Replaced ad-hoc stop dictionaries with `disaggregate_area_demand(area_id, area_p50, area_p90)` to produce fully compliant stop representations.
  - Aligned solver invocation to `vrp_solver.solve(area_id=area_id, stops=stops_payload, num_buses=bus_count)`.
  - Re-instantiated uvicorn with `--reload` to immediately pick up newly registered routers.
* **Verification & Prevention**: Wrote automated integration tests in `tests/test_sprint7_workflow.py`; all 31 tests passed cleanly with 100% pass rate.

---

### [DEV-LOG-012] | Leaflet Stacking Context Overlap & CartoDB Watermark
* **Date**: 2026-10-12
* **Component**: UI Layer (`OfficeDashboard.jsx`, `LeafletMap.jsx`, `index.css`)
* **Symptom / Failure Description**: When opening the Official Driver Trip Sheet modal from the Vehicle Dispatch Roster, the Leaflet map and its zoom controls (`+`/`−`) punched through and overlapped the modal dialog. In addition, CartoDB raster tiles displayed an `"API KEY REQUIRED"` watermark overlay.
* **Root Cause Analysis**:
  1. Leaflet uses internal z-indices up to `1000` for controls and pane layers, which exceeded the modal's Tailwind `z-50` (`z-index: 50`). Without a CSS stacking boundary, Leaflet controls escaped into the root viewport stack.
  2. CartoDB's public raster endpoints transitioned to requiring explicit API keys, resulting in watermarked tile assets.
* **Resolution & Applied Improvement**:
  - Elevated the modal backdrop to `fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm` with modal container `relative z-10`.
  - Added `isolate z-0` to the `LeafletMap` wrapper element to enforce an independent CSS stacking context.
  - Capped Leaflet control layers in `index.css` via `.leaflet-top, .leaflet-bottom { z-index: 20 !important; }`.
  - Replaced the tile layer provider with official, clean, watermark-free OpenStreetMap tiles (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`).
* **Verification & Prevention**: Verified with browser agent and screenshot inspection; the modal renders cleanly above all elements with zero bleed-through, and map tiles load watermark-free.






