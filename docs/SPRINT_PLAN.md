# BUSify: Sprint Execution Framework & Audit Protocol

This document establishes the structured sprint roadmap for BUSify. Each sprint represents a self-contained, verifiable milestone. At the conclusion of each sprint, the build undergoes a rigorous automated test audit, failure analysis check, and documentation sign-off before proceeding.

---

## Sprint Roadmap Overview

```text
┌────────────────────────────────────────────────────────┐
│ Sprint 1: Core Foundation & Data Pipeline              │  --> Audit & Verification
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Sprint 2: Algorithmic Engines (Forecast, Alloc, VRP)   │  --> Audit & Verification
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Sprint 3: FastAPI Orchestration Layer & Endpoints      │  --> Audit & Verification
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Sprint 4: Frontend Scaffold & Core UI Component System │  --> Audit & Verification
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Sprint 5: Dual Dashboards (Office & Student) + Maps    │  --> Audit & Verification
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Sprint 6: End-to-End System Integration & Final Polish │  --> Final Audit Sign-Off
└────────────────────────────────────────────────────────┘
```

---

## Sprint Definitions & Deliverables

### Sprint 1: Core Foundation & Data Pipeline
- **Deliverables:**
  - Python runtime & dependency environment.
  - Relational database schema (`stops`, `buses`, `registrations`, `calendar`, `demand_obs`, `plans`).
  - Privacy-preserving student ID hashing module (SHA-256).
  - Realistic multi-zone synthetic college transit network generator (Karur/Kongu region: 47 stops, 50 buses, 2,200 registrations, 105 calendar days, 3,055 demand observations).
- **Audit Requirement:**
  - Database schema integrity check.
  - Anonymization irreversibility and determinism test.
  - Zero-missing-data verification on generated dataset.

---

### Sprint 2: Algorithmic Engines (Forecasting, Allocation, Routing & Simulation)
- **Deliverables:**
  - Demand Forecasting Engine: LightGBM quantile regression ($p50, p90$) with baseline benchmarking.
  - Disaggregation Engine: Area-to-stop proportional student distribution.
  - Fleet Allocation Engine: OR-Tools CP-SAT Integer Linear Program with schedule stability penalty $\mu$.
  - Routing Engine: Dual-mode Distance Matrix Service (OSRM + Haversine fallback) and Capacitated VRP solver with split-pickup preprocessing.
  - Simulation Engine: Historical backtester benchmarking status quo vs. dynamic dispatch.
- **Audit Requirement:**
  - LightGBM WAPE improvement assertion ($> 20\%$ gain over historical weekday baseline).
  - CP-SAT mathematical optimality & fleet constraint checks ($\sum n_a \le 50$, $s_a \ge 0$).
  - CVRP zero-capacity-violation assertion and backward arrival scheduling accuracy.
  - Simulation reproducibility test.

---

### Sprint 3: FastAPI Orchestration Layer & API Test Suite
- **Deliverables:**
  - REST API Routers: `/api/stops`, `/api/buses`, `/api/forecast`, `/api/allocation`, `/api/routes`, `/api/crowding`, `/api/simulate`, `/api/health`.
  - Pydantic v2 schemas for all requests and responses.
  - CORS middleware and global exception handlers.
  - Automated API test suite (`pytest` + `TestClient`).
- **Audit Requirement:**
  - HTTP status 200 on all valid endpoints.
  - Schema validation test for edge-case query parameters.
  - Endpoint latency audit (< 500ms for cached inferences).

---

### Sprint 4: Frontend Scaffolding & Core Component Design System
- **Deliverables:**
  - Vite + React application setup with Tailwind CSS.
  - Design tokens, typography (Inter / Outfit), glassmorphic styling, and dark/light contrast.
  - Reusable component library: `Navbar`, `MetricCard`, `StatusBadge`, `ChartContainer`.
  - API client service layer (`src/services/api.js`).
- **Audit Requirement:**
  - Vite build verification (`npm run build`).
  - Linting and layout responsiveness checks across mobile and desktop viewports.

---

### Sprint 5: Dual Dashboards (Transport Office & Student Portal) + Interactive Maps
- **Deliverables:**
  - **Transport Office Dashboard (`views/OfficeDashboard.jsx`):**
    - Fleet KPI metrics (standing student reduction, seat utilization %, active buses).
    - Leaflet Map displaying stops, routes, depots, and crowd heat indicators.
    - Recharts comparisons (Status Quo vs. Optimized Fleet, p50/p90 demand curves).
    - One-click historical simulation runner with live benchmark results.
  - **Student View (`views/StudentView.jsx`):**
    - Stop selector, bus assignment, departure time, and crowd congestion badge (Low/Moderate/Busy).
- **Audit Requirement:**
  - End-to-end data flow from backend to visual components.
  - Leaflet map rendering with valid markers and polylines.
  - Cross-view role switching test.

---

### Sprint 6: End-to-End System Integration & Final Delivery
- **Deliverables:**
  - Full-stack live execution test.
  - Final documentation update in `docs/` and root `CHANGELOG.md`.
  - Complete project audit summary report.
- **Audit Requirement:**
  - Zero critical errors across terminal, backend, and browser consoles.
  - Final audit sign-off artifact.
