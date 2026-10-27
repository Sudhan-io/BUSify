# Sprint-6 — Routes & Map Correctness

**Status:** DONE<br>
**Prerequisite:** Sprint-5 DONE (Fleet, Driver, Student and Demand Management).<br>
**Objective:** Resolve route arrival time field omissions (MAP-001), stop detail and passenger demand metrics (MAP-002), and zone metadata cardinal direction contradictions (M-01).<br>
**User-visible outcome:** Live Dispatch Map and turn-by-turn itinerary drawer display accurate arrival times (e.g., `07:22`) instead of `--:--`; stop popups display registered student counts, p90 demand, and cumulative riders onboard; corridor legend accurately maps zones to their real cardinal directions (Zone A West, Zone B South, Zone C South-East, Zone D North, Zone E North-West).

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-5 DONE), `DEFECT_REGISTER.md`.

Key defects and requirements:
- **MAP-001**: VRP solver emitted `time` key while frontend accessed `step.arrival_time`, causing `--:--` or generic text in 3 UI branches. Standardize solver output and UI to supply and consume both `arrival_time` and `time`.
- **MAP-002**: Stop popups and drawer expected `registered_count`, `p90_riders`, and `cumulative_passengers`. Add rolling cumulative passengers onboard for morning pickup and evening dropoff, and propagate stop statistics into itinerary steps.
- **M-01**: Zone metadata contradicted itself in `LeafletMap.jsx:66-72` vs `ZONE_DESCRIPTIONS:74-110` vs legend `951-965` (e.g. Zone A claimed North in legend and comment, but West in zone description and reality). Align all labels, comments, and institution defaults to canonical cardinal directions.

---

## Scope

### In scope

1. **Routing Solver & Itineraries (`backend/app/core/routing/vrp_solver.py`)**:
   - Emit both `arrival_time` and `time` on all itinerary nodes (`pickup_stop`, `dropoff_stop`, `depot_departure`, `depot_arrival`) for both OR-Tools solution and heuristic fallback routes (MAP-001).
   - Compute rolling `cumulative_passengers` onboard for morning pickup (monotonically non-decreasing from depot out to campus hub) and evening dropoff (monotonically decreasing from campus hub dismissal to outer depot) (MAP-002).
   - Propagate `registered_count` and `p90_riders` from stops into each itinerary step (MAP-002).
2. **Interactive Map Component (`frontend/src/components/LeafletMap.jsx`)**:
   - In `isolatedStopSequenceMap`: populate `time: step.arrival_time || step.time`, `passengers`, `totalOnboard: step.cumulative_passengers`, `registeredCount`, and `p90Demand`.
   - In stop `Popup`: display `student_count` / `registered_count`, `p90_riders` / `p90Demand`, and `totalOnboard` when available without dead branches (MAP-002).
   - In turn-by-turn drawer: show `step.arrival_time || step.time` and riders onboard (MAP-001).
   - In `AREA_COLORS` comments and bottom legend overlay: synchronize cardinal directions with `ZONE_DESCRIPTIONS` (Zone A: West, Zone B: South, Zone C: South-East, Zone D: North, Zone E: North-West) (M-01).
   - Fix React hook dependencies in `MapController` (extract scalar lat/lng) to pass OxLint with 0 warnings.
3. **Institution Corridors (`backend/app/models/institution.py`, `backend/app/api/routes_institution.py`)**:
   - Align `DEFAULT_VSB_CORRIDORS` and `default_corridors` with canonical cardinal directions and bearings (M-01).
   - Migrate existing institution records in `seed_default_institutions()` to adopt canonical corridors.

### Out of scope

- Student authenticated login portal and personalized route view (Sprint-7).
- Docker deployment consolidation and accessibility audit (Sprint-8).

---

## Acceptance Criteria Verification

- [x] **Criterion 1 (MAP-001):** VRP solver emits both `arrival_time` and `time` on all itinerary steps (verified via `test_sprint6_map_and_routes.py`).
- [x] **Criterion 2 (MAP-002):** Itinerary steps contain rolling `cumulative_passengers`, `registered_count`, and `p90_riders` for morning and evening trips (verified).
- [x] **Criterion 3 (M-01):** Zone metadata consistent across `ZONE_DESCRIPTIONS`, `AREA_COLORS`, legend overlay, and database institution corridors (verified).
- [x] **Criterion 4 (Frontend Cleanliness):** OxLint clean with 0 warnings, 0 errors; Vite production build clean in 1.07s (verified).
- [x] **Criterion 5 (Test Suite Pass):** All Sprint 6 tests pass; full backend regression suite passing (verified).
