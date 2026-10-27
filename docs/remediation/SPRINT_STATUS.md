# BUSify — Sprint Status Tracker

**Update this file after completing each sprint or work package.**
**A sprint is NOT done unless verification evidence is recorded.**

---

## Legend

| Status | Meaning |
|:---|:---|
| `NOT STARTED` | Sprint not begun |
| `IN PROGRESS` | Active work underway — note what is incomplete |
| `BLOCKED` | Cannot proceed — document the blocker |
| `DONE` | All acceptance criteria met and verified — evidence recorded below |

---

## Sprint Status Table

| Sprint | Title | Status | Completion criteria summary | Blockers | Evidence |
|:---|:---|:---|:---|:---|:---|
| Sprint-0 | Baseline, loading states, dead code removal | **DONE** | No hardcoded fallback numbers; loading spinner renders; API errors shown inline; dead files removed; environment verified | None | Build: 0 errors; Lint: 0 errors; Pytest: 52 passed, 0 failed |
| Sprint-1 | App shell, navigation, routing | **DONE** | React Router installed; 7 office tabs navigable; student has 3 sections; existing state logic preserved | None | Build: 0 errors; Lint: 0 errors; Pytest: 52 passed; Browser subagent: 7 routes + student + 404 verified |
| Sprint-2 | Data integrity, institution persistence | **DONE** | KPI sources canonical; institution DB-persisted; campus coords deduped; chart renders data | None | Build: 0 errors; Lint: 0 errors; Pytest: 84 passed, 0 failed in 95.57s |
| Sprint-3 | Daily Planning workflow | **DONE** | Guided 4-step flow; constraint display; allocation review; no conflicting baselines | None | Build: 0 errors; Lint: 0 errors; Pytest: 87 passed, 0 failed |
| Sprint-4 | Dispatch Manifest — real buses, approval guard | **DONE** | Manifest uses DB buses/drivers; table paginated; dispatch endpoint creates Plan; button disabled without valid manifest | None | Build: 0 errors; Lint: 0 errors; Pytest: 94 passed, 0 failed |
| Sprint-5 | Fleet & Drivers + Students & Demand management | **NOT STARTED** | Fleet CRUD in dedicated page; student demand aggregation | Requires Sprint-1, Sprint-2 | — |
| Sprint-6 | Routes & Map correctness | **NOT STARTED** | Arrival time field name fixed; stop detail fields correct; zone metadata consistent; coordinates canonical | Requires Sprint-2 | — |
| Sprint-7 | Student Commuter experience | **NOT STARTED** | Pass shows correct occupancy; route sections clear; no pre-auth roll selector exposure | Requires Sprint-5, Sprint-2 | — |
| Sprint-8 | Security, accessibility, deployment | **NOT STARTED** | All forms keyboard-accessible; all modals have focus trap; Docker paths fixed; requirements consolidated; regression suite passes | Requires all prior | — |

---

## Sprint-0 Detail

**Objective:** Establish a clean, honest baseline before any navigation or UX work.

**Acceptance criteria:**
- [x] No hardcoded fallback numbers (`50`, `2750`, `2150`) rendered as operational data.
- [x] `loading` state in `OfficeDashboard` renders a visible spinner/skeleton in hero and KPI cards.
- [x] API errors in `OfficeDashboard` render as inline alerts, not console-only (`manifestError` banner).
- [x] `loading` state in `StudentView` renders correctly (loading banner and fallback indicators).
- [x] Dead files removed: `src/App.css`, `tailwind.config.js`.
- [x] Page `<title>` changed from "frontend" to "BUSify | Transit Intelligence", meta description added.
- [x] `alert()` calls in `OfficeDashboard.jsx` replaced with in-app error UI (`busError` alert).
- [x] Python environment confirmed: Python 3.12 (with pytest 9.1.1).
- [x] Baseline test run: 52 passed, 0 failed, 4 warnings in 84.93s.

**Verification commands & results:**
```bash
# Frontend build
cd frontend && npm run build   # PASSED: vite v8.3.4, 0 errors, built in 1.11s
cd frontend && npm run lint    # PASSED: 0 errors, 23 warnings (0 unused loading warnings)

# Backend tests
cd d:\PROJECTS\BUSify
$env:PYTHONPATH="."
py -3.12 -m pytest backend/app/tests/ -v --tb=short
# PASSED: 52 passed, 0 failed, 4 warnings in 84.93s
```

**Files to change:**
- `frontend/src/views/OfficeDashboard.jsx` (loading states, error rendering, remove hardcoded fallbacks, remove `alert()`)
- `frontend/src/views/StudentView.jsx` (loading state rendering)
- `frontend/index.html` (title, meta description)
- Remove: `frontend/src/App.css`, `frontend/src/assets/hero.png`, `frontend/tailwind.config.js` (if confirmed unused)

**Do NOT change:**
- Backend API contracts.
- Routing or navigation structure (that is Sprint-1).
- Any algorithm code.
- `busify.db`.

---

## Sprint-1 Detail

**Objective:** Create an app shell with persistent navigation. Officer can reach 7 destinations. Student has 3 clear sections.

**Prerequisites:** Sprint-0 DONE.

**Acceptance criteria:**
- [x] `npm run build` and `npm run lint` both clean (0 errors).
- [x] 7 office tabs navigable; each renders the correct section (`/office/overview`, `/office/planning`, `/office/routes`, `/office/manifest`, `/office/fleet`, `/office/students`, `/office/reports`).
- [x] Student view renders 3 sections (My Bus Pass, My Route, Travel Status) clearly with dedicated sub-navigation.
- [x] Active tab is visually distinct from inactive tabs.
- [x] Zone filter tabs do not clip on a 1280px viewport (NAV-004 resolved via `min-w-0` and responsive wrapping).
- [x] `.pulse` animation has `@keyframes pulse-dot` and `prefers-reduced-motion` guard (M-14 resolved).
- [x] No data regression: all sections that loaded data before still load data in their new location via `OfficeLayout` shared context.
- [x] Backend test results unchanged from Sprint-0 baseline (52 passed, 0 failed).

**Verification commands & results:**
```bash
# Frontend build & lint
cd frontend; npm run lint    # PASSED: 0 errors
cd frontend; npm run build   # PASSED: 0 errors, built in 1.19s

# Backend tests
$env:PYTHONPATH="."
py -3.12 -m pytest backend/app/tests/ -v --tb=short
# PASSED: 52 passed, 0 failed, 4 warnings in 56.45s

# Browser subagent E2E test:
# Verified / -> /office/overview redirect, all 7 office tabs, modal dialogs,
# student view with 3 section tabs, unknown route 404 page, back/forward navigation.
```

**Files changed:**
- `frontend/package.json` & `package-lock.json` (installed `react-router-dom@^7.18.4`)
- `frontend/src/index.css` (`@keyframes pulse-dot` and `prefers-reduced-motion`)
- `frontend/src/hooks/usePageTitle.js` (dynamic title per route)
- `frontend/src/layouts/OfficeLayout.jsx` (persistent office sub-nav, shared context shell, CSV modal)
- `frontend/src/pages/office/OfficeOverview.jsx`
- `frontend/src/pages/office/DailyPlanning.jsx`
- `frontend/src/pages/office/RoutesAndMap.jsx` (NAV-004 horizontal overflow fix)
- `frontend/src/pages/office/DispatchManifest.jsx`
- `frontend/src/pages/office/FleetAndDrivers.jsx`
- `frontend/src/pages/office/StudentsAndDemand.jsx`
- `frontend/src/pages/office/ReportsAndHistory.jsx`
- `frontend/src/pages/NotFound.jsx` (404 unknown route handler)
- `frontend/src/views/StudentView.jsx` (3 structured commuter sections and sub-navigation)
- `frontend/src/components/Navbar.jsx` (React Router navigation, brand link, active role state)
- `frontend/src/App.jsx` (BrowserRouter and Routes configuration)

---

## Sprint-2 Detail

**Objective:** Make every KPI authoritative. Persist institution registry. Canonicalize campus coordinates.

**Status:** DONE (Tasks 2.1, 2.4-2.7 complete and verified; 84 backend regression tests passed in 95.57s)

**Key tasks:**
1. [x] Persist `INSTITUTIONS_REGISTRY` to a DB table (SEC-001 / C-04) — *Task 2.1 complete*.
2. [x] Canonical campus coordinates: extract to a single constant consumed by all components (M-02) — *Task 2.1 complete*.
3. [x] `total_seats_deployed`: use `sum(bus.seats for active buses)` not `len(manifest) * DEFAULT_BUS_CAPACITY` (DATA-002) — *Task 2.4 complete*.
4. [x] Define seating equity metric explicitly; compute per-area utilization variance; expose it from the API (DATA-003) — *Task 2.5 complete*.
5. [x] Disaggregator zero-division guard (DATA-004 / H-11) — *Task 2.6 complete*.
6. [x] Demand/capacity bar chart: render loading skeleton and empty states (M-15) — *verified with frontend lint and production build on 2026-10-27*.

---

## Handoff Note — Sprint-0 — 2026-10-27

**Completed tasks:**
- **Task 0.1:** Verified development environment (Python 3.12.5, pytest 9.1.1, Node/Vite build and oxlint).
- **Task 0.2:** Removed hardcoded fallback numbers (`|| 50`, `|| 2750`, `|| 2150`) from `OfficeDashboard.jsx` hero section and MetricCards.
- **Task 0.3:** Added `loading` prop and pulse skeleton rendering to `MetricCard.jsx`; wired `loading` prop to all MetricCards in `OfficeDashboard.jsx`.
- **Task 0.4:** Added inline `manifestError` state and banner alert in `OfficeDashboard.jsx` (errored data displays empty/error UI, not fabricated numbers).
- **Task 0.5:** Replaced browser `alert()` dialogs in `OfficeDashboard.jsx` with inline `busError` alert banner in fleet management section and inside Add/Edit Bus modal.
- **Task 0.6:** Rendered `loading` indicator banner and loading fallback text across `StudentView.jsx` digital boarding pass fields.
- **Task 0.7:** Fixed page `<title>` to "BUSify | Transit Intelligence" and added meta description in `frontend/index.html`.
- **Task 0.8:** Removed dead unimported files: `frontend/src/App.css` and `frontend/tailwind.config.js`.

**Modified files:**
- `frontend/index.html`
- `frontend/src/components/MetricCard.jsx`
- `frontend/src/views/OfficeDashboard.jsx`
- `frontend/src/views/StudentView.jsx`
- Deleted: `frontend/src/App.css`, `frontend/tailwind.config.js`
- Docs: `docs/remediation/SPRINT_STATUS.md`, `docs/remediation/DEFECT_REGISTER.md`, `docs/remediation/SPRINTS/SPRINT-00.md`

**Verification results:**
- Frontend Build: `npm run build` PASSED (0 errors, 1.11s).
- Frontend Lint: `npm run lint` PASSED (0 errors, 23 warnings — 0 unused loading warnings).
- Backend Tests: `py -3.12 -m pytest backend/app/tests/` PASSED (52 passed, 0 failed, 4 warnings in 84.93s baseline; regression pass in 60.38s).
- Code Scans: 0 matches for `|| 50 / || 2750 / || 2150`; 0 matches for `alert(`.

**Outstanding defects from this sprint:** None.
**Next task for next session:** Sprint-1 Task 1.1 — Install `react-router-dom` and verify dependencies in `frontend/package.json`. Follow `docs/remediation/SPRINTS/SPRINT-01.md`.

---

## Handoff Note — Sprint-1 — 2026-10-27

**Completed tasks:**
- **Task 1.1:** Installed `react-router-dom@^7.18.4` in `frontend/package.json` and verified zero dependency conflicts with React 19.
- **Task 1.2:** Created route components in `frontend/src/pages/office/` (`OfficeOverview.jsx`, `DailyPlanning.jsx`, `RoutesAndMap.jsx`, `DispatchManifest.jsx`, `FleetAndDrivers.jsx`, `StudentsAndDemand.jsx`, `ReportsAndHistory.jsx`) and `frontend/src/pages/NotFound.jsx`.
- **Task 1.3:** Wired client-side routing in `App.jsx` with `<BrowserRouter>` and nested `<Routes>`, redirecting `/` and `/office` to `/office/overview`.
- **Task 1.4:** Implemented `OfficeLayout.jsx` shell with persistent top sub-navigation bar (7 tabs) with visual active-state indicators, providing shared state through React Router's `<Outlet context={officeContext} />`.
- **Task 1.5:** Extracted Hero and 4 MetricCards into `OfficeOverview.jsx` with quick navigation directory.
- **Task 1.6:** Extracted Scenario condition selector and dynamic allocation chart into `DailyPlanning.jsx`.
- **Task 1.7:** Extracted Map and zone filters into `RoutesAndMap.jsx`, resolving NAV-004 horizontal overflow using `min-w-0` and safe responsive wrapping.
- **Task 1.8:** Extracted Driver Manifest table and Driver Trip Sheet modal into `DispatchManifest.jsx`.
- **Task 1.9:** Extracted Fleet inventory table and Add/Edit Bus modal into `FleetAndDrivers.jsx`.
- **Task 1.10:** Implemented `StudentsAndDemand.jsx` for stop-level commuter demand inspection and zone filtering.
- **Task 1.11:** Extracted 7-Day Performance Backtest simulation and CSV Benchmark savings audit into `ReportsAndHistory.jsx`.
- **Task 1.12:** Implemented 3 structured commuter sections in `StudentView.jsx` (My Bus Pass, My Route, Travel Status) with tabbed sub-navigation.
- **Task 1.13:** Created `usePageTitle.js` hook updating `<title>` dynamically per active route.
- **Task 1.14:** Added `@keyframes pulse-dot` and `prefers-reduced-motion` guard to `.pulse` class in `frontend/src/index.css` (M-14).
- **Task 1.15:** Updated `Navbar.jsx` role tabs to use `useNavigate` and `useLocation` for instant switching and deep link persistence between `/office/overview` and `/student`.

**Modified files:**
- `frontend/package.json` & `frontend/package-lock.json`
- `frontend/src/index.css`
- `frontend/src/App.jsx`
- `frontend/src/components/Navbar.jsx`
- `frontend/src/views/StudentView.jsx`
- `frontend/src/hooks/usePageTitle.js`
- `frontend/src/layouts/OfficeLayout.jsx`
- `frontend/src/pages/office/OfficeOverview.jsx`
- `frontend/src/pages/office/DailyPlanning.jsx`
- `frontend/src/pages/office/RoutesAndMap.jsx`
- `frontend/src/pages/office/DispatchManifest.jsx`
- `frontend/src/pages/office/FleetAndDrivers.jsx`
- `frontend/src/pages/office/StudentsAndDemand.jsx`
- `frontend/src/pages/office/ReportsAndHistory.jsx`
- `frontend/src/pages/NotFound.jsx`
- Docs: `docs/remediation/SPRINT_STATUS.md`, `docs/remediation/DEFECT_REGISTER.md`, `docs/remediation/DECISIONS.md`, `docs/remediation/SPRINTS/SPRINT-01.md`

**Verification results:**
- Frontend Lint: `cd frontend; npm run lint` PASSED (0 errors).
- Frontend Build: `cd frontend; npm run build` PASSED (0 errors, 1.19s).
- Backend Tests: `py -3.12 -m pytest backend/app/tests/` PASSED (52 passed, 0 failed in 56.45s).
- Browser E2E Test: PASSED (all 7 office routes, tab highlights, modal sheets, student section switcher, 404 page, back/forward history verified).
- Git Checks: `git diff --check` PASSED (0 whitespace errors).

**Outstanding defects from this sprint:** None.
**Next task for next session:** Sprint-2 Task 2.1 — Persist `INSTITUTIONS_REGISTRY` to a DB table (SEC-001) and canonicalize campus coordinates (M-02). Follow `docs/remediation/SPRINTS/SPRINT-02.md`.

---

## Handoff Note — Sprint-2 Task 2.1 — 2026-10-27

**Completed tasks:**
- **Task 2.1 (SEC-001):** Implemented `Institution` SQLAlchemy model in `backend/app/models/institution.py` with `institutions` table and idempotent startup seeding in `main.py`. Replaced in-memory `INSTITUTIONS_REGISTRY` in `routes_institution.py` with transactional DB operations across all endpoints (`GET /institutions`, `GET /institutions/active`, `POST /institutions`, `POST /institutions/active`, `GET /institutions/districts`). Added coordinate range validation (`-90 <= lat <= 90`, `-180 <= lng <= 180`).
- **Task 2.1 (M-02):** Canonicalized campus coordinates to `(10.95488, 77.95462)` (VSB Engineering College, Karur). Created single source of truth in `frontend/src/constants/institution.js`. Removed divergent literal `10.95485, 77.95463` from `RoutesAndMap.jsx`, `OfficeDashboard.jsx`, and `StudentView.jsx`. Updated `LeafletMap.jsx` default center and `App.jsx` default institution.
- **Testing:** Created `backend/app/tests/test_sprint2_institution_persistence.py` covering persistence across separate DB sessions, seeder idempotency, active switching, canonical coordinates, and validation.

**Modified files:**
- `backend/app/models/institution.py` (New model & seed helper)
- `backend/app/models/__init__.py` (Model registration)
- `backend/app/main.py` (Startup seeder)
- `backend/app/api/routes_institution.py` (DB-backed endpoints)
- `backend/app/tests/test_sprint2_institution_persistence.py` (New 6 focused tests)
- `frontend/src/constants/institution.js` (New canonical coordinates & default institution)
- `frontend/src/App.jsx`
- `frontend/src/components/LeafletMap.jsx`
- `frontend/src/pages/office/RoutesAndMap.jsx`
- `frontend/src/views/OfficeDashboard.jsx`
- `frontend/src/views/StudentView.jsx`
- Docs: `docs/remediation/SPRINT_STATUS.md`, `docs/remediation/DEFECT_REGISTER.md`, `docs/remediation/DECISIONS.md`, `docs/remediation/SPRINTS/SPRINT-02.md`

**Verification results:**
- Focused Tests: `py -3.12 -m pytest backend/app/tests/test_sprint2_institution_persistence.py backend/app/tests/test_sprint8_institution_and_roads.py` PASSED (11 passed, 0 failed in 0.82s).
- Full Regression: `py -3.12 -m pytest backend/app/tests/` PASSED (58 passed, 0 failed in 51.62s).
- Frontend Lint: `npm run lint` PASSED (0 errors).
- Frontend Build: `npm run build` PASSED (0 errors in 1.30s).
- Coordinate audit: 0 conflicting `10.95485` or `77.95463` literals remain in repository.

**Outstanding defects from this task:** None.
**Next task for next session:** Sprint-2 Task 2.4 — Fix `total_seats_deployed` in `routes_workflow.py:120` to use `sum(b.seats for b in active_buses)` (DATA-002).

---

## Handoff Note — Sprint-2 Task 2.4 — 2026-10-27

**Completed tasks:**
- **Task 2.4 (DATA-002):** Replaced flawed calculation `len(manifest) * capacity` in [backend/app/api/routes_workflow.py](file:///d:/PROJECTS/BUSify/backend/app/api/routes_workflow.py) with authoritative database query summing `Bus.seats` across all active buses (`Bus.is_active == True`). De-duplicated by `bus_id` to prevent multi-reference double counting. Returns 0 and 0.0% utilization if active fleet is empty.
- **Testing:** Created [backend/app/tests/test_sprint2_seats_deployed.py](file:///d:/PROJECTS/BUSify/backend/app/tests/test_sprint2_seats_deployed.py) with 5 regression tests covering mixed bus capacities, exclusion of inactive buses, empty fleet handling, manifest length independence, and API response contract compatibility.

**Modified files:**
- `backend/app/api/routes_workflow.py` (authoritative `total_seats_deployed` computation)
- `backend/app/tests/test_sprint2_seats_deployed.py` (New 5 focused tests)
- `docs/remediation/DEFECT_REGISTER.md` (DATA-002 moved to DONE)
- `docs/remediation/SPRINTS/SPRINT-02.md` (Task 2.4 marked COMPLETED)
- `docs/remediation/SPRINT_STATUS.md` (Task 2.4 updated)

**Verification results:**
- Focused Tests: `py -3.12 -m pytest backend/app/tests/test_sprint2_seats_deployed.py` PASSED (5 passed, 0 failed in 30.71s).
- Full Regression Suite: `py -3.12 -m pytest backend/app/tests/ -v --tb=short` PASSED (65 passed, 0 failed in 84.60s).
- Code Hygiene: `git diff --check` PASSED (clean, 0 whitespace errors).

**Outstanding defects from this task:** None.
**Next task for next session:** Sprint-2 Task 2.5 — Define seating equity metric explicitly; compute per-area utilization variance; expose it from the API (DATA-003). Follow `docs/remediation/SPRINTS/SPRINT-02.md`.

---

## Handoff Note — Sprint-2 Task 2.5 — 2026-10-27

**Completed tasks:**
- **Task 2.5 (DATA-003):** Defined seating equity metric and implemented area-level utilization variance computation in `backend/app/core/allocation/equity.py`. Calculated population variance $\sigma^2$, standard deviation $\sigma$, coefficient of variation $CV = \sigma / \bar{u}$, and seating equity percentage $\max(0.0, 1.0 - CV) \times 100.0$ across active transit areas with positive allocated capacity.
- **Workflow API Integration:** Integrated `compute_seating_equity` into `get_operational_manifest` in `backend/app/api/routes_workflow.py`. Exposed `seating_equity_pct`, `area_utilization_variance`, and `per_area_utilization_pct` in API response payload.
- **Frontend Subtitle Correction:** Replaced misleading hardcoded `"100% seating equity achieved"` in `frontend/src/pages/office/OfficeOverview.jsx` and `frontend/src/views/OfficeDashboard.jsx` with computed `${manifestData.seating_equity_pct}% seating equity achieved`.
- **Testing:** Added 7 focused tests in `backend/app/tests/test_sprint2_seating_equity.py` covering known utilization variance, zero-variance on equal load, empty/single-area handling, zero-capacity safety, demand asymmetry, manifest API field validation, and dynamic scenario recalibration.

**Modified files:**
- `backend/app/core/allocation/equity.py` (New seating equity computation module)
- `backend/app/core/allocation/__init__.py` (Export `compute_seating_equity`)
- `backend/app/api/routes_workflow.py` (Integrated area equity into operational manifest endpoint)
- `backend/app/tests/test_sprint2_seating_equity.py` (New 7 focused tests)
- `frontend/src/pages/office/OfficeOverview.jsx` (Dynamic seating equity subtitle)
- `frontend/src/views/OfficeDashboard.jsx` (Dynamic seating equity subtitle)
- `docs/remediation/DEFECT_REGISTER.md` (DATA-003 moved to DONE)
- `docs/remediation/SPRINTS/SPRINT-02.md` (Task 2.5 marked COMPLETED)
- `docs/remediation/SPRINT_STATUS.md` (Task 2.5 updated)
- `docs/remediation/DECISIONS.md` (Added ADR-012)

**Verification results:**
- Focused Tests: `py -3.12 -m pytest backend/app/tests/test_sprint2_seating_equity.py -v` PASSED (10 passed in 17.19s).
- Full Regression Suite: `py -3.12 -m pytest backend/app/tests/ -v --tb=short` PASSED (75 passed in 114.94s).
- Frontend Lint: `npm run lint` PASSED (0 errors).
- Frontend Build: `npm run build` PASSED (0 errors in 1.07s).
- Code Hygiene: `git diff --check` PASSED.

**Outstanding defects from this task:** None.
**Next task for next session:** Sprint-2 Task 2.6 — Disaggregator zero-division guard in `disaggregator.py:108` (DATA-004 / H-11). Follow `docs/remediation/SPRINTS/SPRINT-02.md`.

---

## Handoff Note — Sprint-2 Task 2.6 — 2026-10-27

**Completed tasks:**
- **Task 2.6 (DATA-004 / H-11):** Corrected zero-division, empty-area, and zero-registration failure modes in `backend/app/core/forecasting/disaggregator.py`. In `get_stop_weights_for_area()`, safely returned empty list for empty dataframes and assigned weights `0.0` when total area registrations equal 0 (eliminating arbitrary uniform demand fabrication). In `disaggregate_area_demand()`, guarded against empty stop collections (422), negative demand (422), and zero registrations with positive demand (422) since missing registrations cannot justify an empirical distribution. Safely conserved zero demand ($0=0$) when demand is zero. See ADR-013.
- **Routing API Integration:** Verified that `GET /api/routes?area_id=...` returns HTTP 422 with a descriptive error when queried for an area with no stop records in the database.
- **Testing:** Added 9 focused unit and API tests in `backend/app/tests/test_sprint2_disaggregator.py` covering normal demand disaggregation, empty areas (422), zero demand conservation, zero-registration rejection of positive demand (422), zero-demand zero-registration conservation, multi-area isolation, negative demand validation (422), deterministic output, and HTTP endpoint contract compliance.

**Modified files:**
- `backend/app/core/forecasting/disaggregator.py` (Zero-division guard, empty stop validation, and zero-registration policy)
- `backend/app/tests/test_sprint2_disaggregator.py` (9 focused tests)
- `docs/remediation/DEFECT_REGISTER.md` (DATA-004 moved to DONE)
- `docs/remediation/SPRINTS/SPRINT-02.md` (Task 2.6 marked COMPLETED)
- `docs/remediation/SPRINT_STATUS.md` (Task 2.6 updated)
- `docs/remediation/DECISIONS.md` (ADR-013 added)

**Verification results:**
- Focused Tests: `py -3.12 -m pytest backend/app/tests/test_sprint2_disaggregator.py -v` PASSED (9 passed in 3.31s).
- Full Regression Suite: `py -3.12 -m pytest backend/app/tests/ -v --tb=short` PASSED (84 passed, 0 failed in 85.36s).
- Frontend Lint: `npm run lint` PASSED (0 errors, 13 pre-existing warnings).
- Code Hygiene: `git diff --check` PASSED.

**Outstanding defects from this task:** None.
**Next task for next session:** Sprint-2 Task 2.7 — Fix demand/capacity bar chart empty and loading state in `DailyPlanning.jsx` (M-15). Follow `docs/remediation/SPRINTS/SPRINT-02.md`.

---

## Handoff Note — Sprint-2 Task 2.7 — 2026-10-27

**Completed tasks:**
- **Task 2.7 (M-15):** `DailyPlanning` now renders a labelled loading skeleton while comparison data is loading and a clear empty-state message when no forecast data exists for the selected date and scenario. Its allocation table also explains when no corridor rows are available.
- **Data integrity:** `comparisonChartData` now requires forecast-area data and no longer invents demand from allocated buses when the forecast response is absent.

**Modified files:**
- `frontend/src/pages/office/DailyPlanning.jsx`
- `frontend/src/layouts/OfficeLayout.jsx`
- `docs/remediation/DEFECT_REGISTER.md`
- `docs/remediation/SPRINTS/SPRINT-02.md`
- `docs/remediation/SPRINT_STATUS.md`

**Verification results:**
- Frontend Lint: `npm run lint` PASSED (0 errors; 13 pre-existing warnings).
- Frontend Build: `npm run build` PASSED (0 errors in 14.37s).
- Code Hygiene: `git diff --check` PASSED.
- Backend Regression: PASSED — Python 3.12 (`C:\Users\SUDHAN D\AppData\Local\Programs\Python\Python312\python.exe -m pytest backend/app/tests/ -v --tb=short`) passed with 84 passed, 0 failed in 95.57s.

**Outstanding defects from this sprint:** None.
**Next task:** Sprint-3 Task 3.1 — Guided 4-step daily planning flow, constraints display, and baseline consolidation (ALLOC-001, ALLOC-004, M-03, M-04). Follow `docs/remediation/SPRINTS/SPRINT-03.md`.

---

## Sprint-3 Detail

**Objective:** Transform Daily Planning into a guided 4-step workflow (Date+Scenario → Solver Constraints → Allocation & Equity Review → Confirmation). Clarify benchmark routing heuristics (`M-03`).

**Status:** DONE (Task 3.1-3.3 complete and verified; 87 backend regression tests passed in 93.31s).

**Key tasks:**
1. [x] Document heuristic benchmark in `routes_workflow.py:600-605` (`M-03`).
2. [x] Refactor `DailyPlanning.jsx` into a guided 4-step workflow:
   - Step 1: Date & Scenario Calibration.
   - Step 2: Solver Constraints & Fleet Boundaries (K=50, >=2 min coverage, standing penalty 10x, 55 seats/bus).
   - Step 3: Comparative Capacity & Equity Review (Chart, summary metrics, corridor table).
   - Step 4: Confirmation & Handoff to Dispatch Manifest (`/office/manifest`).
3. [x] Verified zero lint errors and clean Vite production build.

---

## Handoff Note — Sprint-3 — 2026-10-27

**Completed tasks:**
- **Task 3.1 (M-03):** Clarified CSV benchmark route computation as an angular polar-sweep clustering heuristic for fast upload feedback vs. full CVRP MIP in `backend/app/api/routes_workflow.py:600-605`.
- **Task 3.2 (Daily Planning 4-Step Stepper):** Restructured `frontend/src/pages/office/DailyPlanning.jsx` into a 4-step guided workflow with persistent step indicator, solver policy bounds explanation, comparative capacity charts, seating equity metrics, and 1-click handoff to `/office/manifest`.
- **Verification:** Ran `oxlint` (0 errors), `vite build` (clean in 1.02s), and full backend pytest suite (87 passed, 0 failed in 93.31s).

**Modified files:**
- `backend/app/api/routes_workflow.py`
- `frontend/src/pages/office/DailyPlanning.jsx`
- `docs/remediation/SPRINTS/SPRINT-03.md`
- `docs/remediation/DEFECT_REGISTER.md`
- `docs/remediation/SPRINT_STATUS.md`

**Verification results:**
- Frontend Lint: `npm run lint` PASSED (0 errors, 13 pre-existing warnings in other files).
- Frontend Build: `npm run build` PASSED (0 errors in 1.02s).
- Backend Regression: PASSED — Python 3.12 (`pytest backend/app/tests/ -v --tb=short`) passed with 87 passed, 0 failed in 93.31s.
- Code Hygiene: `git diff --check` PASSED.

**Outstanding defects from this sprint:** None.
**Next task:** Sprint-4 Task 4.1 — Dispatch Manifest: real buses and drivers from DB, pagination for >10 rows (M-09), approval guard & Plan model persistence (M-13). Follow `docs/remediation/SPRINTS/SPRINT-04.md`.
