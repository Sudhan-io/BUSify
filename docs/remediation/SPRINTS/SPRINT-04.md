# Sprint-4 — Dispatch Manifest: Real Bus and Driver Assignment, Pagination, and Plan Approval Guard

**Status:** DONE<br>
**Prerequisite:** Sprint-3 DONE (Daily Planning guided workflow, authoritative baseline).<br>
**Objective:** Transform Dispatch Manifest into a reliable, database-backed dispatch workflow. Source vehicles and drivers from the authoritative database, implement Plan model persistence and approval safeguards (`M-13`, `H-21`), and add manifest table pagination (`M-09`).<br>
**User-visible outcome:** Manifest shows real database buses and drivers, can be paginated without row truncation, and requires authenticated approval that persists to the `plans` table.

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-3 DONE).  
Key defects:
- **M-09**: `manifest` table `.slice(0, 10)` with no pagination label or page controls.
- **M-13 / H-21**: `Plan` model unused (no read, no write path); dispatch lacks database persistence.

---

## Scope

### In scope

1. **Real Bus & Driver Assignment (`routes_workflow.py`)**:
   - Query active fleet from `buses` table (`Bus.is_active == True`).
   - Match routes to eligible buses (home corridor preference, non-duplicate allocation).
   - Use actual driver names, phones, and seat capacities from the database record.
   - Truthfully represent fleet shortages (`UNASSIGNED_INSUFFICIENT_FLEET`) if active buses are fewer than routes.
   - Prevent any physical vehicle from being assigned to more than one route for the same departure slot.
2. **Database-Backed Plan Persistence & Approval Guard (`models/plan.py`, `routes_workflow.py`)**:
   - Add schema columns (`scenario`, `status`, `total_riders`) to `Plan` with idempotent migration.
   - Implement `POST /api/workflow/plan/approve` guarded by `require_admin` (Admin/Transport Officer).
   - Implement server-side validation: reject duplicate bus assignments, inactive vehicles, or incomplete fleet.
   - Atomically persist route records to the `plans` table in a single database transaction.
   - Implement `GET /api/workflow/plan/status` to inspect persisted plan state.
3. **Manifest Pagination & Approval UI (`DispatchManifest.jsx`, `OfficeLayout.jsx`, `api.js`)**:
   - Replace hardcoded `.slice(0, 15)` with full client pagination (10, 25, 50, All).
   - Page controls: item count range, previous/next, active page indicator.
   - Connect "Approve & Dispatch" button to authenticated `api.approvePlan(...)` endpoint.
   - Display real approval state (`DRAFT` vs `APPROVED`).
4. **Verification**:
   - Full regression suite passing (backend + frontend).

### Out of scope

- Direct student pass mutations (Sprint-7).
- Full fleet management CRUD page overhaul (Sprint-5).
- Stop geographic coordinates editing (Sprint-6).

---

## Acceptance Criteria

1. Manifest vehicles and drivers strictly match active rows in the `buses` database table; zero synthetic fallback driver names appear when DB records are present.
2. No active bus is assigned to more than one simultaneous route in a manifest.
3. `POST /api/workflow/plan/approve` rejects unauthenticated callers with HTTP 401/403.
4. Approving a manifest creates persistent `Plan` rows in the database with transaction rollback safety.
5. Repeat approval requests for the same date/slot idempotently update existing plan rows without creating orphaned duplicates.
6. Manifest table allows navigating across all scheduled trips with page size controls and item counts (resolving `M-09`).
7. Full test suite passes without regressions.
