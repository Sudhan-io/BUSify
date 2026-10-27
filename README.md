# BUSify: Demand-Aware College Fleet Allocation & Capacitated Routing

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![OR-Tools](https://img.shields.io/badge/Optimizer-Google%20OR--Tools-orange.svg)](https://developers.google.com/optimization)
[![LightGBM](https://img.shields.io/badge/Forecasting-LightGBM-yellow.svg)](https://lightgbm.readthedocs.io)
[![React Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb.svg)](https://vitejs.dev)
[![Tailwind CSS v4](https://img.shields.io/badge/Styling-Tailwind%20v4-38bdf8.svg)](https://tailwindcss.com)
[![SDG 11 & 10](https://img.shields.io/badge/Impact-UN%20SDG%2010%20%26%2011-green.svg)](https://sdgs.un.org)

> **BUSify** replaces static, rigid college bus timetables with a predictive, demand-aware dispatch system. By estimating ridership surges at the regional zone level and solving both macro fleet integer programs and micro capacitated vehicle routing (CVRP), BUSify ensures seating equity, eliminates standing travel, and cuts deadhead fuel waste.

---

## Social Impact & UN SDG Alignment
- **UN SDG 11 (Sustainable Cities & Communities):** Target 11.2 — Providing access to safe, affordable, accessible, and sustainable transport systems for all students.
- **UN SDG 10 (Reduced Inequalities):** Protects transit-dependent students who lack private personal vehicle alternatives and ensures paid transit fees guarantee a confirmed seat.

---

## System Architecture


```text
                          ┌─────────────────────┐
                          │   Transport Office  │
                          │ Registrations & Cal │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ Data Anonymizer &   │
                          │ Feature Pipeline    │
                          └──────────┬──────────┘
                                     │
                        ┌────────────┴────────────┐
                        ▼                         ▼
             ┌─────────────────────┐   ┌─────────────────────┐
             │ Demand Forecasting  │   │  Fleet Allocation   │
             │ LightGBM (p50, p90) │   │  OR-Tools (CP-SAT)  │
             └──────────┬──────────┘   └──────────┬──────────┘
                        │                         │
                        │ Area Demands            │ Bus Counts (n_a)
                        └────────────┬────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ Capacitated Routing │
                          │ OR-Tools CVRP+OSRM  │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │   FastAPI Backend   │
                          │   REST Endpoints    │
                          └──────────┬──────────┘
                                     │
                        ┌────────────┴────────────┐
                        ▼                         ▼
             ┌─────────────────────┐   ┌─────────────────────┐
             │ Transport Dashboard │   │  Student Commuter   │
             │ Recharts & Simulator│   │  Route & Crowding   │
             └─────────────────────┘   └─────────────────────┘
```

---

## Core Mathematical Formulations

### 1. Pinball Loss Quantile Regression ($\alpha = 0.50, 0.90$)
$$L_\alpha(y, \hat{y}) = \max(\alpha(y - \hat{y}), (1 - \alpha)(\hat{y} - y))$$
* **$p50$ (Median):** Expected operational volume.
* **$p90$ (Upper Headroom):** Upper-quantile demand insuring against passenger overload.

### 2. Fleet Allocation Integer Program (OR-Tools CP-SAT)
$$\min \sum_{a \in A} W_s \cdot s_a + W_e \cdot e_a + W_d \cdot d_a$$
$$\text{subject to: } \sum_{a \in A} n_a \le 50, \quad n_a \ge 2 \quad \forall a$$
$$s_a \ge D_a^{p90} - (55 \cdot n_a), \quad e_a \ge (55 \cdot n_a) - D_a^{p90}$$
$$d_a \ge |n_a - n_{\text{baseline}, a}|$$

### 3. Capacitated Vehicle Routing Problem (CVRP)
* Formulated with Google OR-Tools Routing Library.
* Maximum vehicle capacity: $55$ passengers.
* Automated split-pickup preprocessor for high-volume junctions.
* Reverse-scheduled morning departure timestamps ensuring arrival at the campus depot before $08:30\text{ AM}$.

---

## Quickstart & Setup Guide

### 1. Backend Setup & Run
```bash
# Clone and navigate to project root
git clone https://github.com/Sudhan-io/BUSify.git
cd BUSify

# Install backend dependencies
python -m pip install -r backend/requirements.txt

# Seed realistic college transit dataset (47 stops, 50 buses, 2,200 registrations)
python -m backend.app.core.data.synthetic_generator

# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Frontend Setup & Run
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
* Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Testing & Verification

Run the full automated test suite (122 unit, integration, and stress tests) and frontend checks locally:
```bash
# Frontend verification (from frontend directory)
cd frontend
npm ci
npm run lint    # OxLint across 105 rules
npm run build   # Vite production build

# Backend verification (from project root)
python -m pip install -r requirements.txt
python -m backend.app.core.data.synthetic_generator   # Bootstrap deterministic test data
python -m pytest backend/app/tests/ -v --tb=short     # Full 122-test regression suite
```

### Automated CI Pipeline

A reproducible GitHub Actions CI pipeline (`.github/workflows/ci.yml`) automatically executes on every push to `main` and on pull requests targeting `main`. It tests:
* **Frontend Job (Node.js 20):** `npm ci`, OxLint (`npm run lint`), and Vite build (`npm run build`).
* **Backend Job (Python 3.12):** Clean synthetic database bootstrap and full pytest regression suite with non-sensitive isolated test environment variables.


---

## Technical Documentation Hub

All design decisions, schemas, API specifications, and remediation roadmaps are organized in `docs/`:

| Document | Purpose |
| :--- | :--- |
| [docs/ARCHITECTURE.md](file:///d:/PROJECTS/BUSify/docs/ARCHITECTURE.md) | High-level system architecture and mathematical models |
| [docs/API_SPECIFICATION.md](file:///d:/PROJECTS/BUSify/docs/API_SPECIFICATION.md) | Full REST endpoint specifications & schemas |
| [docs/DATA_DICTIONARY.md](file:///d:/PROJECTS/BUSify/docs/DATA_DICTIONARY.md) | Database schemas, column constraints, privacy hashing |
| [docs/MODULES.md](file:///d:/PROJECTS/BUSify/docs/MODULES.md) | Deep-dive breakdown of all 6 software modules |
| [docs/remediation/MASTER_PLAN.md](file:///d:/PROJECTS/BUSify/docs/remediation/MASTER_PLAN.md) | Multi-sprint remediation plan and architecture contracts |
| [docs/remediation/SPRINT_STATUS.md](file:///d:/PROJECTS/BUSify/docs/remediation/SPRINT_STATUS.md) | Sprint progress tracker and automated verification evidence |
| [docs/remediation/DEFECT_REGISTER.md](file:///d:/PROJECTS/BUSify/docs/remediation/DEFECT_REGISTER.md) | Stable-ID defect register and remediation tracking |
| [CHANGELOG.md](file:///d:/PROJECTS/BUSify/CHANGELOG.md) | Comprehensive development changelog |
