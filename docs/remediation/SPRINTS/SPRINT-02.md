# Sprint-2 — Data Integrity, Institution Persistence, Metric Canonicalization

**Status:** NOT STARTED  
**Prerequisite:** Sprint-1 DONE (navigation shell exists).  
**Objective:** Every KPI card traces to a single authoritative source. Institutions persist in the database. Campus coordinates have one canonical value. Chart renders data.  
**User-visible outcome:** KPI cards show real numbers from the database, not computed-from-defaults or conflicting values.

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-1 DONE).  
Key defects: SEC-001, DATA-001 (residual), DATA-002, DATA-003, DATA-004, M-02, M-15.

---

## Scope

### In scope

- Persist institution registry to a DB table (SEC-001 / C-04).
- Canonical campus coordinates: extract to one constant, remove duplicates (M-02).
- `total_seats_deployed`: compute from actual bus seats, not `len(manifest) * DEFAULT_BUS_CAPACITY` (DATA-002).
- Seating equity: define metric formally; compute per-area utilization; expose via API (DATA-003).
- Demand/capacity bar chart: fix empty/loading state (M-15).
- Disaggregator zero-division guard (DATA-004 / H-11).

### Out of scope

- Dispatch approval guard (Sprint-4).
- Algorithm changes beyond the zero-division guard.
- Student profile data (Sprint-7).

---

## Ordered Implementation Tasks

### Task 2.1 — Create `institutions` DB table and migration

Create `backend/app/models/institution.py`:
```python
from sqlalchemy import Column, String, Float, Integer
from backend.app.database import Base

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    campus_code = Column(String(32))
    city = Column(String(64))
    district = Column(String(64))
    campus_lat = Column(Float, nullable=False)
    campus_lng = Column(Float, nullable=False)
    total_fleet_size = Column(Integer, default=50)
    default_capacity = Column(Integer, default=55)
    is_active = Column(Integer, default=0)  # boolean
```

Register the model in `backend/app/models/__init__.py`. `Base.metadata.create_all` will create the table on startup.

---

### Task 2.2 — Migrate `routes_institution.py` to use the DB

Replace the in-memory `INSTITUTIONS_REGISTRY` list with DB queries.  
`GET /institutions` → `db.query(Institution).all()`.  
`POST /institutions` → insert new `Institution` record.  
`GET /institutions/active` → `db.query(Institution).filter(Institution.is_active == 1).first()`.  
`POST /institutions/active` → `UPDATE Institution SET is_active = 0` then `UPDATE Institution SET is_active = 1 WHERE id = ...`.

Seed the existing VSB institution record on first startup (check if table is empty; if so, insert the default).

**Verify:** `GET /institutions` returns the VSB entry. `POST /institutions/active` switches active campus.

---

### Task 2.3 — Canonical campus coordinates

Extract campus coordinates to one shared location. Options:
- `settings.COLLEGE_DEPOT_LAT` / `settings.COLLEGE_DEPOT_LON` already exist in `config.py`.
- All components should read from the active institution's `campus_lat` / `campus_lng` (which comes from the backend) rather than from hardcoded constants.

Audit and fix:
- `App.jsx:17-18` (`DEFAULT_INSTITUTION` — keep as the default; ensure it uses `settings` values not raw literals)
- `OfficeDashboard.jsx:547` (map fallback)
- `StudentView.jsx:271` (map fallback)
- `LeafletMap.jsx:26` (hardcoded constant)

All map components receive `activeInstitution.campus_lat` / `.campus_lng` as props — verify they use props, not local constants.

---

### Task 2.4 — Fix `total_seats_deployed`

In `backend/app/api/routes_workflow.py:120`:

```python
# CURRENT (wrong — ignores per-bus capacity)
deployed_seats = len(manifest) * capacity

# CORRECT
from backend.app.models.bus import Bus
active_buses = db.query(Bus).filter(Bus.is_active == True).all()
deployed_seats = sum(b.seats for b in active_buses)
```

Note: the endpoint currently does not receive `db` for this computation. Ensure `db: Session = Depends(get_db)` is present and used.

---

### Task 2.5 — Define seating equity and expose via API

**Definition:** Seating equity = 1 minus the coefficient of variation of per-area utilization.
- Per-area utilization: `total_riders_in_area / (allocated_buses * bus_capacity)`.
- CV = `std(utilizations) / mean(utilizations)`.
- Equity = `max(0, 1 - CV)` → range [0, 1]; multiply by 100 for percentage.

Compute this in `routes_workflow.py` after building the manifest.  
Add `seating_equity_pct: float` to the manifest response.

In `OfficeDashboard`'s Overview component, replace `"100% seating equity achieved"` with the computed value.

---

### Task 2.6 — Disaggregator zero-division guard (DATA-004)

In `backend/app/core/forecasting/disaggregator.py`:
- At the top of `disaggregate_area_demand()`, check if the area has any stops.
- If `len(stops) == 0`, raise `HTTPException(status_code=422, detail=f"Area {area_id} has no stops. Cannot disaggregate demand.")`.

---

### Task 2.7 — Fix demand/capacity bar chart empty/loading state

In the `DailyPlanning` component (after Sprint-1 extraction), the Recharts `BarChart` renders on `comparisonChartData`. When `forecastData` is `null` (data not loaded yet), `comparisonChartData` is `[]` — the chart renders blank.

Add: if `loading`, render a skeleton. If `!loading && comparisonChartData.length === 0`, render an empty-state message ("No forecast data available for this date and scenario.").

---

## Test Cases

| Test | Command | Expected |
|:---|:---|:---|
| Institution persists across restart | POST /api/institutions; restart backend; GET /api/institutions | New institution present |
| Active institution persists | POST /api/institutions/active; restart; GET /institutions/active | Same institution active |
| `total_seats_deployed` | GET /api/workflow/operational-manifest | equals sum of active bus seats |
| `seating_equity_pct` present | GET /api/workflow/operational-manifest | field exists, value in [0, 100] |
| Zero-division guard | GET /api/routes with area with no stops | 422 with clear message |
| Frontend build | `npm run build` | 0 errors |

---

## Acceptance Criteria

- [ ] Institution list persists through backend restart.
- [ ] `total_seats_deployed` equals actual sum of active bus seats.
- [ ] `seating_equity_pct` field present in manifest response.
- [ ] Campus coordinates: all map components use `activeInstitution` props, not hardcoded literals.
- [ ] Demand/capacity chart shows loading skeleton and empty state.
- [ ] Disaggregator raises 422 when area has no stops.
- [ ] `npm run build` and `npm run lint` clean.
- [ ] No backend tests regressed.

---

## Definition of Done

All acceptance criteria checked. `SPRINT_STATUS.md` Sprint-2 DONE. `DEFECT_REGISTER.md` updated: SEC-001, DATA-002, DATA-003, DATA-004, M-02, M-15 moved to DONE.
