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
| Sprint-0 | Baseline, loading states, dead code removal | **NOT STARTED** | No hardcoded fallback numbers; loading spinner renders; API errors shown inline; dead files removed; environment verified | None | — |
| Sprint-1 | App shell, navigation, routing | **NOT STARTED** | React Router installed; 7 office tabs navigable; student has 3 sections; existing state logic preserved | Requires Sprint-0 | — |
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
- [ ] No hardcoded fallback numbers (`50`, `2750`, `2150`) rendered as operational data.
- [ ] `loading` state in `OfficeDashboard` renders a visible spinner in each card/section.
- [ ] API errors in `OfficeDashboard` render as inline alerts, not console-only.
- [ ] `loading` state in `StudentView` renders correctly.
- [ ] Dead files removed: `src/App.css`, `tailwind.config.js`, unused SVGs.
- [ ] Page `<title>` changed from "frontend" to "BUSify".
- [ ] `alert()` calls in `OfficeDashboard.jsx:207,222` replaced with in-app error UI.
- [ ] Python environment confirmed: list which `requirements.txt` and Python version are used.
- [ ] Baseline test run: record which tests pass, which fail, which are skipped (OSRM absent).

**Verification commands:**
```bash
# Frontend build
cd frontend && npm run build   # must succeed, 0 errors
cd frontend && npm run lint    # 0 errors

# Backend tests (PYTHONPATH must include repo root)
cd d:\PROJECTS\BUSify
$env:PYTHONPATH="."
python -m pytest backend/app/tests/ -v --tb=short 2>&1 | Tee-Object docs/remediation/sprint0_test_results.txt
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

## Handoff Notes

**For Sprint-0 executor:** Read `SPRINT_EXECUTION_GUIDE.md` first, then `SPRINTS/SPRINT-00.md`.  
**Do not begin Sprint-1 until Sprint-0 test results are recorded in this file.**
