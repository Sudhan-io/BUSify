# BUSify — Master Remediation Plan

**Owner:** Lead Architect  
**Last updated:** 2026-10-27  
**Status:** Planning phase complete. Ready for Sprint-0 execution.

---

## 1. Repository Architecture Summary

BUSify is a React + FastAPI college transit platform for VSB Engineering College, Karur (50 buses, 2200+ students, 5 residential zones AREA_A–AREA_E).

**Frontend:** Single-page React app. Two views: `OfficeDashboard.jsx` (1278 lines, all officer workflows on one page) and `StudentView.jsx`. No router. No global state manager.

**Backend:** FastAPI + SQLite (dev) / PostgreSQL (prod). OR-Tools CP-SAT for fleet allocation and VRP routing. LightGBM for demand forecasting. OSRM for road distances (Haversine fallback).

**Full architecture:** See `docs/remediation/ARCHITECTURE_AND_CONTRACTS.md`.

---

## 2. Target User Experience (Post-Remediation)

### Transport Office — 7 named destinations

| Tab | Contents |
|:---|:---|
| **Overview** | KPI cards (real sources), dispatch readiness, actionable warnings, shortcuts |
| **Daily Planning** | Guided 4-step flow: date+scenario → allocate → review → confirm |
| **Routes & Map** | Zone selector, map, stop list, route details, capacity chips |
| **Dispatch Manifest** | Searchable/filterable table, approval guard, versioned dispatch |
| **Fleet & Drivers** | Bus inventory CRUD separate from dispatch |
| **Students & Demand** | Demand chart, opt-out management, stop demand per area |
| **Reports & History** | Dispatch audit log, 7-day simulation, historical KPIs |

### Student Commuter — 3 sections

| Section | Contents |
|:---|:---|
| **My Bus Pass** | Digital pass: bus code, seat, driver (no exposure without auth) |
| **My Route** | Ordered stop list, map, scheduled times |
| **Travel Status** | Opt-out toggle, occupancy, service status |

---

## 3. Prioritized Finding Summary

### Confirmed Critical (fix first)

1. **NAV-001** — No navigation; entire officer UI is one scroll. All other UX work blocked by this.
2. **DATA-001** — Hardcoded `50 buses / 2750 seats / 2150 riders` displayed as operational data when API is slow.
3. **DISPATCH-001** — "Approve & Dispatch" is client-only button; no server validation or audit trail.
4. **DISPATCH-002** — `Plan` model unused; approved dispatches are discarded.
5. **SEC-001** — Institution registry in process memory; multi-worker deployment diverges.
6. **NAV-002** — Loading state never rendered; API failures swallowed to console.

### High severity (needed for operational correctness)

- **ALLOC-002, ALLOC-003** — Manifest bus codes and driver assignments are synthetic, not from the database.
- **MAP-001, MAP-002** — Wrong field names produce blank arrival times and stop details in the map.
- **DATA-007** — Manifest table silently truncated to 10 rows.
- **A11Y-001** — Forms and modals not keyboard-accessible.

---

## 4. Sprint Sequence

Dependencies flow top-to-bottom. Do not start a sprint until its prerequisites are complete.

```
Sprint-0: Baseline + environment + loading/error states + dead code
    │
Sprint-1: App shell, navigation, routing structure, design system
    │
Sprint-2: Data integrity — metric sources, institution persistence, campus deduplication
    │
Sprint-3: Daily Planning workflow — guided flow, allocation review, constraint display
    │
Sprint-4: Dispatch Manifest — real bus/driver assignment, approval guard, Plan persistence
    │
Sprint-5: Fleet & Drivers + Students & Demand management
    │
Sprint-6: Routes & Map — field-name fixes, stop sequencing, geographic correctness
    │
Sprint-7: Student Commuter experience — pass accuracy, opt-out, auth prep
    │
Sprint-8: Security, accessibility, deployment correctness, integration testing
```

### Dependencies

| Sprint | Requires |
|:---|:---|
| Sprint-1 | Sprint-0 (clean baseline, working loading states) |
| Sprint-2 | Sprint-1 (navigation shell exists for new data to populate) |
| Sprint-3 | Sprint-2 (metric definitions authoritative) |
| Sprint-4 | Sprint-3 (allocation result is trustworthy) |
| Sprint-5 | Sprint-1 (navigation shell); Sprint-2 (data contracts) |
| Sprint-6 | Sprint-2 (campus coordinates canonical) |
| Sprint-7 | Sprint-2 (student data contracts); Sprint-5 (student data endpoints) |
| Sprint-8 | All prior sprints (regression target) |

---

## 5. Cross-Sprint Risks

| Risk | Mitigation |
|:---|:---|
| `OfficeDashboard.jsx` (1278 lines) is the blast radius of every sprint | Extract one section per sprint; preserve all existing state logic while doing so |
| OSRM not running locally — `/routes` and `/operational-manifest` return 500 | Tests that need routing must skip when OSRM is absent; use Haversine fallback in dev |
| Python env on dev machine may be 3.10 vs target 3.12 | Create a venv and install from root `requirements.txt` before any backend test run |
| Institution registry is in-memory — multi-worker diverges | Fix in Sprint-2; do not add more in-memory state between Sprint-0 and Sprint-2 |
| `busify.db` is tracked intentionally (Docker build depends on it) | Do not add it to `.gitignore`; schema migrations require Alembic (M-24, Sprint-8) |
| Two conflicting baselines (H-05) produce different churn metrics | Fix in Sprint-3 before displaying churn in the new Planning workflow |

---

## 6. Success Criteria

The remediation is complete when:

1. Officer can navigate between Overview, Planning, Map, Dispatch, Fleet, Students, and Reports without scrolling.
2. Every KPI card shows a spinner during load and an inline error on failure; no hardcoded fallback numbers.
3. "Approve & Dispatch" calls a server endpoint that validates the manifest and creates a `Plan` record; the button is disabled when no valid manifest exists.
4. Manifest table shows all rows (not silently truncated to 10) with pagination.
5. Manifest bus codes and driver assignments come from the `buses` table, not sequential generation.
6. Campus coordinates are canonical (one source of truth); zone metadata consistent.
7. Map arrival time field names are correct; stop details display properly.
8. All forms have `htmlFor/id` pairs; all modals have `role="dialog"`, focus trap, and Escape dismissal.
9. Student pass shows correct occupancy from server; seat guarantee reflects real allocation.
10. All existing tests pass; new tests added for Dispatch persistence, metric invariants, and accessibility.

---

## 7. Planning Documents Index

| File | Purpose |
|:---|:---|
| `docs/remediation/MASTER_PLAN.md` | This file |
| `docs/remediation/DEFECT_REGISTER.md` | Stable-ID defect inventory with severity and sprint mapping |
| `docs/remediation/ARCHITECTURE_AND_CONTRACTS.md` | Actual file layout, metric definitions, API contracts |
| `docs/remediation/DECISIONS.md` | Architecture decision log |
| `docs/remediation/SPRINT_STATUS.md` | Progress tracker (update after each sprint) |
| `docs/remediation/SPRINT_EXECUTION_GUIDE.md` | Instructions for a fresh agent session |
| `docs/remediation/SPRINTS/SPRINT-00.md` | Sprint-0 specification |
| `docs/remediation/SPRINTS/SPRINT-01.md` | Sprint-1 specification |
| `docs/remediation/SPRINTS/SPRINT-02.md` | Sprint-2 specification |
| … | (further sprints added as each prior sprint completes) |
| `docs/OUTSTANDING_ISSUES.md` | Pre-existing bug register (authoritative history) |
