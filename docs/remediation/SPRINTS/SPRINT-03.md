# Sprint-3 — Daily Planning Workflow, Constraint Calibration, and Benchmark Clarification

**Status:** DONE<br>
**Prerequisite:** Sprint-2 DONE (authoritative data contracts, persisted institutions, canonical coordinates).<br>
**Objective:** Transform Daily Planning into an intuitive, guided 4-step workflow (Date+Scenario → Solver Constraints → Allocation & Equity Review → Confirmation). Clarify benchmark routing heuristics (`M-03`).<br>
**User-visible outcome:** Officer has a step-by-step workflow for configuring, inspecting, and approving daily bus allocations before dispatching.

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-2 DONE).  
Key defects / improvements: ALLOC-001 (verified), ALLOC-004 (verified), DATA-005 (verified), M-03, M-04 (verified), M-15 (verified).

---

## Scope

### In scope

1. **Step-by-step Planning Stepper in `DailyPlanning.jsx`**:
   - **Step 1: Date & Scenario Calibration**: Select planning date and timetable scenario (Regular, Exams, Placement, Monsoon) with clear operational context.
   - **Step 2: Fleet Constraints & Policy**: Explicitly display active solver bounds ($K=50$ fleet budget, minimum corridor coverage $\ge 2$ buses, safety standing penalty $w_{\text{standing}}=10.0$, 55 seats/bus). Accurately frames zero standing as an optimization penalty minimization, not an unconditioned physical guarantee.
   - **Step 3: Comparative Capacity & Equity Review**: Inspect the LightGBM quantile demand vs. dynamic allocation bar chart, corridor delta badges (+/- shifted vehicles), and computed seating equity percentage.
   - **Step 4: Confirmation & Dispatch Handoff**: Summary review card with quick action to navigate to `/office/manifest` with active scenario and date passed forward.
2. **Benchmark Heuristic Documentation (`M-03`)**:
   - Clarify in `backend/app/api/routes_workflow.py` that CSV upload route benchmarking uses an angular sweep clustering heuristic with Haversine + road winding factor, contrasting it with full OR-Tools CVRP.
3. **Verification**:
   - Full regression pass on frontend and backend.

### Out of scope

- Direct dispatch execution and Plan model DB persistence (Sprint-4).
- Fleet inventory CRUD modal changes (Sprint-5).
- Stop coordinates editing (Sprint-6).

---

## Ordered Implementation Tasks

### Task 3.1 — Document Heuristic Benchmark (`M-03`)
In `backend/app/api/routes_workflow.py`, add explicit comments and docstrings explaining the angular sweep heuristic in the CSV benchmark calculation (`M-03`), documenting why this fast approximate heuristic is used for immediate client upload feedback instead of the longer-running OR-Tools CVRP solver.

### Task 3.2 — Implement Guided 4-Step Flow in `DailyPlanning.jsx`
Restructure `frontend/src/pages/office/DailyPlanning.jsx` to feature:
- A prominent progress stepper (Steps 1–4) allowing sequential forward progression or direct tab clicking.
- Interactive step contents:
  - Step 1: Date picker + scenario selector with description cards.
  - Step 2: Solver parameters card detailing fleet budget ($K=50$), minimum coverage constraint ($\ge 2$ buses/zone), objective function weightings ($w_{\text{standing}}=10\times$, $w_{\text{empty}}=1\times$, $w_{\text{churn}}=0.5\times$), and bus capacity.
  - Step 3: Capacity vs. Demand chart, allocation summary metrics, seating equity indicator, and zone allocation breakdown table.
  - Step 4: Plan confirmation summary with readiness checklist and "Proceed to Dispatch Manifest" button linking directly to `/office/manifest`.
- Step navigation buttons (Back / Next / Proceed to Dispatch).

### Task 3.3 — Verification & Evidence Recording
- Frontend Lint (`npm run lint` -> 0 errors).
- Frontend Build (`npm run build` -> clean).
- Backend Pytest (`py -3.12 -m pytest backend/app/tests/` -> 87 passed).
- Update `SPRINT_STATUS.md` and `DEFECT_REGISTER.md`.
