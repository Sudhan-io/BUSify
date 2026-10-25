# BUSify Documentation Hub

Welcome to the **BUSify** technical documentation library. This directory contains detailed guides, architectural specifications, data dictionaries, and operational logs updated continuously as the system is developed.

---

## Documentation Index

> ### 👉 Start here
> If you are an AI agent or a new contributor picking this repo up, read
> **[OUTSTANDING_ISSUES.md](file:///d:/PROJECTS/BUSify/docs/OUTSTANDING_ISSUES.md) first.**
> It lists every *unresolved* defect with file:line references, the environment
> traps that will waste your time, what has already been fixed (so you don't
> redo or revert it), and which tests are expected to fail.

| Document | Purpose |
| :--- | :--- |
| [OUTSTANDING_ISSUES.md](file:///d:/PROJECTS/BUSify/docs/OUTSTANDING_ISSUES.md) | **Work backlog.** Unresolved defects by severity, environment traps, completed-work log, expected test failures. Primary handoff document. |
| [ARCHITECTURE.md](file:///d:/PROJECTS/BUSify/docs/ARCHITECTURE.md) | High-level system architecture, data flow diagrams, mathematical optimization formulations, and component relationships. |
| [SPRINT_PLAN.md](file:///d:/PROJECTS/BUSify/docs/SPRINT_PLAN.md) | Structured 6-sprint execution roadmap, milestone deliverables, and testing audit protocols. |
| [AUDIT_REPORT_SPRINT_1_2.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_1_2.md) | **Certified Audit Report** for Sprint 1 (Data Foundation) and Sprint 2 (Algorithmic Engines) — 100% test pass rate. |
| [AUDIT_REPORT_SPRINT_3.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_3.md) | **Certified Audit Report** for Sprint 3 (FastAPI REST Orchestration Layer & Endpoints) — 100% test pass rate. |
| [AUDIT_REPORT_SPRINT_4.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_4.md) | **Certified Audit Report** for Sprint 4 (Frontend Scaffold & Core Component Design System) — 100% build pass. |
| [AUDIT_REPORT_SPRINT_5.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_5.md) | **Certified Audit Report** for Sprint 5 (Dual Dashboards: Office & Student Views + Interactive Geospatial Maps) — 100% pass. |
| [AUDIT_REPORT_SPRINT_6.md](file:///d:/PROJECTS/BUSify/docs/AUDIT_REPORT_SPRINT_6.md) | **Certified Final Audit Report** for Sprint 6 (STA, Stress Invariants, Edge Cases & System Delivery) — 27/27 tests pass. |
| [MODULES.md](file:///d:/PROJECTS/BUSify/docs/MODULES.md) | Deep-dive breakdown of all core engines: Demand Forecasting, Fleet Allocation, Capacitated Routing, Simulator, Backend API, and Frontend. |
| [DATA_DICTIONARY.md](file:///d:/PROJECTS/BUSify/docs/DATA_DICTIONARY.md) | Database schemas, entity relationship definitions, field types, and anonymization standards. |
| [FAILURES_AND_IMPROVEMENTS.md](file:///d:/PROJECTS/BUSify/docs/FAILURES_AND_IMPROVEMENTS.md) | **Live incident, failure, and improvement tracking log**. Details bugs encountered, root cause analyses, solutions applied, and architecture adjustments. |
| [API_SPECIFICATION.md](file:///d:/PROJECTS/BUSify/docs/API_SPECIFICATION.md) | Complete REST API endpoint documentation, request/response payloads, and status codes. |

---

## Project Purpose & Social Impact
BUSify addresses systemic transit inequity in college bus networks where static scheduling leads to severe overcrowding and standing passengers, directly addressing:
- **UN SDG 11 (Sustainable Cities and Communities):** Safe, accessible, and sustainable transport for students.
- **UN SDG 10 (Reduced Inequalities):** Ensuring equitable access for transit-dependent commuters.

---

## Maintenance Rules
1. **Synchronous Updates:** Any code addition or schema modification must be accompanied by updates to [MODULES.md](file:///d:/PROJECTS/BUSify/docs/MODULES.md) or [DATA_DICTIONARY.md](file:///d:/PROJECTS/BUSify/docs/DATA_DICTIONARY.md).
2. **Issue Logging:** Whenever a tool fails, a model doesn't converge, or an edge case breaks an optimization constraint, an entry must be appended to [FAILURES_AND_IMPROVEMENTS.md](file:///d:/PROJECTS/BUSify/docs/FAILURES_AND_IMPROVEMENTS.md).
3. **Backlog Discipline:** Unresolved defects belong in [OUTSTANDING_ISSUES.md](file:///d:/PROJECTS/BUSify/docs/OUTSTANDING_ISSUES.md). When an item is fixed, move it from the open tables to the §2 "Already Fixed" section and record the verification method. Keep status markers (`OPEN` / `IN-PROGRESS` / `BLOCKED` / `DONE`) accurate — an item marked done but never verified is worse than one left open.
