# BUSify — Architecture Decision Log

**Format:** each entry has an ID, decision, rationale, alternatives considered, consequences, and when it was superseded (if applicable).

---

## ADR-001 — No React Router in initial implementation

**Date:** pre-audit (original codebase)
**Decision:** Use a single `activeRole` state in `App.jsx` to switch between `OfficeDashboard` and `StudentView`. No URL-based routing.
**Rationale (original):** Simpler initial implementation.
**Consequence:** `OfficeDashboard.jsx` accumulated all 8 conceptual officer sections into one 1278-line scroll. Adding navigation now requires extracting sections and installing a router.
**Status:** Superseded by Sprint-1 (add `react-router-dom` and extract sections into route components).

---

## ADR-002 — Institution registry stored in process memory

**Date:** pre-audit (original codebase)
**Decision:** `routes_institution.py:28` stores the campus list in a module-level Python list.
**Rationale (original):** Simpler initial implementation; single-worker dev setup.
**Consequence:** Multi-worker Gunicorn deployment causes divergence — `POST /institutions` mutates one worker, `GET /active` returns stale data from others.
**Status:** Superseded by Sprint-2 (persist to DB table).

---

## ADR-003 — `busify.db` intentionally tracked in git

**Date:** 2026-10-25 (added `.gitignore` entry for `*.db-wal` and `*.db-shm` but kept `busify.db`)
**Decision:** Do not add `busify.db` to `.gitignore`.
**Rationale:** `backend/Dockerfile` does `COPY busify.db ./data/busify.db`. Ignoring the file silently breaks the Docker build.
**Consequence:** Binary database is committed. Contains student attendance rows keyed by HMAC-SHA256 hashes (not raw roll numbers). Review before any public push.
**Alternative considered:** Alembic migrations + seed command. Correct long-term design but blocked by M-24 (Alembic in requirements but unused).
**Status:** Open. Track as M-24. Do not change until migrations are implemented.

---

## ADR-004 — Student enumeration mitigation via DEMO_STUDENT_ROSTER

**Date:** 2026-10-13
**Decision:** Scope `/workflow/student-profile` and `/workflow/student-opt-out` to a 4-entry `DEMO_STUDENT_ROSTER`. Return 404 for any roll outside the roster.
**Rationale:** The previous implementation accepted any string and synthesised a profile, turning the endpoint into an enumeration oracle over 2200 students.
**Consequence:** This is a mitigation, not authentication. The roster is a demo fixture. A production deployment requires per-student credentials or opaque session tokens (C-01a, C-02).
**Status:** Active. Do not remove the roster restriction without implementing real student auth.

---

## ADR-005 — OR-Tools VRP time limit set to 1s per area

**Date:** 2026-10-25
**Decision:** `vrp_solver.py` sets `search_parameters.time_limit.seconds = 1` with `GUIDED_LOCAL_SEARCH`.
**Rationale:** 5 areas × 10s (previous value) = 50s blocking latency on `/operational-manifest`, exceeding the 30s client timeout. At 1s, latency is ~5s for all 5 areas while still finding near-optimal routes for ≤15-node corridors.
**Consequence:** On very large instances (>15 stops per area), the solver may return a good-but-not-optimal route. This is acceptable for the current deployment.
**Status:** Active.

---

## ADR-006 — `POST /simulate` left ungated by auth

**Date:** 2026-10-25
**Decision:** `/simulate` does not require auth.
**Rationale:** It does not mutate state. The correct control is rate-limiting or async execution, not authorization.
**Consequence:** Any caller can saturate backend CPU with a simulation request. Tracked as SEC-003 / H-03.
**Status:** Open. Fix in Sprint-8 via rate-limit or background task queue.

---

## ADR-007 — `client-side-only` dispatch confirmation (pre-Sprint-4)

**Date:** 2026-10-25 (identified; not yet fixed)
**Decision (current):** "Approve & Dispatch" button in `OfficeDashboard.jsx` sets local state only; no server call.
**Defect:** DISPATCH-001, DISPATCH-002.
**Required fix (Sprint-4):** Add `POST /api/workflow/dispatch` that validates the manifest, writes a `Plan` record, returns a dispatch ID. Front-end button calls this endpoint and is disabled when no valid manifest exists.
**Status:** Open. Fix in Sprint-4.

---

## ADR-008 — `require_admin` wraps transport_officer and admin roles

**Date:** 2026-10-13
**Decision:** `auth_service.py` defines `require_admin` to accept both `transport_officer` and `admin` roles.
**Rationale:** Transport officers need to manage buses, stops, and dispatch. A separate `require_officer` dependency would be identical in scope for current endpoints.
**Consequence:** If a stricter separation of duties is needed later (e.g., officers cannot delete institutions), split into `require_officer` and `require_admin` at that point.
**Status:** Active. Do not change without reviewing all 6 gated endpoints.

---

## ADR-009 — Haversine fallback disabled by default

**Date:** pre-audit
**Decision:** `ENABLE_OFFLINE_HAVERSINE_FALLBACK = False` in `config.py`.
**Rationale:** Straight-line Haversine produces wrong route polylines. The map draws real roads but the optimizer uses wrong distances. This was identified as a silent correctness failure.
**Consequence:** When OSRM is unreachable, `/operational-manifest` returns HTTP 500. This is intentional — it surfaces the real failure rather than silently producing wrong routes.
**Risk:** OSRM must be running for any endpoint that calls the distance matrix. Tests that call these endpoints must skip when OSRM is absent.
**Status:** Active. Do not re-enable the fallback without an explicit per-endpoint policy.

---

## ADR-010 — React Router DOM installation and OfficeLayout shared context architecture

**Date:** 2026-10-27 (Sprint-1)
**Decision:** Install `react-router-dom@^7.18.4` and implement `OfficeLayout` shell providing shared state to 7 route components via `<Outlet context={officeContext} />`.
**Rationale:** Preserves zero-regression data synchronization across routes without duplicate network fetches or losing in-flight state (e.g. selected timetable scenario, uploaded spreadsheet benchmark, editing bus modal). Enables deep-linking, direct URL navigation, back/forward history, and dynamic `<title>` tags.
**Consequence:** Office destinations (`/office/overview`, `/office/planning`, `/office/routes`, `/office/manifest`, `/office/fleet`, `/office/students`, `/office/reports`) are independently accessible while sharing authoritative state. Unknown paths route to dedicated 404 page.
**Status:** Implemented and verified in Sprint-1.

---

## ADR-011 — Institution Database Persistence and Campus Coordinate Canonicalization

**Date:** 2026-10-27 (Sprint-2, Task 2.1)
**Decision:** Persist institution registries into an `institutions` table using SQLAlchemy ORM `Institution` model. Replace in-memory `INSTITUTIONS_REGISTRY` in `routes_institution.py` with transactional DB operations. Canonicalize campus coordinates across backend and frontend to `(10.95488, 77.95462)` (VSB Engineering College, Karur).
**Rationale:** Resolves SEC-001 (multi-worker Gunicorn state divergence and restart data loss) and M-02 (conflicting coordinate literals `10.95488, 77.95462` vs `10.95485, 77.95463`).
**Consequence:**
- `Institution` table stores institution records with `is_active` boolean and dynamic JSON `corridors`.
- Idempotent `seed_default_institutions(db)` runs on FastAPI startup, ensuring `VSB_KARUR` is populated without duplicates.
- Frontend components (`LeafletMap`, `RoutesAndMap`, `OfficeDashboard`, `StudentView`, `App`) reference canonical `CANONICAL_CAMPUS_COORDINATES` and `DEFAULT_INSTITUTION` from `frontend/src/constants/institution.js`.
- Coordinate validation enforces `-90 <= lat <= 90` and `-180 <= lng <= 180` at API boundary.
**Status:** Implemented and verified in Sprint-2 Task 2.1.

---

## ADR-012 — Seating Equity Metric Definition and Seat-Utilization Consistency Calculation

**Date:** 2026-10-27 (Sprint-2, Task 2.5)
**Decision:** Explicitly define seating equity as seat-utilization consistency derived from area-level utilization variance across active geographic transit corridors (`AREA_A` through `AREA_E`). Compute utilization per area $u_i = \text{allocated\_riders}_i / \text{allocated\_capacity}_i$ for valid areas with capacity $> 0$ and demand $\ge 0$. Compute population variance $\sigma^2 = \frac{1}{N}\sum_{i=1}^N (u_i - \bar{u})^2$, standard deviation $\sigma = \sqrt{\sigma^2}$, coefficient of variation $CV = \sigma / \bar{u}$ (defined only when $\bar{u} > 0$), and consistency percentage $\max(0.0, 1.0 - CV) \times 100.0$. Expose `seating_equity_pct`, `area_utilization_variance`, `per_area_utilization_pct`, and `equity_status` via `GET /api/workflow/operational-manifest`.
**Rationale:** Resolves DATA-003. The frontend previously hardcoded `"100% seating equity achieved"` whenever standing passengers equaled zero, conflating zero standing commuters with equitable seat allocation across corridors.
**Consequence:**
- Replaces misleading "equity achieved" phrase in `OfficeOverview.jsx` and `OfficeDashboard.jsx` with precise `${manifestData.seating_equity_pct}% seat-utilization consistency` (or `"Seat-utilization consistency unavailable"` when undefined).
- When data cannot support meaningful comparison (empty dataset $N=0$, single area $N=1$, or zero demand $\bar{u}=0$ across all areas), metric returns `None` and an explicit `equity_status` (`"UNAVAILABLE"`, `"INSUFFICIENT_AREAS"`, `"ZERO_DEMAND"`) rather than fabricating a reassuring 100% score.
- Multiple-leg route vehicle capacity is deduplicated by bus ID to prevent artificial capacity inflation.
- Equal non-zero utilization across corridors yields $0.0$ variance and $100.0\%$ consistency.
- Zero variance proves equal measured utilization under the defined formula; it does not conflate with unconstrained capacity adequacy or total student satisfaction.
**Status:** Implemented, audited, and verified in Sprint-2 Task 2.5.

---

## ADR-013 — Demand Disaggregation Zero-Registration Fallback and Demand Conservation Policy

**Date:** 2026-10-27 (Sprint-2, Task 2.6 review)
**Decision:** Prohibit arbitrary uniform demand fabrication (`1.0 / len(stops)`) when an area has stops but zero student registrations. When total student registrations for an area are zero:
1. If forecast demand is zero (`area_p50 == 0 and area_p90 == 0`), stop weights are set to `0.0` and disaggregation safely returns stops with `p50_riders = 0` and `p90_riders = 0`. Demand is conserved ($0 = 0$) and genuine zero demand is preserved without division error.
2. If forecast demand is positive (`area_p50 > 0 or area_p90 > 0`), the disaggregator rejects the unresolvable input with `HTTPException(status_code=422, detail=f"Area {area_id} has zero student registrations. Cannot disaggregate positive demand.")`.
**Rationale:** Resolves DATA-004 / H-11 audit. Tracing the codebase back to commit `69ab6ffd5c` showed uniform weighting was an arbitrary math fallback to prevent `ZeroDivisionError`, not an intentional transit domain policy. Distributing positive passenger demand uniformly across stops without student registrations fabricates fictitious passenger densities (identified in `docs/audit_and_plan.md` R1 as misleading bus drivers). When student registration data cannot justify a spatial distribution, the backend must not fabricate one.
**Consequence:**
- Replaces defensive `1.0 / len(df)` with strict domain integrity.
- Preserves valid non-zero proportional weighting and demand conservation across all operational areas (`AREA_A` through `AREA_E`).
- Preserves valid zero-demand operations without raising errors.
- Clearly flags missing or unpopulated student registration data as unprocessable (HTTP 422).
**Status:** Implemented and verified in Sprint-2 Task 2.6 review.
