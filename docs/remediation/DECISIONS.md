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
