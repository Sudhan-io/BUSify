# BUSify — Architecture and Data Contracts

**Source of truth:** actual repository files at `d:/PROJECTS/BUSify`.
**Last audited:** 2026-10-27.

---

## 1. Repository Layout

```
BUSify/
├── frontend/           React + Vite + Recharts + Leaflet
│   └── src/
│       ├── App.jsx                 — app shell, routing between roles, session, health check
│       ├── components/
│       │   ├── Navbar.jsx          — institution switcher, role tabs, date picker, auth
│       │   ├── LeafletMap.jsx      — map with stops, routes, filters (42 KB; very large)
│       │   ├── LoginModal.jsx      — officer login modal
│       │   ├── MetricCard.jsx      — single KPI display
│       │   ├── ChartContainer.jsx  — thin recharts wrapper (475 B)
│       │   ├── StatusBadge.jsx     — manifest status chip
│       │   └── InfoHint.jsx        — tooltip hint
│       ├── views/
│       │   ├── OfficeDashboard.jsx — ENTIRE office UI, 1278 lines, all workflows on one page
│       │   └── StudentView.jsx     — student pass, opt-out, map
│       ├── services/
│       │   ├── api.js              — axios client with auth interceptors, all API calls
│       │   └── auth.js             — sessionStorage JWT, describeError
│       └── constants/status.js    — CHECKING/HEALTHY/DEGRADED/OFFLINE enum + colours
├── backend/app/
│   ├── main.py                    — FastAPI app, CORS, health, router mounting
│   ├── config.py                  — pydantic-settings from .env
│   ├── database.py                — SQLAlchemy engine, WAL mode, foreign keys
│   ├── models/                    — SQLAlchemy ORM tables
│   │   ├── bus.py                 — Bus (bus_id PK, seats, driver_name, etc.)
│   │   ├── stop.py                — Stop (stop_id PK, area_id, sequence_order, lat/lng)
│   │   ├── registration.py        — Registration (student_hash FK stop_id)
│   │   ├── demand.py              — AreaDemand (area_id, date, p50, p90)
│   │   ├── plan.py                — Plan (date, scenario) — HAS NO READER OR WRITER YET
│   │   ├── calendar.py            — AcademicCalendar
│   │   └── student_attendance.py  — StudentAttendance (SHA-256 id, roll_hash, date, traveling)
│   ├── schemas/__init__.py        — Pydantic schemas: BusSchema, StopCreate/Update, etc.
│   ├── auth/
│   │   ├── routes_auth.py         — POST /api/auth/token → {access_token, role, name}
│   │   └── auth_service.py        — require_admin dep, hmac.compare_digest
│   ├── api/
│   │   ├── __init__.py            — api_router aggregator
│   │   ├── routes_buses.py        — GET/POST/PUT/DELETE /api/buses
│   │   ├── routes_stops.py        — GET/POST/PUT/DELETE /api/stops
│   │   ├── routes_forecast.py     — GET /api/forecast
│   │   ├── routes_allocation.py   — GET /api/allocation
│   │   ├── routes_routing.py      — GET /api/routes
│   │   ├── routes_crowding.py     — GET /api/crowding
│   │   ├── routes_simulation.py   — POST /api/simulate
│   │   ├── routes_workflow.py     — GET /api/workflow/operational-manifest,
│   │   │                            GET /api/workflow/student-profile,
│   │   │                            POST /api/workflow/student-opt-out,
│   │   │                            POST /api/workflow/upload-stops-csv,
│   │   │                            GET /api/workflow/template-csv
│   │   └── routes_institution.py  — GET/POST /api/institutions, /active
│   └── core/
│       ├── forecasting/
│       │   ├── lightgbm_model.py  — LightGBM p50/p90 quantile forecaster
│       │   ├── feature_pipeline.py— feature engineering, lag/rolling
│       │   └── disaggregator.py   — area-level demand → per-stop demands
│       ├── allocation/
│       │   └── optimizer.py       — OR-Tools CP-SAT fleet allocator
│       ├── routing/
│       │   ├── vrp_solver.py      — OR-Tools VRP solver (CVRP)
│       │   ├── road_geometry_service.py — OSRM polyline fetcher + FIFO cache
│       │   └── matrix_service.py  — OSRM distance/duration matrix
│       ├── simulation/
│       │   └── simulator.py       — 7-day backtest, serial
│       └── data/
│           ├── synthetic_generator.py — AREAS_CONFIG, stop seed data
│           └── anonymizer.py         — hash_student_id (HMAC-SHA256)
├── docs/                          — existing docs (do not delete)
│   ├── OUTSTANDING_ISSUES.md      — AUTHORITATIVE bug register (read first)
│   └── remediation/               — this new directory
├── tests/fixtures/synthetic/      — synthetic test fixtures + generator
└── busify.db                      — SQLite DB (tracked intentionally — see M-24)
```

---

## 2. Frontend Architecture

**Framework:** React 18 + Vite 8.  
**Styling:** Tailwind CSS utility classes inline; global design tokens in `index.css`.  
**State management:** Component-local `useState`/`useEffect`. No Redux, no Zustand.  
**Navigation:** Zero React Router. Role switch is a single `activeRole` state in `App.jsx`. The entire Transport Office UI is one 1278-line file (`OfficeDashboard.jsx`). Adding pages requires splitting this file and adding a router.  
**Charts:** Recharts (`BarChart` only).  
**Map:** Leaflet via `react-leaflet`, custom `L.divIcon` HTML markers.

**Critical gap:** `OfficeDashboard.jsx` renders all 8 conceptual sections vertically — scenario selector, KPI cards, manifest table, fleet management, map, chart, simulation, CSV modal — on a single scroll. There is no page-level navigation. Adding navigation requires extracting each section into a separate route component.

---

## 3. Backend Architecture

**Framework:** FastAPI (ASGI, Uvicorn/Gunicorn).  
**Database:** SQLite in dev, PostgreSQL in production (URL from env). WAL mode enabled.  
**Auth:** HS256 JWT, 8-hour expiry. Two roles: `transport_officer`, `admin`.  
**Algorithms:** OR-Tools CP-SAT (allocation), OR-Tools VRP (routing), LightGBM (forecasting).  
**Routing geometry:** OSRM self-hosted (or Haversine fallback when `ENABLE_OFFLINE_HAVERSINE_FALLBACK=True`).

**Institution state:** `INSTITUTIONS_REGISTRY` is an in-memory list in `routes_institution.py`. Under multi-worker Gunicorn, mutations (POST /institutions) reach only one worker. This is `C-04` in the outstanding issues register.

---

## 4. Authoritative Metric Definitions

These definitions are the intended semantics. Verify each data path when implementing.

| Metric | Definition | Source | Known status |
|:---|:---|:---|:---|
| Registered vehicles | Rows in `buses` table | `GET /api/buses` → `len()` | Confirmed correct |
| Active vehicles | `buses.is_active = True` | Filter in `list_fleet` | Correct, but manifest uses a derived sequential count, not this |
| Total usable seats | `sum(bus.seats for active buses)` | Not computed anywhere as a single number | **MISSING** — manifest uses `len(manifest) * DEFAULT_BUS_CAPACITY` which ignores per-bus capacity |
| Expected demand | `p90_demand * surge_multiplier` per area | Forecaster → workflow | Confirmed |
| Assigned load | Sum of `stop.demand` per route from VRP solver | `route.total_riders` | Confirmed |
| Standing passengers | `max(0, demand - capacity)` per area from CP-SAT slack `s[a]` | `alloc_res["total_standing"]` | Confirmed |
| Fleet utilization | `total_riders / (total_active_buses * capacity) * 100` | `routes_workflow.py:130` | Uses `DEFAULT_BUS_CAPACITY` not per-bus seats |
| Seating equity | Not formally defined anywhere | — | **UNDEFINED** — dashboard shows "100% equity" when `total_standing == 0` |
| Fleet churn | `sum(abs(allocated - baseline))` | `routes_workflow.py:134` | Confirmed; two different baselines exist (H-05) |
| Dispatch readiness | No concept exists in backend | — | **MISSING** — "Approve & Dispatch" button is client-side only, no server guard |
| Manifest version | No versioning | — | **MISSING** — dispatch references no pinned manifest |

---

## 5. API Contracts (Critical Endpoints)

### GET /api/workflow/operational-manifest
```json
{
  "date": "2026-10-15",
  "scenario": "REGULAR",
  "surge_multiplier": 1.0,
  "bus_capacity": 55,
  "total_active_buses": 38,
  "total_seats_deployed": 2090,
  "total_expected_riders": 1932,
  "overall_utilization_pct": 92.4,
  "total_standing": 0,
  "total_empty": 158,
  "churn": 4,
  "manifest": [...],
  "area_allocation": {"AREA_A": 8, ...},
  "baseline_allocation": {"AREA_A": 10, ...},
  "total_fleet_churn": 12
}
```
**Known issue H-07:** `manifest[n].bus_code` is `BUS-{sequential}` not drawn from the `buses` table.  
**Known issue H-08:** `driver_name` assigned by `(bus_idx-1) % 10` — same driver on two routes possible.

### GET /api/workflow/student-profile
- Scoped to 4-entry `DEMO_STUDENT_ROSTER` (C-01a, C-02).
- Returns `seat_guarantee: "CONFIRMED_NO_STANDING"` and hardcoded `occupancy_pct: 78` (C-07 / H-16).

### POST /api/auth/token
Returns `{access_token, token_type, role, name}`. Token stored in `sessionStorage`.

### GET /api/buses
Returns all Bus rows via `Bus.to_dict()`. Active/inactive flag exists; manifest ignores it.

---

## 6. Cross-Page Synchronization

| Data | Owner | Consumer | Sync mechanism |
|:---|:---|:---|:---|
| `selectedDate` | `App.jsx` state | `OfficeDashboard`, `StudentView` | Props |
| `activeInstitution` | `App.jsx` state | All components | Props |
| `activeScenario` | `OfficeDashboard` state | Manifest fetch trigger | Local effect deps |
| Auth session | `sessionStorage` (token) | `api.js` interceptor | Token read on every request |
| Manifest data | `OfficeDashboard` state | KPI cards, table, trip sheet modal | Local state — no global store |
| Bus list | `OfficeDashboard` state | Fleet table, add/edit modal | Local state |

**Risk:** `OfficeDashboard` loads manifest, buses, forecast, and stops in a single `Promise.all`. If any fails, all four are lost. No partial rendering. No retry.

---

## 7. Unknowns (require investigation before implementation)

- Whether the Python environment on the dev machine can run pytest (§1 of OUTSTANDING_ISSUES.md says Python 3.10 globally, target is 3.12, no venv).
- Whether OSRM is available at runtime. Tests that call `/routes` or `/operational-manifest` may 500 without it.
- Whether `alembic` is intended to be used for migrations (it is in requirements but unused — see M-24).
- Whether the `Plan` model is intended to persist approved manifests (it has no reader or writer — H-21).
