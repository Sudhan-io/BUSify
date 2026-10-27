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
| Sprint-1 | App shell, navigation, routing | **NOT STARTED** | React Router installed; 7 office tabs navigable; student has 3 sections; existing state logic preserved | Ready to start (Sprint-0 DONE) | — |
| Sprint-2 | Data integrity, institution persistence | **NOT STARTED** | KPI sources canonical; institution DB-persisted; campus coords deduped; chart renders data | Requires Sprint-1 | — |
| Sprint-3 | Daily Planning workflow | **NOT STARTED** | Guided 4-step flow; constraint display; allocation review; no conflicting baselines | Requires Sprint-2 | — |
| Sprint-4 | Dispatch Manifest — real buses, approval guard | **NOT STARTED** | Manifest uses DB buses/drivers; table paginated; dispatch endpoint creates Plan; button disabled without valid manifest | Requires Sprint-3 | — |
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

**Key tasks:**
1. Install `react-router-dom` (verify no version conflict with existing deps).
2. Create route components: `OfficeOverview`, `DailyPlanning`, `RoutesMap`, `DispatchManifest`, `FleetDrivers`, `StudentsAndDemand`, `ReportsHistory`.
3. Move corresponding sections from `OfficeDashboard.jsx` into their route components.
4. Persistent top bar: service date, institution name, backend status indicator.
5. Student view: `MyPass`, `MyRoute`, `TravelStatus` sections.
6. Fix horizontal overflow of zone filter tabs (NAV-004).
7. Ensure `.pulse` CSS has `@keyframes` and `prefers-reduced-motion` (M-14).

**Do NOT change:**
- Backend APIs.
- State logic within sections — just move the JSX.
- Algorithm files.

---

## Sprint-2 Detail

**Objective:** Make every KPI authoritative. Persist institution registry. Canonicalize campus coordinates.

**Key tasks:**
1. Persist `INSTITUTIONS_REGISTRY` to a DB table (SEC-001 / C-04).
2. Canonical campus coordinates: extract to a single constant consumed by all components (M-02).
3. `total_seats_deployed`: use `sum(bus.seats for active buses)` not `len(manifest) * DEFAULT_BUS_CAPACITY` (DATA-002).
4. Define seating equity metric explicitly; compute per-area utilization variance; expose it from the API (DATA-003).
5. Demand/capacity bar chart: render loading and empty states; verify `forecastData` shape matches bar keys.
6. Disaggregator zero-division guard (DATA-004 / H-11).

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
