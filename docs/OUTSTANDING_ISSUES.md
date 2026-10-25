# BUSify — Outstanding Defects & Work Backlog

**Purpose:** single source of truth for *unresolved* bugs, correctness risks and
infrastructure problems. Written to survive context loss — an agent picking this
repo up cold should read this file first, then `docs/FAILURES_AND_IMPROVEMENTS.md`
(historical, all-resolved dev incidents) for background.

**Last updated:** 2026-10-13 (auth + status + gitignore batch landed)
**Repo root:** `D:/PROJECTS/BUSify`

---

## How to use this file

1. Read §1 (Environment) before running anything — there are traps.
2. Read §2 (Already Fixed) so you don't revert or duplicate completed work.
3. Pick work from §3 onward. **Do not start a new numbered item without appending it here.**
4. When you finish an item, move it to §2 with what you changed and how you verified it.
5. Keep the status markers accurate. An item marked `DONE` but never verified is worse than one marked `OPEN`.

### Status legend
| Marker | Meaning |
| :--- | :--- |
| `OPEN` | Not started |
| `IN-PROGRESS` | Being worked on — add a note with who/what |
| `BLOCKED` | Needs a decision or external input |
| `DONE` | Fixed **and** verified. Verification method recorded in §2. |

### Severity
| Level | Meaning |
| :--- | :--- |
| **C** | Data corruption, security exposure, or silently wrong operational numbers |
| **H** | Feature broken, or a whole class of bugs is uncaught |
| **M** | Correctness/UX/maintainability debt |
| **L** | Cleanup |

---

## 1. Environment — read before running anything

| Fact | Detail |
| :--- | :--- |
| **Target Python** | 3.12 (README, Dockerfiles, pinned `requirements.txt`) |
| **Local Python** | **3.10.11** — no venv exists in the repo. Installing the pinned stack may fail on 3.10. |
| **Backend deps not installed** | `pandas`, `numpy`, `lightgbm`, `ortools`, `pytest`, `jwt` all missing globally |
| **Frontend deps installed** | `frontend/node_modules` **is** populated. `npm run lint` and `npm run build` both work. |
| **Linter** | `oxlint` — more rules active than `.oxlintrc.json` suggests; reports 27 pre-existing warnings, 0 errors. |
| **Build** | `npm run build` succeeds (~11s, 2585 modules). Rewrites `frontend/dist/` with a new content hash. |
| **OSRM** | Not running locally. `ENABLE_OFFLINE_HAVERSINE_FALLBACK=False` is the default. |

### Traps
- **`backend/requirements.txt` is incomplete.** It omits `PyJWT`, `python-multipart` and `gunicorn`, all of which are imported by the app. The README quickstart tells you to install *this* file, so a fresh clone cannot start. The pinned root `requirements.txt` is complete — Docker uses it. Fix by consolidating to one file (see **M-08**).
- **Two divergent requirements files.** Root `requirements.txt` is pinned (`==`), `backend/requirements.txt` is unpinned (`>=`) and incomplete. Always confirm which one you installed.
- **`frontend/Dockerfile` builds `VITE_API_BASE_URL`; `services/api.js:3` reads `VITE_API_URL`.** The build arg never reaches the client. See **M-07**.
- **`.env` contains real secrets** (`JWT_SECRET`, `ADMIN_PASSWORD`, `TRANSPORT_OFFICER_PASSWORD`, `STUDENT_HASH_SALT`) and there is **no root `.gitignore`** (see **C-11**).
- Several files contain **mojibake** (literal U+FFFD characters where an em-dash belongs): `docs/*.md`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `osrm-setup.sh`, `models/student_attendance.py`.

---

## 2. Already Fixed (do not revert)

### 2.1 Forecasting pipeline — `core/forecasting/lightgbm_model.py`, `feature_pipeline.py`

**Was:** `prepare_data()` re-ran a full SQL aggregate + feature build + `LabelEncoder.fit_transform()` on *every* prediction (5–6× per request, 35× for a 7-day backtest). Inference lags were read from the last *training* row, so all future dates produced a byte-identical feature vector. `lag_7` was fed `lag_1` (t−2) while training used `shift(5)`. `is_holiday` was hardcoded `0`.

**Now:** raw/feature/history/calendar caches loaded once; encoder fitted only in `train_and_evaluate()`; `_lag_features()` rebuilds lag/rolling columns relative to the target date via `np.searchsorted`; holiday flags resolved from a cached calendar lookup.

**Verified:** a pure-Python replication of pandas `shift`/`rolling(min_periods=1)` was compared against the new inference formula across **1,485 series positions — 0 mismatches**. Constants `LAG_WEEKLY_OFFSET / ROLLING_SHORT_WINDOW / ROLLING_LONG_WINDOW` are shared by both paths and must be changed together.

### 2.2 Target leakage — `feature_pipeline.py`
**Was:** `bfill()` on `lag_1`, `lag_7`, `rolling_7_mean`, `rolling_14_mean` injected *future* observations into the earliest training rows.
**Now:** single `dropna()` on those columns (drops 5 rows/area, ~50 of ~450). Split still yields ~245 train / ~50 test.

### 2.3 OSRM distance matrix — `core/routing/matrix_service.py`
**Was:** `except Exception: pass` silently substituted straight-line distances whenever OSRM failed, while the map still drew real roads — routes that looked correct but weren't the routes optimised. Also: live OSRM was *skipped entirely* when `ENABLE_OFFLINE_HAVERSINE_FALLBACK=True` (inverted), hardcoded `timeout=2.5`, bare `requests.get` with no retry, unbounded cache.
**Now:** OSRM always attempted; every failure mode logged with its specific cause; fallback applied only per the documented policy, otherwise `RuntimeError`; timeout from `settings`; pooled retry session matching `road_geometry_service`; cache capped at 64 entries with FIFO eviction.

> ### ⚠ Deliberate behaviour change — review before reverting
> `/workflow/operational-manifest` uses `include_road_geometry=False`, so it previously survived an OSRM outage by producing straight-line-derived distances. **It will now return HTTP 500 when OSRM is down and the fallback flag is False.**
> Justification: `ENABLE_OFFLINE_HAVERSINE_FALLBACK=False` is documented as "OSRM is mandatory", and `road_geometry_service` already hard-fails on the same outage, so this adds no *new* class of failure for geometry-enabled paths — it just surfaces the true cause earlier.
> **If this outage behaviour is unacceptable, it needs an explicit per-endpoint policy flag. Do not "fix" it by restoring the silent `except`.**

### 2.4 Test change — `tests/test_sprint6_edge_cases.py`
Split `test_distance_matrix_metric_properties` into:
- `test_haversine_matrix_physical_invariants` — deterministic, offline, always runs.
- `test_distance_matrix_metric_properties` — original, now `pytest.skip`s when OSRM is genuinely unreachable.

Flagged deliberately: a test was modified to accommodate a behaviour change.

### 2.5 `area_id` validation — `api/routes_buses.py`, `api/routes_crowding.py`
**Was:** `add_bus` accepted any `default_area_id`; `/crowding` fed it to `LabelEncoder.transform` → unhandled 500.
**Now:** `_validate_area_id()` rejects unknown areas at the write boundary (422); `/crowding` guards at the read boundary for buses seeded before validation existed.

### 2.6 Schedule times — `core/schedule_utils.py` (new), `core/routing/vrp_solver.py`, `api/routes_workflow.py`, `config.py`
**Was:** `f"{first_pickup} AM"` appended to already-24-hour strings → `"16:30 AM"` / `"1612:07 AM"`. Backward scheduling subtracted real OSRM durations with no floor. The CVRP fallback emitted `f"08:{5 + i * 5:02d}"` → **invalid `"08:65"` for routes with 12+ stops**.
**Now:** `format_12h` / `format_24h` are the only place AM/PM is ever appended (unit-tested, handles `16:30 → "04:30 PM"`, midnight → `"12:12 AM"`, garbage → `"--:--"`); backward scheduling clamps at `settings.EARLIEST_ROUTE_DEPARTURE` (default `05:00`) and sets `schedule_feasible: false`; fallback walk-forward uses real `timedelta` arithmetic. Manifest now emits both `departure_time` (12h) and `departure_time_24h`, plus `bus_capacity`, `surge_multiplier`, `total_fleet_churn`.

**Fabricated defaults removed** from the manifest (`allocated_riders: 48`, `utilization_pct: 87.2`, `total_distance_km: 22.4`) — they were surfacing as real operational data. Now `0`/`0.0`.

### 2.7 Student pickup schedule — `api/routes_workflow.py`
**Was:** `pickup_minutes = int(35 + sequence_order * 4.5)` from 07:00 — **completely disconnected from distance**.
**Now:** derived from corridor distance at `settings.AVERAGE_BUS_SPEED_KMH`, scheduled backwards from `FIRST_CLASS_ARRIVAL_TIME`, clamped at `EARLIEST_ROUTE_DEPARTURE`, with `schedule_feasible` exposed.

**Verified** (note the correction — see §4.1): implied travel speed for the 11 stops in `AREA_B`, threshold 60 km/h:

| seq | dist_km | OLD pickup | OLD implied km/h | NEW pickup | NEW implied km/h |
| ---: | ---: | :--- | ---: | :--- | ---: |
| 8 | 22.1 | 08:11 | 70 | 07:51 | 34 |
| 9 | 24.3 | 08:15 | 97 | 07:47 | 34 |
| 10 | 26.5 | 08:20 | 159 | 07:43 | 34 |
| 11 | 28.7 | 08:24 | **287** | 07:39 | 34 |

**OLD: 4/11 stops physically impossible. NEW: 0/11.**

### 2.8 Institution field contract — `services/api.js`, `App.jsx`, `components/Navbar.jsx`
**Was (three separate bugs):**
| Direction | Symptom |
| :--- | :--- |
| Write | Navbar sent `short_name`/`fleet_size`/`bus_capacity`; Pydantic silently dropped all three → **every campus created with defaults 45 buses / 55 seats regardless of user input** |
| Read | UI read `short_name`/`fleet_size`; backend emitted `campus_code`/`total_fleet_size` → `Navbar.jsx:145` always showed "8 Buses", `LeafletMap.jsx:451` always "10" |
| Create response | `createInstitution` returned the wrapper `{success, message, institution}`; App stored *the wrapper* → `created.id` was `undefined` → `key={undefined}`, blank name, and `campus_lat` fell back so the map never moved |

**Now:** `normalizeInstitution()` maps backend→UI names once in the API layer; `toInstitutionCreatePayload()` maps UI→backend names before POST and unwraps `.institution`; `handleCreateInstitution` no longer fabricates an `INST_${Date.now()}` object on failure (it re-throws so Navbar's existing `catch` shows the error); `handleSelectInstitution` prefers the server's response. Navbar's `parseInt(...) || 8` replaced with `toIntOrUndefined()` so the backend default applies instead of forcing a fleet of 8.

**Verified:** a script cross-checked `InstitutionCreateRequest`'s accepted fields, the registry's emitted keys, Navbar's payload, and the mapped payload — **zero unmapped keys**. Confirmed by `npm run lint` (0 errors) and `npm run build` (success).

**Verified:** a script cross-checked `InstitutionCreateRequest`'s accepted fields, the registry's emitted keys, Navbar's payload, and the mapped payload — **zero unmapped keys**. Confirmed by `npm run lint` (0 errors) and `npm run build` (success).

### 2.9 Authentication — backend gates + frontend session (`C-01a`, `C-03`)

**Backend — state-changing routes now require an officer/admin token:**
| Route | Gate |
| :--- | :--- |
| `POST /api/institutions` | `require_admin` |
| `POST /api/institutions/active` | `require_admin` |
| `POST /api/workflow/upload-stops-csv` | `require_admin` |
| `POST/PUT/DELETE /api/buses` | `require_admin` (already had it) |

**Deliberately left ungated:** `POST /workflow/student-opt-out` (student-scoped — `require_admin` would be the wrong control; see remaining `C-01a`) and `POST /simulate` (does not mutate; it is a resource problem, not an authorisation one — see `C-05b`).

`TokenResponse` now returns `role` and `name` so the client never has to decode the JWT payload itself.

**Frontend (new):**
- `services/auth.js` — token in **`sessionStorage`, never `localStorage`** (an 8h token must not outlive the tab or be readable by injected script), plus `describeError()` for uniform error rendering.
- `services/api.js` — request interceptor attaches `Authorization: Bearer`; response interceptor tears down the session and notifies the app on **401**.
- `components/LoginModal.jsx` — labelled inputs, `role="dialog"`, `aria-modal`, Escape, error alert.
- `constants/status.js` — see 2.10.
- Gated call sites: `handleSaveBus`, `handleDeleteBus`, `handleUploadCsv`, `handleSelectInstitution`, `handleCreateInstitution`.
- Reads and the student commuter view remain public by design — the app is not gated behind login.

**Ordering note:** the frontend auth landed *before* the backend gates, deliberately. Gating first would have broken campus registration, CSV import and bus CRUD for users with no way to sign in.

**Verified:** `npm run lint` → **0 errors**; `npm run build` → success (new bundle hash, auth code confirmed present). A static cross-check confirmed: 6/6 mutating routes gated, only the 2 deliberate exceptions ungated, `backend require_admin` roles `['admin','transport_officer']` == frontend `ADMIN_ROLES`, interceptors present, token in `sessionStorage` with **zero `localStorage.*Item` calls anywhere in `src`**, and all 5 privileged handlers session-gated.

### 2.10 Honest backend status (`C-05`, `C-06`)

**Was:** the health `catch` set `'HEALTHY'`, and the footer dot was hardcoded green. A dead backend rendered as green "Dispatch Active" on a dispatch console — the worst possible direction for an operator. Navbar separately collapsed `DEGRADED` and `OFFLINE` into one "Connecting" label.

**Now:** `constants/status.js` is the single source of truth for `CHECKING | HEALTHY | DEGRADED | OFFLINE` → colour + label, used by both Navbar and the footer. Catch sets `OFFLINE`. `DEGRADED` (backend up, DB down) is distinguishable from `OFFLINE`.

### 2.11 Root `.gitignore` (`C-08`)

Covers `.env` (4 live secrets), `osrm_data/` (2–3 GB), `data/seed/`, Python caches, editors, logs. `frontend/.gitignore` already covered `node_modules/` + `dist/`.

**`busify.db` is intentionally NOT ignored** — `backend/Dockerfile` does `COPY busify.db ./data/busify.db`, so ignoring it silently breaks the Docker build. Shipping a binary DB in the image is still the wrong design (it should be Alembic migrations + a seed command); recorded as `M-24` rather than breaking the build without saying so.

### 2.12 Test auth fixture — `tests/conftest.py` (new)

`client` and `admin_headers` fixtures. `admin_headers` obtains a real Admin token through `/api/auth/token` rather than minting one, so the login route is exercised too. Updated the 6 affected call sites in `test_sprint7_workflow.py` and `test_sprint8_institution_and_roads.py`, and **added** `test_campus_mutation_requires_officer_auth` asserting 401 on both campus routes unauthenticated (new coverage, not just adaptation).

### 2.13 Student identity scoping (`C-01a`, `C-02`, `C-07`)

**Was:** `GET /workflow/student-profile?roll_no=…` accepted **any string** and synthesised a profile for it — seat, assigned stop, driver name and phone. `POST /workflow/student-opt-out` likewise accepted any roll, so an unauthenticated caller could enumerate the whole 2,200-student body *and* flip any student's travel flag. This directly contradicted the README's privacy guarantee.

**Now:** `DEMO_STUDENT_ROSTER` in `routes_workflow.py` is the single source of truth; `_resolve_known_student()` returns 404 for anything outside it, applied to **both** student endpoints. New `GET /workflow/students` serves the roster so the frontend stops hardcoding it. Profile now includes `student_name`/`student_department`.

**Residual risk — read this before shipping.** This bounds the exposure to a 4-student demo fixture; it does **not** solve student authentication. A real deployment needs per-student credentials or an opaque token issued after login. `driver_phone` is intentionally still exposed: with the roster closed it is a college work contact for a commuter the student already rides with, and removing it would break a legitimate feature. Unchanged residual issues are tracked below.

**Also fixed while in this code path (`C-07`):** `toggleStudentOptOut` now sends `date`, so the navbar date picker is no longer ignored (the toggle used to persist for *today* while the profile was read for the selected day). The response is no longer locally patched with hardcoded `occupancy_pct`/`crowd_level` — the profile is re-read from the server.

**Frontend fixes in the same pass:** roster fetched from the API; `profileError`/`optOutError` rendered instead of `console.error`; request cancellation flag added; missing `activeInstitution` effect dependencies added; fabricated `'BUS-02'` / `'LOW'` / `'55 Seats'` fallbacks replaced with honest placeholders so an API failure cannot render as a valid pass.

**Verified:** `npm run lint` → 0 errors (warnings 26 → 24), `npm run build` → success. Added 3 backend tests: roster endpoint, **unknown roll → 404 on both endpoints**, and every roster entry resolves. Existing tests use `21CS104`, which is in the roster, so they remain valid.

---

## 3. Outstanding — Critical

| ID | Item | Location | Note |
| :--- | :--- | :--- | :--- |
| **C-01a** | **Real student authentication still absent.** `/student-opt-out` is correctly left ungated, but scoping it to a 4-entry demo roster (§2.13) is a mitigation, not authentication. Needs per-student credentials or an opaque session token. | `routes_workflow.py:60` (`DEMO_STUDENT_ROSTER`) |
| **C-02** | Profile endpoint remains **public by design** (a commuter must see their own pass without a login). Blast radius is now the closed roster rather than all 2,200 students, but there is still no proof of *whose* pass is being viewed. Fully closed only by C-01a. | `routes_workflow.py:194` |
| **C-04** | `INSTITUTIONS_REGISTRY` is process-global mutable state | `routes_institution.py:28` | Under the 4 gunicorn workers in `backend/Dockerfile`, `POST /institutions` mutates one worker only; `GET /active` disagrees across workers |
| **C-05b** | `POST /simulate` remains **ungated by decision** | `routes_simulation.py:7` | It does not mutate state, so auth is the wrong control. It is a *resource* problem (unbounded sync CPU) and belongs to H-03's async/rate-limit fix. Gating it would have broken 4 test call sites for no authorisation benefit. |
| **C-07** | `/workflow/student-opt-out` never receives `date`; navbar date picker silently ignored | `services/api.js:136-141` vs `routes_workflow.py:241` | Toggle persists for *today*. Masked by the "latest record" fallback at `routes_workflow.py:183-187` |
| **C-09** | `Base.metadata.create_all()` at **import time** | `main.py:10` | Runs per gunicorn worker and during test collection. Should be a lifespan handler |
| **C-10** | Raw `ALTER TABLE` migration at import | `routes_buses.py:59` | `alembic` is in requirements but unused |
| **C-11** | 897 kB single JS chunk, no code splitting | `frontend/dist/` | recharts+leaflet+react-leaflet in the initial payload for **both** roles even though only one view renders at a time. Add `React.lazy` + `manualChunks`. (`dist/` itself is already ignored via `frontend/.gitignore`.) |
| **C-12** | `L.divIcon({ html })` interpolates values into innerHTML | `LeafletMap.jsx:31-40` | Not currently exploitable (inputs are index/colour only) but a latent XSS sink. No CSP anywhere |

---

## 4. Outstanding — High

| ID | Item | Location |
| :--- | :--- | :--- |
| **H-01** | `loading` state set but **never rendered**; all fetch failures swallowed to `console`; UI falls back to hardcoded `50` buses / `2750` seats / `2150` riders presented as live data | `OfficeDashboard.jsx:29,246,247,311,312,319,320`; `StudentView.jsx:20,152,209`; `LeafletMap.jsx:333-336` |
| **H-02** | No `AbortController` on any effect; 4 untracked `setTimeout`s fire `setState` post-unmount; `LeafletMap.jsx:283` `forEach(async …)` = un-awaited floating promises with no failure caching → refetch storm vs public OSRM demo server | `OfficeDashboard.jsx:58-99,103,191,206`; `StudentView.jsx:24-52,68`; `App.jsx:27-52`; `LeafletMap.jsx:286-312` |
| **H-03** | `/simulate` synchronous, unauthenticated, up to 30 days × 5 areas × forecast + 30 CP-SAT solves at 10 s each, on the event loop | `routes_simulation.py:7` |
| **H-04** | N+1 **serial** OSRM calls in CSV benchmark — one 5 s + 3 retries round-trip per bus | `routes_workflow.py:469,533` |
| **H-05** | Two conflicting baseline allocations: `{10,12,8,12,8}` vs `{10,10,10,10,10}` | `core/simulation/simulator.py:9-15` vs `routes_workflow.py:73` |
| **H-06** | Magic `55` hardcoded ~8× remaining in `parse_and_benchmark_csv`; plus `opt_bus_capacity = 52` with no rationale | `routes_workflow.py:449,475,539,573,582` and `:487` |
| **H-07** | `bus_code` collisions: manifest numbers `BUS-01…` sequentially but `area_bus_mapping` hardcodes `AREA_A→BUS-02`, `AREA_E→BUS-45` — wrong bus whenever the optimizer assigns ≠10 | `routes_workflow.py:93,164-170` |
| **H-08** | Driver roster rotates `(bus_idx-1) % 10` with no constraint — same driver can appear on two routes | `routes_workflow.py:92` |
| **H-09** | `/crowding` runs a full CP-SAT solve just to divide by `buses_in_area`; an area-mean lookup suffices | `routes_crowding.py:58-60` |
| **H-10** | `get_student_profile` does `db.query(Stop).all()` on every request | `routes_workflow.py:157` |
| **H-11** | `disaggregator` divides by zero on an area with no stops; empty list feeds `RoutingIndexManager(1, n, 0)` | `disaggregator.py:26-28` |
| **H-12** | `simulator` denominator wrong: `total_trips += TOTAL_FLEET_SIZE` regardless of actual allocation | `core/simulation/simulator.py:115` |
| **H-13** | `db` injected and never used; unused imports `Bus`/`Registration` | `routes_workflow.py:56,11,13`; `config.py:1`; `database.py:1` |
| **H-14** | `Bus.to_dict` emits reg no `…024` while `add_bus` writes `…026` | `models/bus.py:24` vs `routes_buses.py:84` |
| **H-15** | `stops_list` truncated to 4 but `stop_count` is full length → UI divides riders by full count → `~Infinity` when empty | `routes_workflow.py:116`; `OfficeDashboard.jsx:653` |
| **H-16** | Occupancy overwritten client-side with **wrong** values (`78/74`; server says `78/76`) | `StudentView.jsx:64-65` |
| **H-17** | `step.arrival_time` doesn't exist — solver emits `"time"`; 3 UI sites always show placeholders | `LeafletMap.jsx:358,719,912` (fix `StudentView.jsx:300` is correct) |
| **H-18** | Fields the backend never returns → dead UI branches (`registered_count`, `p90_riders`, `cumulative_passengers`) | `LeafletMap.jsx:726,729,916` |
| **H-19** | 15 form labels with no `htmlFor`/`id`; 4 modals with no `role="dialog"`, focus trap, Escape or scroll lock; **zero `:focus-visible` rules** while inputs strip `outline` | `Navbar.jsx:275-363`; `OfficeDashboard.jsx:1098-1187`; `index.css` |
| **H-20** | Unbounded never-evicting caches, incl. caching *fallback* geometry | `road_geometry_service.py:62` |
| **H-21** | `Plan` model has no writer or reader anywhere — daily dispatch plans computed then discarded | `models/plan.py` |

---

## 5. Outstanding — Medium

| ID | Item | Location |
| :--- | :--- | :--- |
| **M-01** | Zone metadata contradicts itself in **four** places — `LeafletMap.jsx:69-105` vs `:946-958` is the same file contradicting itself | as listed |
| **M-02** | Campus coordinates duplicated 5× and disagreeing (`10.95488,77.95462` vs `10.95485,77.95463`) | `App.jsx:17-18`; `OfficeDashboard.jsx:547`; `StudentView.jsx:271`; `LeafletMap.jsx:26` |
| **M-03** | `parse_and_benchmark_csv` "optimized" isn't optimised — sorts by polar angle + greedy packs; savings come from hand-applied `1.18` vs `1.28` detour factors, i.e. **assumed, not measured** | `routes_workflow.py:489-531` |
| **M-04** | CO₂/fuel constants `2.68` kg/L and `94.5` INR/L hardcoded, uncited; formula doesn't reduce to a documented derivation | `routes_workflow.py:553-554` |
| **M-05** | `backend/Dockerfile` DB path mismatch: `COPY busify.db ./data/busify.db` but `sqlite:///./busify.db` resolves to `/app/busify.db`; compose volume mounts `/app/data` → data lost on rebuild | `backend/Dockerfile` |
| **M-06** | `frontend/Dockerfile` arg mismatch (see §1 Traps) | `frontend/Dockerfile` vs `services/api.js:3` |
| **M-07** | `VITE_API_BASE_URL` never reaches client (same as M-06) | as above |
| **M-08** | Consolidate the two `requirements.txt` files (see §1 Traps) | root + `backend/` |
| **M-09** | Dead weight: `src/App.css` (158 lines, unimported, references non-existent CSS vars), `src/assets/{react.svg,vite.svg,hero.png}`, `public/icons.svg`, inert `tailwind.config.js` (no `@config` directive in `index.css`) | as listed |
| **M-10** | Unused lucide imports (27 warnings); enable `exhaustive-deps`/`no-unused-vars` in `.oxlintrc.json` | 4 files |
| **M-11** | `step.arrival_time` hardcoded `"16:30 PM"` (malformed 12-hour); arrival times hardcoded in prose | `LeafletMap.jsx:652-653`; `StudentView.jsx:263`; `OfficeDashboard.jsx:775` |
| **M-12** | `.slice(0, 10)` silently truncates a ~50-row driver manifest with no "showing 10 of 50" | `OfficeDashboard.jsx:387` |
| **M-13** | `.XLSX` advertised in UI but `accept=".csv,.txt"`; hidden file input unreachable by keyboard | `OfficeDashboard.jsx:720,789` |
| **M-14** | CSV modal auto-fires a heavy CVRP solve on open | `OfficeDashboard.jsx:251` |
| **M-15** | Unused API methods `getAllocation`, `getCrowding`, `getDistricts` | `services/api.js` |
| **M-16** | `SimulateRequest()` mutable default at import | `routes_simulation.py:7` |
| **M-17** | `_preprocess_stops(stops, num_buses)` — `num_buses` never used | `vrp_solver.py:41` |
| **M-18** | `_haversine_route_km(itinerary)` called twice per fallback route | `vrp_solver.py:383-384` |
| **M-19** | Missing prettier/eslint `no-console` policy; raw `alert()` used in 2 places while in-app `<div>` error pattern exists | `OfficeDashboard.jsx:207,222` |
| **M-20** | `metadata "description"`, OG tags and a real `<title>` missing (`<title>frontend</title>`) | `frontend/index.html:7` |
| **M-21** | `downloadTemplateCsv` does DOM side effects inside the API client; no `URL.revokeObjectURL` | `services/api.js` |
| **M-22** | No test coverage for `auth`, `routes_institution`, `road_geometry_service`, `matrix_service` | `backend/app/tests/` |
| **M-23** | `.pulse` class has no `@keyframes`; no `prefers-reduced-motion` handling despite `scroll-behavior: smooth` + Leaflet `flyTo` animations | `index.css` |
| **M-24** | **Binary database shipped in the image.** `backend/Dockerfile` does `COPY busify.db ./data/busify.db`, so the build depends on a tracked `.db`. Correct fix is Alembic migrations + an idempotent seed command. Interacts with `.gitignore` §2.11 (the file is deliberately *not* ignored so the build keeps working until this is resolved). | `backend/Dockerfile`; `requirements.txt` (`alembic` present but unused) |

---

## 6. Outstanding — Low

- `L-01` `index.html` no CSP. `L-02` third-party OSRM demo fetch from browser (`LeafletMap.jsx:297`) - proxy through backend. `L-03` tile URLs hardcoded, map fully broken offline. `L-04` hardcoded student roll as default param (`api.js:129`). `L-05` index used as list `key` in several places. `L-06` naive `datetime.utcnow` (`models/plan.py:13`) alongside tz-aware columns. `L-07` `.oxlintrc.json` enables only 2 rules. `L-08` mojibake (U+FFFD) across several files.

---

## 7. Test risks — expected failures

| Test | Expectation |
| :--- | :--- |
| `tests/test_sprint2_algorithms.py:13` — `assert metrics["wape_improvement_pct"] > 0` | **May now fail.** Removing the `bfill()` leakage changes the measured WAPE, plausibly downward. If it flips negative that is the *correct* measurement, not a regression. The assertion should be revisited, **not** the code. |
| `tests/test_sprint2_algorithms.py:11` — `metrics["lightgbm_p50_wape"] < metrics["baseline_wape"]` | Same exposure. Previously satisfied partly on leaked rows. |
| Any test touching `/routes` or `operational-manifest` without OSRM | Now 500 by design (§2.3). |
| `tests/test_sprint6_edge_cases.py:87` matrix test | Already handled — splits into offline + skippable variants. |

**Backend suite has not been executed since these changes** (no working Python environment yet — see §1). Frontend *was* verified: `npm run lint` 0 errors, `npm run build` success.

---

## 8. Suggested execution order

1. **C-08** root `.gitignore` — trivial, stops secret leakage.
2. **C-01/C-02** auth coverage + scoping `/student-profile`.
3. **H-01/H-05(H-02)** loading & error states — removes fabricated operational numbers.
4. **C-03** frontend auth interceptor — unblocks Bus CRUD.
5. **H-02** cancellation, timers, unmount.
6. **C-04** persist the institution registry.
7. **M-05/M-06/M-08** deployment correctness.
8. **H-19** accessibility (extract one shared `<Modal>`).
9. **M-01/M-02/M-09** de-duplication and dead-code removal.

---

## 9. Corrections to the original audit

Recorded so a future reader doesn't re-learn these:

1. **Student pickup time (§2.7).** The original audit said "pickup times can be *later than* campus arrival". That was imprecise — 08:24 is before 08:30. The actual defect is that the schedule was **disconnected from distance**: it implied 70–287 km/h for 4 of 11 stops. Same fix, correct rationale.
2. **`matrix_service` fallback gate.** The original audit did not spell out that OSRM was skipped entirely when `ENABLE_OFFLINE_HAVERSINE_FALLBACK=True`. That inversion is now fixed (§2.3).
