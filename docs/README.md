# BUSify Documentation Hub

Welcome to the **BUSify** technical documentation library. This directory contains detailed guides, architectural specifications, data dictionaries, and operational logs updated continuously as the system is developed.

---

## Documentation Index

> ### 👉 Start here
> Review **[remediation/MASTER_PLAN.md](file:///d:/PROJECTS/BUSify/docs/remediation/MASTER_PLAN.md)** and
> **[remediation/SPRINT_STATUS.md](file:///d:/PROJECTS/BUSify/docs/remediation/SPRINT_STATUS.md)**
> for current sprint progress and architecture contracts.

| Document | Purpose |
| :--- | :--- |
| [ARCHITECTURE.md](file:///d:/PROJECTS/BUSify/docs/ARCHITECTURE.md) | High-level system architecture, data flow diagrams, mathematical optimization formulations, and component relationships. |
| [API_SPECIFICATION.md](file:///d:/PROJECTS/BUSify/docs/API_SPECIFICATION.md) | Complete REST API endpoint documentation, request/response payloads, and status codes. |
| [DATA_DICTIONARY.md](file:///d:/PROJECTS/BUSify/docs/DATA_DICTIONARY.md) | Database schemas, entity relationship definitions, field types, and anonymization standards. |
| [MODULES.md](file:///d:/PROJECTS/BUSify/docs/MODULES.md) | Deep-dive breakdown of all core engines: Demand Forecasting, Fleet Allocation, Capacitated Routing, Simulator, Backend API, and Frontend. |
| [remediation/MASTER_PLAN.md](file:///d:/PROJECTS/BUSify/docs/remediation/MASTER_PLAN.md) | Remediation execution roadmap, milestone deliverables, and testing protocols. |
| [remediation/SPRINT_STATUS.md](file:///d:/PROJECTS/BUSify/docs/remediation/SPRINT_STATUS.md) | Real-time sprint status tracker with automated verification records. |

---

## Project Purpose & Social Impact
BUSify addresses systemic transit inequity in college bus networks where static scheduling leads to severe overcrowding and standing passengers, directly addressing:
- **UN SDG 11 (Sustainable Cities and Communities):** Safe, accessible, and sustainable transport for students.
- **UN SDG 10 (Reduced Inequalities):** Ensuring equitable access for transit-dependent commuters.

---

## Maintenance Rules
1. **Synchronous Updates:** Any code addition or schema modification must be accompanied by updates to [MODULES.md](file:///d:/PROJECTS/BUSify/docs/MODULES.md) or [DATA_DICTIONARY.md](file:///d:/PROJECTS/BUSify/docs/DATA_DICTIONARY.md).
2. **Defect Tracking:** Active defects and remediation tasks are tracked with verified tests in [remediation/DEFECT_REGISTER.md](file:///d:/PROJECTS/BUSify/docs/remediation/DEFECT_REGISTER.md).
