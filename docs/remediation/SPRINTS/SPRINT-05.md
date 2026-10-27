# Sprint-5 — Fleet, Driver, Student and Demand Management

**Status:** DONE<br>
**Prerequisite:** Sprint-4 DONE (Dispatch Manifest, real bus/driver assignment, plan approval guard).<br>
**Objective:** Deliver authoritative, database-backed fleet and driver management, student registration and demand summaries, lifecycle startup hygiene (M-11, M-12), and file upload format accuracy (M-10).<br>
**User-visible outcome:** Fleet & Drivers page enables full CRUD with driver conflict safeguards; Students & Demand page displays real registration counts (2,200 total) and zone distributions; server startup uses clean FastAPI lifespan handler.

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-4 DONE), `DEFECT_REGISTER.md`.

Key defects and requirements:
- **M-10**: UI advertised `.xlsx` but file input only accepts `.csv,.txt`. Align UI file input, text, and backend validation.
- **M-11**: `Base.metadata.create_all()` and `seed_default_institutions()` executed at module import time; convert to FastAPI `lifespan` handler.
- **M-12**: Raw `ALTER TABLE` column migrations in `routes_buses.py` and `models/plan.py` executed at top-level import; run inside startup lifespan.
- **Phase 2 (Fleet Management)**: Authoritative DB CRUD, seat bounds validation (10–120), unique bus ID, corridor validation, and prevention of deletion when a bus is assigned to an approved plan.
- **Phase 3 (Driver Management)**: Single source of truth for drivers on `Bus` model, dedicated drivers listing endpoint, prevention of conflicting driver assignments across multiple active buses for simultaneous trips.
- **Phase 4 (Student and Demand Management)**: Connect `stops` to `registrations` table to expose real student registration counts per stop; add student registrations search endpoint with privacy protection; ensure student opt-out does not corrupt locked approved plans.

---

## Scope

### In scope

1. **Server Startup & Lifecycle Hygiene (`main.py`, `routes_buses.py`, `models/plan.py`)**:
   - Create FastAPI `lifespan` async context manager in `main.py` (M-11).
   - Move database table creation and seed calls into `lifespan`.
   - Move `_ensure_bus_columns()` and `_ensure_plan_columns()` out of top-level module scope into lifespan startup (M-12).
2. **Fleet Management (`routes_buses.py`, `schemas/__init__.py`, `FleetAndDrivers.jsx`)**:
   - `GET /api/buses`: Support query filtering by `area_id`, `is_active`, and `search`.
   - `POST /api/buses`: Validate unique `bus_id`, seats (10–120), valid `default_area_id`.
   - `PUT /api/buses/{bus_id}`: Validate fields, update specs, driver, and active status.
   - `DELETE /api/buses/{bus_id}`: Check `plans` table; reject deletion with HTTP 409 if assigned to approved dispatch plans.
3. **Driver Management (`routes_buses.py`, `routes_workflow.py`, `FleetAndDrivers.jsx`)**:
   - Add `GET /api/buses/drivers` endpoint to list all assigned drivers, vehicle mappings, contact numbers, and active status.
   - Prevent conflicting driver assignments: reject assigning the same driver to more than one active vehicle.
   - Exclude inactive drivers from manifest generation.
4. **Student & Demand Management (`routes_stops.py`, `routes_workflow.py`, `StudentsAndDemand.jsx`)**:
   - Compute real registration counts per stop via `registrations` table in `GET /api/stops`.
   - Add `GET /api/workflow/students/registrations` endpoint with pagination, zone/stop filtering, and student ID hash masking.
   - Add `GET /api/workflow/demand-summary` aggregating real registration counts, stop counts, and forecast demand per area.
   - Protect approved plans: record student preference changes while keeping historical approved plans locked for operational stability.
5. **CSV/File Upload Format Alignment (`OfficeLayout.jsx`, `OfficeDashboard.jsx`, `routes_workflow.py`)**:
   - Resolve M-10: clarify UI label to `.CSV, .TXT` and ensure file dialog allows matching types.
   - Add clear error if a binary `.xlsx` file is uploaded.

### Out of scope

- Direct geographic polyline editing on map (Sprint-6).
- Student authenticated login portal and personalized route view (Sprint-7).
- Docker deployment consolidation and accessibility audit (Sprint-8).

---

## Acceptance Criteria Verification

- [x] **Criterion 1:** `Base.metadata.create_all()` and migrations run in FastAPI lifespan (0 import-time side-effects) (M-11, M-12 verified).
- [x] **Criterion 2:** `GET /api/buses` supports filtering; `POST /api/buses` and `PUT /api/buses/{bus_id}` validate inputs (verified).
- [x] **Criterion 3:** `DELETE /api/buses/{bus_id}` returns 409 if bus has approved dispatch records in `plans` (verified).
- [x] **Criterion 4:** Conflicting driver assignments (same driver on $\ge 2$ active buses) rejected with HTTP 400 (verified).
- [x] **Criterion 5:** `GET /api/buses/drivers` returns roster of drivers with assigned bus and active status (verified).
- [x] **Criterion 6:** `GET /api/stops` returns accurate `student_count` matching `registrations` table (total 2,200) (verified).
- [x] **Criterion 7:** `GET /api/workflow/students/registrations` provides searchable, paginated registrations with hashed IDs (verified).
- [x] **Criterion 8:** `POST /api/workflow/student-opt-out` preserves approved plan locking (verified).
- [x] **Criterion 9:** Full backend test suite passing: **103 passed, 0 failed in 128.72s** (verified).
- [x] **Criterion 10:** Frontend lint (0 errors) and production build clean in 12.19s (verified).

