# BUSify: System Architecture Specification

## 1. Architectural Overview

**BUSify** replaces rigid, static college bus schedules with a closed-loop, predictive and capacitated transit dispatch system. The platform orchestrates 4 core computational stages:
1. **Demand Forecasting:** LightGBM quantile regression ($p50$ median and $p90$ peak capacity).
2. **Fleet Allocation:** OR-Tools Integer Programming allocating a fixed 50-bus fleet across regional zones.
3. **Capacitated Routing:** Multi-vehicle routing problem (CVRP) ensuring every stop is served with zero standing students while minimizing mileage.
4. **Visibility Layer:** Dual-surface React application for the Transport Office and Student body.

```text
                                  ┌─────────────────────────────┐
                                  │      Transport Office       │
                                  │   Registrations & Calendar  │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │     Data Processing &       │
                                  │    Privacy Anonymization    │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │    PostgreSQL / SQLite      │
                                  │  Stops, Buses, Demand, Plans│
                                  └──────────────┬──────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
             ┌─────────────────────┐                           ┌─────────────────────┐
             │ Demand Forecasting  │                           │  Fleet Allocation   │
             │ LightGBM (p50, p90) │                           │  OR-Tools (CP-SAT)  │
             └──────────┬──────────┘                           └──────────┬──────────┘
                        │                                                 │
                        │ Area Demands (p50/p90)                          │ Bus Counts (n_a)
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │ Capacitated Routing (CVRP)  │
                                  │ OR-Tools + OSRM Road Matrix │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │       FastAPI Backend       │
                                  │  REST Orchestration API     │
                                  └──────────────┬──────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
             ┌─────────────────────┐                           ┌─────────────────────┐
             │ Transport Dashboard │                           │    Student View     │
             │ Recharts & Simulation│                          │ Assigned Bus & Crowd│
             └─────────────────────┘                           └─────────────────────┘
```

---

## 2. Mathematical Formulations

### A. Demand Forecasting (Quantile Regression)
Instead of predicting single point estimates (which fail during demand surges), we formulate demand prediction as asymmetric **quantile regression** using the pinball loss function:

$$L_\alpha(y, \hat{y}) = \begin{cases} \alpha(y - \hat{y}) & \text{if } y \ge \hat{y} \\ (1 - \alpha)(\hat{y} - y) & \text{if } y < \hat{y} \end{cases}$$

* **$\alpha = 0.50$ (Median):** Expected regular volume used for financial and seat-fill estimations.
* **$\alpha = 0.90$ (90th Percentile):** Safe upper-bound demand ensuring sufficient bus capacity is dispatched to eliminate standing passengers 90% of the time.

### B. Fleet Allocation Integer Programming
Allocates a fixed fleet of $B = 50$ buses across set of geographic zones $A$:

* **Decision Variables:**
  * $n_a \in \mathbb{Z}_{\ge 0}$: Buses assigned to area $a$.
  * $s_a \ge 0$: Unmet demand (standing students) in area $a$.
  * $e_a \ge 0$: Surplus empty seats in area $a$.
  * $d_a \ge 0$: Churn distance from the status-quo schedule $|n_a - n_{\text{current}, a}|$.

* **Objective Function:**
  $$\min \sum_{a \in A} s_a + \lambda \sum_{a \in A} e_a + \mu \sum_{a \in A} d_a$$

* **Constraints:**
  1. **Fleet Capacity Limit:** $\sum_{a \in A} n_a \le B$
  2. **Minimum Coverage:** $n_a \ge n_{\min, a} \quad \forall a \in A$
  3. **Standing Capacity Slack:** $s_a \ge D_a^{p90} - (C_{\text{bus}} \cdot n_a) \quad \forall a \in A$
  4. **Empty Seat Slack:** $e_a \ge (C_{\text{bus}} \cdot n_a) - D_a^{p90} \quad \forall a \in A$
  5. **Schedule Stability Bounds:** $d_a \ge n_a - n_{\text{current}, a}$ and $d_a \ge n_{\text{current}, a} - n_a$

### C. Capacitated Vehicle Routing Problem (CVRP)
Within each area $a$, a set of stops $V_a$ with positive demands $q_i$ are assigned across $n_a$ allocated vehicles:
* **Depot Node:** College campus $0$.
* **Capacity Dimension:** Cumulative student boarding $\sum_{i \in \text{route}} q_i \le C_{\text{bus}}$.
* **Time Windows:** Cumulative transit time must ensure arrival before class start time ($T_{\text{class}} = 08:30$).

---

## 3. Technology Stack Decisions

| Component | Selected Technology | Alternative Rejected | Rationale |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | FastAPI | Flask / Django | Asynchronous endpoints, automatic OpenAPI documentation, strict Pydantic model validation. |
| **Forecasting Model** | LightGBM | ARIMA / Prophet | Handles non-linear multi-feature tabular signals (exams, weekdays, rolling features) orders of magnitude faster. |
| **Optimization Solver** | Google OR-Tools CP-SAT | Custom Heuristics | Guaranteed mathematical optimality, native vehicle routing constraints, battle-tested performance. |
| **Routing Matrix** | OSRM + Haversine fallback | Google Maps API | Zero API costs, privacy-preserving, runs locally, offline development support. |
| **Database** | PostgreSQL + SQLite fallback | MongoDB | Relational integrity for bookings/stops, PostGIS geospatial support, local zero-install testability. |
| **Frontend** | React + Vite + Tailwind | Next.js / Vanilla JS | Rapid development, modular components, high-performance interactive map and chart rendering. |
