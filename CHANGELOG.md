# Changelog & Development Record

All notable changes, file additions, refactorings, and optimizations to **BUSify** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] - 2026-10-12

### Added
- Created comprehensive master implementation plan artifact: `project_master_plan.md`.
- Established documentation directory structure under `docs/`:
  - [README.md](file:///d:/PROJECTS/BUSify/docs/README.md): Master documentation hub and index.
  - [SPRINT_PLAN.md](file:///d:/PROJECTS/BUSify/docs/SPRINT_PLAN.md): Structured 6-sprint execution roadmap, milestone deliverables, and testing audit protocols.
  - [ARCHITECTURE.md](file:///d:/PROJECTS/BUSify/docs/ARCHITECTURE.md): System architecture, mathematical models (Pinball Loss, Allocation IP, CVRP), and tech stack decisions.
  - [MODULES.md](file:///d:/PROJECTS/BUSify/docs/MODULES.md): Detailed functional specifications for Forecasting, Allocation, Routing, Simulator, API, and UI.
  - [DATA_DICTIONARY.md](file:///d:/PROJECTS/BUSify/docs/DATA_DICTIONARY.md): Entity relationship schemas, field specifications, indices, and anonymization constraints.
  - [FAILURES_AND_IMPROVEMENTS.md](file:///d:/PROJECTS/BUSify/docs/FAILURES_AND_IMPROVEMENTS.md): Live log tracking bugs, solver failures, root causes, and improvements (`DEV-LOG-001` through `DEV-LOG-007`).
- **Sprint 1 (Core Foundation & Data Pipeline)**:
  - Database schema models (`Stop`, `Bus`, `Registration`, `Calendar`, `DemandObservation`, `Plan`) in [models/](file:///d:/PROJECTS/BUSify/backend/app/models).
  - SHA-256 salted student ID anonymizer in [anonymizer.py](file:///d:/PROJECTS/BUSify/backend/app/core/data/anonymizer.py).
  - Synthetic college transit network generator in [synthetic_generator.py](file:///d:/PROJECTS/BUSify/backend/app/core/data/synthetic_generator.py) (47 stops, 50 buses, 2,200 student registrations, 105 calendar days, 3,055 demand observations).
- **Sprint 2 (Algorithmic Engines & Benchmarking)**:
  - Demand Forecasting: LightGBM quantile regression ($p50, p90$) and baseline comparison in [lightgbm_model.py](file:///d:/PROJECTS/BUSify/backend/app/core/forecasting/lightgbm_model.py) (+25.76% WAPE improvement over historical weekday baseline).
  - Area-to-stop disaggregator in [disaggregator.py](file:///d:/PROJECTS/BUSify/backend/app/core/forecasting/disaggregator.py).
  - Fleet Allocation: OR-Tools CP-SAT integer program with operational churn dampening in [optimizer.py](file:///d:/PROJECTS/BUSify/backend/app/core/allocation/optimizer.py).
  - Routing: Dual-mode distance matrix service in [matrix_service.py](file:///d:/PROJECTS/BUSify/backend/app/core/routing/matrix_service.py) (OSRM with Haversine fallback).
  - Capacitated VRP solver in [vrp_solver.py](file:///d:/PROJECTS/BUSify/backend/app/core/routing/vrp_solver.py) with automated split-pickup virtual node preprocessing and Capacity-Constrained FFD bin packing fallback.
  - Historical Backtesting Simulator in [simulator.py](file:///d:/PROJECTS/BUSify/backend/app/core/simulation/simulator.py).
- **Sprint 1 & 2 Automated Test Audit**:
  - Full automated test suite in [tests/test_sprint1_data.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint1_data.py) and [tests/test_sprint2_algorithms.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint2_algorithms.py).
  - Audit Result: **10/10 tests passed (100% pass rate)**.
- **Sprint 3 (FastAPI REST Orchestration Layer & Endpoints)**:
  - Main FastAPI application in [main.py](file:///d:/PROJECTS/BUSify/backend/app/main.py) with CORS middleware and `/api/health`.
  - Pydantic v2 schemas in [schemas/__init__.py](file:///d:/PROJECTS/BUSify/backend/app/schemas/__init__.py).
  - REST route modules in [api/](file:///d:/PROJECTS/BUSify/backend/app/api): `/api/stops`, `/api/buses`, `/api/forecast`, `/api/allocation`, `/api/routes`, `/api/crowding`, `/api/simulate`.
  - Upgraded Starlette and FastAPI for modern compatibility with `httpx >= 0.28`.
  - Sprint 3 Automated API Test Suite in [tests/test_sprint3_api.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint3_api.py).
  - Audit Result: **11/11 API tests passed | 21/21 cumulative tests passed (100% pass rate)**.
  - Audit Report: [AUDIT_REPORT_SPRINT_3.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_3.md).
- **Sprint 4 (Frontend Scaffold & Core Component Design System)**:
  - Scaffolded Vite React web application in [frontend/](file:///d:/PROJECTS/BUSify/frontend).
  - Implemented design system with Tailwind CSS v4, Plus Jakarta Sans, and glassmorphism tokens in [index.css](file:///d:/PROJECTS/BUSify/frontend/src/index.css) and [tailwind.config.js](file:///d:/PROJECTS/BUSify/frontend/tailwind.config.js).
  - Built core component library: [Navbar.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/Navbar.jsx), [MetricCard.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/MetricCard.jsx), [StatusBadge.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/StatusBadge.jsx), [ChartContainer.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/ChartContainer.jsx).
  - Implemented REST client service in [api.js](file:///d:/PROJECTS/BUSify/frontend/src/services/api.js).
  - Resolved Tailwind v4 PostCSS relocation (`DEV-LOG-010`).
  - Audit Result: **100% clean production build in 5.53s**.
  - Audit Report: [AUDIT_REPORT_SPRINT_4.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_4.md).
- **Sprint 5 (Dual Dashboards & Interactive Geospatial Maps)**:
  - Built interactive Leaflet map component in [LeafletMap.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/LeafletMap.jsx) with custom SVG DivIcons, zone color coding, and dynamic CVRP vehicle route polylines.
  - Implemented Transport Office Dashboard in [OfficeDashboard.jsx](file:///d:/PROJECTS/BUSify/frontend/src/views/OfficeDashboard.jsx) with KPI metric cards, Recharts comparative capacity bar charts, zone allocation table, and one-click historical simulation runner.
  - Implemented Student Commuter Portal in [StudentView.jsx](file:///d:/PROJECTS/BUSify/frontend/src/views/StudentView.jsx) with boarding stop selector, assigned bus card, reverse-scheduled pickup arrival time, and real-time crowd congestion badges.
  - Integrated dual-surface role switching in [App.jsx](file:///d:/PROJECTS/BUSify/frontend/src/App.jsx).
  - Audit Result: **100% clean production build in 9.04s | 21/21 backend tests passing**.
  - Audit Report: [AUDIT_REPORT_SPRINT_5.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_5.md).
- **Sprint 6 (STA, Edge-Case Stress Testing, & Master System Certification)**:
  - Bytecode Static Analysis: Passed `python -m compileall backend/app` with 0 syntax or compilation errors.
  - Edge-case and stress test suite in [tests/test_sprint6_edge_cases.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint6_edge_cases.py):
    - Extreme demand surge handling ($> 2\times$ capacity, multi-bus splits).
    - Zero demand minimum route coverage guarantees.
    - CVRP strict vehicle capacity invariant validation across varying load distributions.
    - OSRM & Haversine distance matrix metric properties (symmetry, non-negativity, triangle inequality).
    - SHA-256 salted anonymizer collision-resistance across 500 distinct IDs.
    - REST API boundary conditions and input validation ($422$ and $404$ statuses).
  - Production Frontend Bundling: 100% clean Vite build in < 1.0s (`dist/` asset size optimized).
  - Cumulative Regression Suite: **27 / 27 tests passed (100% pass rate)**.
- **Sprint 7 (Pragmatic Operational Workflows & Authentic Editorial Design System)**:
  - Redesigned visual aesthetic inspired by publication-grade typography from AudioTag-AI:
    - Warm natural paper palette (`#f7f8f5`) with deep forest-charcoal ink text (`#18201d`).
    - Editorial **Georgia Serif** headings, kickers, side notes, and 34px stat numerals.
    - Completely removed all emojis across UI, badges, and documentation.
    - Upgraded Leaflet map to clean CartoDB Positron architectural light tiles with clean SVG pins.
  - Implemented 3-Step College Transport Office Workflow:
    - Timetable scenario selector (Regular Academic Day, Semester Exams, Placement Drives, Monsoon Rain Surge).
    - Dynamic fleet balancing and one-click "Approve & Dispatch Today's Fleet" broadcast.
    - Vehicle Dispatch Roster with drivers, phones, routes, and interactive printable Driver Trip Sheet modal.
  - Implemented Authentic Student Commuter Workflow:
    - University Roll Number lookup (`21CS104`, `22ME045`, etc.) with digital university bus pass.
    - Guaranteed seat number assignment (`Seat #38 Confirmed`), vehicle captain direct phone contact, and pickup countdown.
    - Live "Not Riding Today" / "Re-confirm Seat" attendance switch that dynamically releases campus seat capacity in real-time.
  - Backend Workflow Endpoints in [routes_workflow.py](file:///d:/PROJECTS/BUSify/backend/app/api/routes_workflow.py):
    - `GET /api/workflow/operational-manifest`
    - `GET /api/workflow/student-profile`
    - `POST /api/workflow/student-opt-out`
  - Automated Workflow Test Suite in [tests/test_sprint7_workflow.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint7_workflow.py).
  - Cumulative Regression Suite: **31 / 31 tests passed (100% pass rate)**.
- **Sprint 8 (Real-World Road Routing, Multi-Campus Scalability, Orientation Compass & Interactive Tooltips)**:
  - **Real Turn-by-Turn Road Routing (`DEV-LOG-013`)**:
    - Replaced straight-line Euclidean interpolation with high-resolution OpenStreetMap (OSRM) turn-by-turn road geometry via [road_geometry_service.py](file:///d:/PROJECTS/BUSify/backend/app/core/routing/road_geometry_service.py).
    - Bus routes now strictly trace actual streets, highways, and river bridges without cutting through buildings or water bodies.
    - Added solid, smooth polyline styling (`dashArray: null`, `weight: 4.5`, `lineJoin: 'round'`) with client-side OSRM fallback in [LeafletMap.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/LeafletMap.jsx).
  - **Multi-Institution Scalability (`DEV-LOG-015`)**:
    - Built multi-campus architecture in [routes_institution.py](file:///d:/PROJECTS/BUSify/backend/app/api/routes_institution.py) with endpoints `GET /api/institutions`, `GET /api/institutions/active`, `POST /api/institutions/active`, and `POST /api/institutions`.
    - Integrated pre-configured institutional profiles: Central Engineering College Trichy, NIT Trichy, Anna University Guindy Chennai, PSG Tech Coimbatore, IIT Madras.
    - Implemented topbar Campus Switcher dropdown and "+ Register New College / Campus" modal in [Navbar.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/Navbar.jsx) allowing any university to onboard with custom fleet sizes, capacities, and coordinates.
    - Dynamically anchors all radial geocoding, depot pin placement, distance calculations, and CVRP solver bounds to the selected college hub.
  - **Corridor Compass & Spatial Orientation**:
    - Added the **Corridor Compass** toolbar atop the map with directional pills (`Zone A: North`, `Zone B: East`, `Zone C: South`, `Zone D: West`, `Zone E: Central Urban`) to eliminate spatial ambiguity and allow 1-click focus onto any corridor.
    - Enhanced stop tooltips and popups with corridor highway names, cardinal bearings, and real-time Haversine distance to campus hub.
  - **Interactive Question Mark Micro-Tooltips (`InfoHint`)**:
    - Built [InfoHint.jsx](file:///d:/PROJECTS/BUSify/frontend/src/components/InfoHint.jsx) with clean CSS micro-tooltips (`.info-hint`, `.hint-trigger`, `.hint-box`).
    - Added hoverable `?` explanations over every table column header (`Stop Name ?`, `Zone / Corridor ?`, `Student Headcount ?`, `Suggested Bus ?`, `Latitude & Longitude ?`, `Geocoding Status ?`), geocoding badges, and benchmark comparison cards in [OfficeDashboard.jsx](file:///d:/PROJECTS/BUSify/frontend/src/views/OfficeDashboard.jsx).
  - **Automated Regression Test Suite**:
    - Created [tests/test_sprint8_institution_and_roads.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint8_institution_and_roads.py).
    - Cumulative Regression Suite: **38 / 38 tests passed (100% pass rate)**.




