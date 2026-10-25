# BUSify: Module Specifications

This document outlines the responsibilities, input/output contracts, internal algorithms, and edge-case handling for each module in the BUSify platform.

---

## 1. Data Ingestion & Synthesis Engine (`core/data`)
* **Purpose**: Ingest real or synthetic transit records, clean student registrations, anonymize PII, and generate training datasets.
* **Key Components**:
  - `anonymizer.py`: Computes salted SHA-256 hashes of student identifiers (`student_hash = SHA256(student_id + salt)`).
  - `synthetic_generator.py`: Generates realistic multi-zone transit networks (5 geographic zones, 45+ stops, 50 buses, 2,200 registrations, 90 days of historical demand observations with exam and weather spikes).
* **Inputs**: Raw CSV/Excel or programmatic parameters.
* **Outputs**: Relational database records (`stops`, `buses`, `registrations`, `demand_obs`, `calendar`).

---

## 2. Demand Forecasting Engine (`core/forecasting`)
* **Purpose**: Quantile forecasting of ridership at the Area $\times$ Slot level.
* **Key Components**:
  - `baseline.py`: Computes 4-week historical same-weekday rolling averages as benchmark.
  - `feature_pipeline.py`: Extracts cyclical day-of-week, week-of-semester, exam flags, holiday indicators, 7-day/14-day rolling demand averages, and lag features.
  - `lightgbm_model.py`: Trains LightGBM regressors with `objective='quantile'` for $\alpha = 0.50$ (p50) and $\alpha = 0.90$ (p90).
  - `disaggregator.py`: Proportionally divides area-level predicted ridership down to individual stops using historical registration distributions.
* **Evaluation Criteria**: LightGBM WAPE must be strictly lower than baseline WAPE.

---

## 3. Fleet Allocation Engine (`core/allocation`)
* **Purpose**: Solves macro bus fleet assignment across zones given predicted peak demand $D_a^{p90}$.
* **Key Components**:
  - `optimizer.py`: Wraps Google OR-Tools CP-SAT solver. Formulates decision variables ($n_a, s_a, e_a, d_a$) subject to fleet budget and coverage bounds.
* **Inputs**:
  - Target date and slot.
  - Area demand predictions ($p90$).
  - Current baseline allocation vector ($n_{\text{current}}$).
* **Outputs**:
  - Optimized bus allocation dictionary: `{ "Area A": 8, "Area B": 12, ... }`.
  - Slack metrics (estimated standing students, unused capacity, reallocations made).

---

## 4. Capacitated Routing Engine (`core/routing`)
* **Purpose**: Determines the optimal stop sequence and pickup schedules for buses within an area.
* **Key Components**:
  - `matrix_service.py`: Computes $N \times N$ distance and travel time matrices with automatic fallback between live OSRM instances and offline Haversine geodesic calculations.
  - `vrp_solver.py`: Uses OR-Tools `RoutingModel` with a `Dimension` for vehicle seat capacity ($C_{\text{bus}} = 55$). Enforces that total onboard passengers at any point along a route does not exceed capacity.
* **Outputs**:
  - Turn-by-turn route objects containing ordered stop IDs, pickup arrival timestamps, and total route kilometers.

---

## 5. Simulation & Backtesting Engine (`core/simulation`)
* **Purpose**: Compares the status-quo fixed allocation against the proposed dynamic allocation on historical or counterfactual test days.
* **Key Components**:
  - `simulator.py`: Replays ridership observations and calculates:
    1. **Overcrowding Rate**: Trips where passenger count $> C_{\text{bus}}$.
    2. **Average Standing Students**: Sum of unseated passengers divided by total trips.
    3. **Total Fleet Kilometers**: Distance traveled across all active routes.
    4. **Fleet Efficiency**: Ratio of passenger-km to seat-km.
* **Outputs**: Comparative JSON payload consumed by the Transport Office dashboard.

---

## 6. FastAPI REST Layer (`app/api`)
* **Purpose**: Exposes clean, validated REST endpoints for web clients.
* **Endpoints**:
  - `GET /api/health`: System health and status.
  - `GET /api/stops`: List of all stops with lat/long and zone.
  - `GET /api/buses`: Fleet inventory and capacities.
  - `GET /api/forecast?date=YYYY-MM-DD`: $p50$ and $p90$ demand by area.
  - `GET /api/allocation?date=YYYY-MM-DD`: Current vs. optimized bus counts.
  - `GET /api/routes?date=YYYY-MM-DD&area_id=X`: Route itineraries for Area X.
  - `GET /api/crowding?bus_id=Y&date=YYYY-MM-DD`: Real-time crowding indicator (Low, Moderate, Busy).
  - `POST /api/simulate`: Historical comparison over a specified date range.

---

## 7. Frontend User Interfaces (`frontend/src`)
* **Transport Office Dashboard (`views/OfficeDashboard.jsx`)**:
  - KPI metric cards (Standing passenger reduction %, Fleet utilization, Active buses).
  - Leaflet Map: Displays stops with crowding heatmap indicators, route lines, and vehicle depots.
  - Recharts: Visualizes status quo vs. optimized fleet distribution and demand forecasts.
  - Backtesting Simulation Panel: Interactive date-range benchmark trigger.
* **Student View (`views/StudentView.jsx`)**:
  - Quick stop finder and route lookup.
  - Assigned bus card with scheduled departure, pickup time, and crowd level badge.
