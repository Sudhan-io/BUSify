# Sprint-7 — Student Commuter Experience

**Status:** DONE<br>
**Prerequisite:** Sprint-6 DONE (Routes & Map Correctness).<br>
**Objective:** Deliver an authentic, structured, and responsive student commuter portal with verified identity access, eliminating commuter enumeration (`NAV-003`, `SEC-002`), removing N+1 stop queries (`DATA-006` / `H-10`), establishing clear modular navigation sections (`STUDENT-001`), and providing honest unapproved vs approved dispatch states.<br>
**User-visible outcome:** Clean, structured Student Commuter Console with dedicated sections (My Bus Pass, My Route, Travel Schedule, Service Status & Support); verified commuter lookup with accessible roll input; digital boarding pass with approved dispatch integration; morning/evening travel schedules; and persistent attendance opt-out/reconfirmation.

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-6 DONE), `DEFECT_REGISTER.md`.

Key defects and requirements:
- **NAV-003 / SEC-002**: Student roll-number selector was exposed on cold load as clickable buttons for all sample students, allowing unauthenticated enumeration. Replace with direct roll verification input while providing a discreet collapsible evaluation roster for testing.
- **DATA-006 (H-10)**: `get_student_profile` executed `db.query(Stop).all()` on every single request. Implement module-level stops caching with invalidation on updates.
- **STUDENT-001**: Student commuter experience was buried in a monolithic scroll view without dedicated sections. Break into distinct navigable tabs: My Bus Pass, My Route, Travel Schedule, and Service Status.
- **Honest Dispatch & Occupancy**: Do not claim guaranteed driver assignments or approved passes without supporting data. Link profile to persisted `Plan` records when available; mark provisional draft state when dispatch has not yet been approved.

---

## Scope

### In scope

1. **Stop Query Caching & Plan Integration (`backend/app/api/routes_workflow.py`)**:
   - Add `_get_all_stops_cached(db)` and `invalidate_stops_cache()` to eliminate redundant DB fetches on student profile calls (`DATA-006`).
   - Query persisted `plans` table for the target travel date; if approved plan exists, consume authoritative vehicle ID, driver info, and stop arrival time.
   - If no approved plan exists, return truthful provisional status (`is_approved_dispatch=False`, `plan_status="PENDING_APPROVAL"`, `service_status="ON_SCHEDULE"` or `"ABSENCE_RECORDED"`).
2. **Student Commuter Console UI (`frontend/src/views/StudentView.jsx`)**:
   - Commuter Identity Verification (`NAV-003`): Accessible roll input with verified student identity badge and collapsible evaluation roster for test ease.
   - Distinct Sub-Navigation Tabs (`STUDENT-001`): `ALL`, `PASS`, `ROUTE`, `SCHEDULE`, `STATUS`.
   - Section 1 (My Bus Pass): Digital ticket with pass ID, academic year, assigned seat, pickup time, driver contact with tel: link, expected occupancy meter, and attendance toggle.
   - Section 2 (My Route): Interactive corridor map and sequential route stop cards with arrival times.
   - Section 3 (Travel Schedule): Morning inbound and evening outbound dismissal (16:30) timetables with academic scenario badges.
   - Section 4 (Service Status): Plan approval state, attendance preference, and emergency transport desk helpline.
3. **Automated Test Coverage**:
   - `backend/app/tests/test_sprint7_student_experience.py`: stops caching, unapproved vs approved dispatch states, enumeration protection, attendance opt-out.
   - Existing regression tests in `test_sprint7_workflow.py`.

### Out of scope

- Production SSO / OAuth2 student portal login (Sprint-8 / post-demo).
- Docker deployment consolidation and accessibility audit (Sprint-8).

---

## Acceptance Criteria Verification

- [x] **Criterion 1 (NAV-003 / SEC-002):** Roll number selector replaced with roll input verification; unknown rolls return 404 (verified).
- [x] **Criterion 2 (DATA-006):** Stop query caching implemented and verified in `test_stops_caching_eliminates_n_plus_one_queries` (verified).
- [x] **Criterion 3 (STUDENT-001):** Modular sub-nav tabs (Pass, Route, Schedule, Status, All) implemented and fully navigable (verified).
- [x] **Criterion 4 (Authoritative Pass Data):** Profile links to approved plans when available, otherwise signals provisional schedule honestly (verified).
- [x] **Criterion 5 (Frontend Quality):** OxLint clean with 0 warnings, 0 errors; Vite production build clean in 1.04s (verified).
- [x] **Criterion 6 (Test Suite):** Dedicated Sprint 7 suite (5 passed) and full regression suite (112 passed, 0 failed in 137.95s) (verified).
