# BUSify Route-Optimization Audit & Fix Plan

## Confirmed Root Causes (Evidence-based)

### R1 — Trip-sheet stops show uniform `~N riders` (hardcoded divide)
**File:** `OfficeDashboard.jsx:681`
```jsx
~{Math.round(selectedTripSheet.allocated_riders / selectedTripSheet.stop_count)} riders
```
Every stop in the trip sheet shows the SAME rider count (total/count). Real stop-level boarding data (`itinerary[].boarded`) is available from the route API but not passed to the manifest. Practical impact: drivers cannot know which stop boards how many.

### R2 — Metric card "Fleet Churn" is fabricated arithmetic
**File:** `OfficeDashboard.jsx:358`
```jsx
value={`${Math.abs((manifestData?.area_allocation?.AREA_A || 10) - 10) * 2} Shifts`}
```
This is `|AREA_A_buses - 10| * 2` — meaningless, hardcodes AREA_A and baseline 10. Should use `manifestData?.churn_adjustments` from the API.

### R3 — "0 Standing" metric card is always hardcoded 0
**File:** `OfficeDashboard.jsx:350`
Always shows `0` regardless of solver result. The API returns `total_predicted_standing_students` via the manifest/allocation.

### R4 — OSRM not running locally — Haversine fallback active but disabled
`ENABLE_OFFLINE_HAVERSINE_FALLBACK=False` but OSRM container is not running → every `/api/routes` call throws `RuntimeError` unless the env var is set True. The tests skip OSRM tests, so this was never caught. Frontend shows a blank map.

### R5 — VRP heuristic fallback uses `sequence_order` field that is `N/A` in disaggregator output
**Fixed in last session** — `disaggregator.py` DOES populate `sequence_order` from DB (confirmed via SQL query `ORDER BY s.sequence_order ASC`). The field arrives correctly. BUT — the heuristic fallback does corridor-order only within a bus's assigned chunk; it doesn't sort stops in the actual itinerary order before building pickup steps. Stops within each bus chunk were pre-sorted by sequence_order on the outer sorted_stops list, but `buses_chunks[b_idx]` preserves insertion order from the FFD packing loop, not geographic order.

### R6 — Evening drop schedule uses fabricated `5 + i*3` minute spacing
**File:** `vrp_solver.py:249`
```python
cur_dt += timedelta(minutes=int(5 + p_idx * 3))
```
Ignores real OSRM duration. 10 stops → last stop gets 5+9*3=32 min cumulative from campus, which could be correct or completely wrong depending on actual distance. Should use `dur_matrix` like morning pickup.

### R7 — No tests for fixture-based synthetic scenarios
Existing tests use live DB (which must be pre-seeded). No isolated, reproducible synthetic fixtures. `tests/fixtures/synthetic/` doesn't exist.

### R8 — `sequence_order` missing in heuristic fallback itinerary
Within each bus chunk assigned by FFD, stops are appended in demand-sorted order (from outer `sorted_stops` list). After the fix, `sorted_stops` is sorted by `sequence_order`, but FFD packing may interleave stops from geographically different parts of the corridor if their demand packs optimally. Need to **re-sort each bus chunk by sequence_order** before building the itinerary.

---

## Priority Plan

| P | Fix | File | Risk | Verifiable By |
|---|-----|------|------|---------------|
| P0 | Enable OSRM fallback in dev `.env` | `.env` | Low | Map renders |
| P1 | Re-sort heuristic bus chunks by `sequence_order` | `vrp_solver.py` | Low | Stop order test |
| P1 | Fix trip-sheet per-stop rider display | `OfficeDashboard.jsx` | Low | UI visual |
| P1 | Fix fabricated churn + standing metrics | `OfficeDashboard.jsx` | Low | UI visual |
| P2 | Fix evening drop to use real dur_matrix | `vrp_solver.py` | Med | Scheduler test |
| P2 | Create `tests/fixtures/synthetic/` suite | New files | Low | pytest pass |
| P3 | Pass stop-level boarding to manifest | `routes_workflow.py` | Med | API + UI test |

---

## Verification Criteria
- `pytest backend/app/tests/ -q` all pass
- Synthetic fixture tests pass offline (no DB, no OSRM)
- `/api/routes?area_id=AREA_A` returns `status=SUCCESS`, stops in ascending `sequence_order`
- Trip sheet shows per-stop real boarding counts
- Map renders route polylines (haversine fallback active in dev)
- "Fleet Churn" and "Standing" metrics non-zero when optimizer reports non-zero
