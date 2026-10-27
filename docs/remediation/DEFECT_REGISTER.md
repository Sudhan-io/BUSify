# BUSify — Defect Register

**Stable IDs.** Move items only when DONE + verified. Add new items at the bottom of each severity block.
**Reference:** `docs/OUTSTANDING_ISSUES.md` for full text and history of already-fixed items.

---

## How to use

1. Pick by severity and sprint dependency.
2. Do not start work without reading the full description in `OUTSTANDING_ISSUES.md`.
3. When done, record exact verification evidence in the Status cell and move to the DONE section.

---

## Severity key

| Level | Meaning |
|:---|:---|
| **CRITICAL** | Data corruption, security exposure, or silently wrong operational numbers |
| **HIGH** | Feature broken or whole class of bugs uncaught |
| **MEDIUM** | Correctness / UX / maintainability debt |
| **LOW** | Cleanup |

---

## Confidence key

| Level | Meaning |
|:---|:---|
| **Confirmed** | Verified by reading code |
| **Probable** | Strongly supported by evidence, not fully verified |
| **Unverified** | Needs a test or deeper investigation |

---

## OPEN — Critical

| ID | Title | Confidence | Affected files | User impact | Fix | Sprint |
| **DISPATCH-001** | "Approve & Dispatch" button has no server-side guard — `handleBroadcast` is client-only | Confirmed | `OfficeDashboard.jsx:110-113`, `routes_workflow.py` (no dispatch endpoint) | Empty or stale manifest can be "dispatched" with no backend validation | Add `POST /api/workflow/dispatch` that validates manifest, creates a `Plan` record, and returns a dispatch ID | Sprint-4 |
| **DISPATCH-002** | `Plan` model has no reader or writer — approved manifests are discarded immediately | Confirmed | `models/plan.py`, zero callers | No audit trail for approved trips | Implement dispatch persistence via `Plan` model | Sprint-4 |
| **SEC-002** | Student authentication absent — `/student-profile` and `/student-opt-out` rely on a 4-entry demo roster only | Confirmed | `routes_workflow.py:60` (DEMO_STUDENT_ROSTER) | Any caller who knows a valid roll number can read that student's pass | Requires per-student credentials or opaque token; demo roster is a mitigation only | Sprint-7 (post-demo) |
| **SEC-003** | `POST /simulate` is ungated, synchronous, runs up to 300 CP-SAT solves on the event loop | Confirmed | `routes_simulation.py:7` | Any caller can saturate the server CPU | Rate-limit or run async; add auth for resource protection | Sprint-8 |

---

## OPEN — High

| ID | Title | Confidence | Affected files | User impact | Fix | Sprint |
|:---|:---|:---|:---|:---|:---|:---|
| **NAV-003** | Student roll-number selector exposed before authentication — enumerable | Confirmed | `StudentView.jsx:120-145` | Any visitor sees all registered commuter names and rolls | Replace selector with direct lookup after student auth | Sprint-7 |
| **MAP-001** | `step.arrival_time` field does not exist — solver emits `time` key; 3 UI branches always show `--:--` | Confirmed | `LeafletMap.jsx:358,719,912` | Route arrival times always blank on map and trip sheet | Use `step.time` not `step.arrival_time` | Sprint-6 |
| **MAP-002** | `registered_count`, `p90_riders`, `cumulative_passengers` fields never returned by backend; dead UI branches | Confirmed | `LeafletMap.jsx:726,729,916` | Stop detail panel shows blank fields | Remove dead branches or add fields to solver output | Sprint-6 |
| **ALLOC-002** | `bus_code` in manifest is sequential `BUS-{n}`, not drawn from `buses` table — wrong bus when allocator assigns ≠10 per area | Confirmed | `routes_workflow.py:93,144` | Driver sheet references non-existent bus IDs | Map manifest rows to actual registered buses | Sprint-4 |
| **ALLOC-003** | Driver roster rotates `(bus_idx-1) % 10` — same driver can appear on two routes | Confirmed | `routes_workflow.py:92` | Two trip sheets show same driver name | Assign from registered driver list without repeats; flag if insufficient drivers | Sprint-4 |
| **DATA-006** | `H-10`: `get_student_profile` runs `db.query(Stop).all()` on every request | Confirmed | `routes_workflow.py:157` | N+1 DB fetch, no caching | Cache stops or use a smarter query | Sprint-7 |
| **DATA-007** | `H-15`: manifest table sliced to 10 rows silently; stop count full vs sliced mismatch | Confirmed | `OfficeDashboard.jsx:410` (`slice(0,10)`) | Officer sees only 10 of ~38 dispatch rows | Add pagination or show-all with count label | Sprint-4 |
| **A11Y-001** | 15 form labels with no `htmlFor/id`, 4 modals with no role/focus-trap/Escape, zero `:focus-visible` | Confirmed | `Navbar.jsx:275-363`, `OfficeDashboard.jsx:1098-1187`, `index.css` | Keyboard-only users cannot operate forms or dismiss modals | Add `htmlFor`, `id`, `role="dialog"`, focus trap, Escape handler | Sprint-8 |
| **STUDENT-001** | Student commuter experience buried at bottom of a long scroll; no distinct navigation | Confirmed | `StudentView.jsx` structure | Student cannot find bus pass quickly | Student view needs clear top-level sections: Pass, Route, Schedule, Status | Sprint-7 |

---

## OPEN — Medium

| ID | Title | Confidence | Affected files | Sprint |
|:---|:---|:---|:---|:---|
| **M-01** | Zone metadata contradicts itself in `LeafletMap.jsx:69-105` vs `:946-958` | Confirmed | `LeafletMap.jsx` | Sprint-6 |
| **M-03** | "Optimized" CSV benchmark is a greedy sort with assumed detour factors, not CVRP | Confirmed | `routes_workflow.py:489-531` | Sprint-3 |
| **M-05** | `backend/Dockerfile` DB path mismatch | Confirmed | `backend/Dockerfile` | Sprint-8 |
| **M-06** | `frontend/Dockerfile` build arg `VITE_API_BASE_URL` never reaches client | Confirmed | `frontend/Dockerfile`, `services/api.js:3` | Sprint-8 |
| **M-07** | Two divergent `requirements.txt` files | Confirmed | root + `backend/` | Sprint-0 |
| **M-09** | `manifest` table `.slice(0,10)` with no pagination label | Confirmed | `OfficeDashboard.jsx:410` | Sprint-4 |
| **M-10** | `.xlsx` advertised in UI but file input only accepts `.csv,.txt` | Confirmed | `OfficeDashboard.jsx:720,789` | Sprint-5 |
| **M-11** | `base.metadata.create_all()` at import time — should be lifespan handler | Confirmed | `main.py:10` | Sprint-8 |
| **M-12** | Raw `ALTER TABLE` migration at import in `routes_buses.py` | Confirmed | `routes_buses.py:59` | Sprint-8 |
| **M-13** | `Plan` model unused (no read, no write path) | Confirmed | `models/plan.py` | Sprint-4 |
| **M-17** | `H-04`: N+1 serial OSRM calls in CSV benchmark (one per bus) | Confirmed | `routes_workflow.py:469,533` | Sprint-5 |

---

## OPEN — Low

| ID | Title | Sprint |
|:---|:---|:---|
| **L-01** | No Content Security Policy | Sprint-8 |
| **L-02** | OSRM tile fetched from browser (should proxy through backend) | Sprint-6 |
| **L-03** | Tile URLs hardcoded; map fully broken offline | Sprint-6 |
| **L-05** | `index` used as list `key` in several places | Sprint-1 |
| **L-06** | `datetime.utcnow` (naive) alongside tz-aware columns | Sprint-8 |
| **L-07** | `.oxlintrc.json` enables only 2 rules | Sprint-8 |
| **L-08** | Mojibake (U+FFFD) across multiple doc files | Sprint-0 |

---

## DONE (do not revert)

See `docs/OUTSTANDING_ISSUES.md` §2 for full descriptions and verification evidence.

| ID | Title | Verified |
|:---|:---|:---|
| ORG-001 (C-08) | Root `.gitignore` | `git status` clean |
| FORE-001 | LightGBM lag/cache/encoder bug | 1485-position replication |
| FORE-002 | Target leakage (bfill) | `dropna` + split sizes confirmed |
| ROUTE-001 | OSRM matrix silent-fail fallback inversion | Code reading |
| BUS-001 (2.5) | `area_id` validation at write boundary | Test coverage |
| TIME-001 (2.6) | Schedule time format bugs (`"08:65"`, AM/PM appended twice) | `format_12h` unit tests |
| STUDENT-002 (2.7) | Pickup time disconnected from distance | 11-stop table, 0 infeasible |
| INST-001 (2.8) | Institution field contract mismatch | Static cross-check, 0 unmapped keys |
| AUTH-001 (2.9) | Backend auth gates + frontend session + LoginModal | Static check; 0 localStorage calls |
| STATUS-001 (2.10) | Hardcoded green health status | Code reading; `constants/status.js` |
| GIT-001 (2.11) | `.gitignore` created | `git status` |
| TEST-001 (2.12) | Auth fixture in conftest | Test suite |
| PRIV-001 (2.13) | Student roster scoped; enumeration closed | Test: unknown roll → 404 |
| DATA-001 | Removed hardcoded `50 buses / 2750 seats / 2150 riders` fallbacks in `OfficeDashboard.jsx`; explicit `—` and loading skeleton rendered | Verified in Sprint-0; 0 grep matches |
| NAV-002 | `loading` state rendered in hero, MetricCards, and StudentView boarding pass; `manifestError` and `busError` inline alerts replace console-only errors | Verified in Sprint-0; lint unused-loading warning resolved |
| M-16 | Replaced `alert()` with inline `busError` alerts in fleet table and bus modal | Verified in Sprint-0; 0 alert() matches |
| L-04 | Page `<title>` updated to "BUSify | Transit Intelligence" and meta description added in `index.html` | Verified in Sprint-0; build succeeds |
| M-08 | Removed unimported `frontend/src/App.css` and inert `frontend/tailwind.config.js` | Verified in Sprint-0/1; build clean |
| NAV-001 | Extracted monolithic office view into 7 distinct route components (`OfficeOverview`, `DailyPlanning`, `RoutesAndMap`, `DispatchManifest`, `FleetAndDrivers`, `StudentsAndDemand`, `ReportsAndHistory`) with `react-router-dom@^7.18.4`, `OfficeLayout`, persistent sub-nav bar, dynamic titles, and 404 handler | Verified in Sprint-1; browser subagent E2E pass |
| NAV-004 | Zone-filter tabs in `RoutesAndMap.jsx` fixed for horizontal overflow with `min-w-0` and safe responsive wrapping | Verified in Sprint-1; no clipping at 1280px in browser subagent |
| M-14 | Added `@keyframes pulse-dot` and `@media (prefers-reduced-motion: reduce)` to `.pulse` class in `frontend/src/index.css` | Verified in Sprint-1; CSS build succeeds |
| SEC-001 (C-04) | `Institution` ORM model persisted to `institutions` DB table, idempotent startup seed, active campus switching, process-global in-memory registry eliminated | Verified in Sprint-2 Task 2.1; 6 unit tests passing across DB sessions + regression suite |
| M-02 | Campus coordinates canonicalized to `(10.95488, 77.95462)` in `backend.app.core.config.settings` and `frontend/src/constants/institution.js`; divergent `(10.95485, 77.95463)` removed | Verified in Sprint-2 Task 2.1; 0 conflicting coordinate matches in repo, tests passing |
| DATA-002 | `total_seats_deployed` in `/api/workflow/operational-manifest` computes sum of seats from database active buses (`Bus.is_active == True`), replacing `len(manifest) * capacity` | Verified in Sprint-2 Task 2.4; 5 focused tests passing + full regression suite (65 passed) |
| DATA-003 | Seating equity defined as `max(0, 1 - CV) * 100` over per-area utilization variance; exposed via `seating_equity_pct`, `area_utilization_variance`, and `per_area_utilization_pct`; UI displays actual equity percentage | Verified in Sprint-2 Task 2.5; 7 focused tests passing + full regression suite (72 passed) |
| DATA-004 (H-11) | `disaggregate_area_demand` guards against empty areas, negative demand, and zero-registration positive demand with HTTPException(422); conserves zero demand without fabricating uniform weights (ADR-013) | Verified in Sprint-2 Task 2.6 review; 9 focused unit tests passing + full regression suite (84 passed) |
| M-15 | Daily Planning demand/capacity chart renders an accessible loading skeleton and an explicit empty state when no comparison data is available | Verified in Sprint-2 Task 2.7: `npm run lint` (0 errors) and `npm run build` passed on 2026-10-27 |
| ALLOC-001 | Consolidate `/api/workflow/operational-manifest` baseline to canonical `BASELINE_ALLOCATION` `{AREA_A: 10, AREA_B: 12, AREA_C: 8, AREA_D: 12, AREA_E: 8}`, matching simulator and allocation optimizer | Verified: manifest unit test in `test_sprint3_api.py` + regression suite pass |
| ALLOC-004 | Replaced hardcoded `55` and `opt_bus_capacity = 52` with `settings.DEFAULT_BUS_CAPACITY` across CSV benchmark calculation | Verified: `test_sprint3_api.py` and regression suite pass |
| DATA-005 (H-12) | Corrected simulator trips denominator to use actual baseline allocation and dynamic allocation sums instead of static fleet size | Verified: `test_sprint2_algorithms.py`, `test_sprint3_api.py`, regression suite pass |
| M-04 | Documented diesel consumption (3.8 km/L), operational days (220/yr), diesel price (₹94.5/L), and carbon intensity (2.68 kg CO2/L) in benchmark savings | Verified: code comments and formulas aligned in `routes_workflow.py` |
