# Sprint-8 — Security, Accessibility, and Integration Hardening

**Status:** DONE<br>
**Prerequisite:** Sprint-7 DONE (Student Commuter Experience).<br>
**Objective:** Deliver cross-module hardening across security, privacy, accessibility, and container deployment consistency. Remediate `A11Y-001`, `SEC-003`, `M-05`, `M-06`, `M-07`, `L-01`, `L-06`, and `L-07`.<br>
**User-visible outcome:** Hardened security headers and Content-Security-Policy; concurrency-protected simulation endpoint preventing CPU saturation; strict production environment checks rejecting default secrets and SQLite; keyboard-accessible modal dialogs with Escape listeners and focus rings; consistent Docker container builds and environment variables.

---

## Context

Read first: `SPRINT_EXECUTION_GUIDE.md`, `SPRINT_STATUS.md` (Sprint-7 DONE), `DEFECT_REGISTER.md`.

Key defects and requirements:
- **A11Y-001**: Interactive modals (`Navbar.jsx`, `OfficeLayout.jsx`, `FleetAndDrivers.jsx`, `DispatchManifest.jsx`) lacked `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `Escape` key listeners; form inputs lacked explicit `htmlFor` / `id` bindings; missing visible focus indicators.
- **SEC-003**: `POST /api/simulate` was vulnerable to concurrent CPU saturation via Google OR-Tools CP-SAT backtesting. Implement thread-safe concurrency lock returning HTTP 429 on concurrent executions.
- **L-01**: Missing HTTP security headers (CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
- **M-05**: Divergence between `backend/Dockerfile` DB directory (`/app/busify.db`) and `docker-compose.yml` mounted volume (`/app/data/busify.db`).
- **M-06**: `frontend/Dockerfile` passed `ARG VITE_API_BASE_URL` without `/api` suffix while `api.js` read only `VITE_API_URL`.
- **M-07**: `backend/requirements.txt` was unpinned and missing dependencies present in root `requirements.txt`.
- **L-06**: Deprecated `datetime.utcnow` in `backend/app/models/plan.py`.
- **L-07**: `frontend/.oxlintrc.json` enabled only 2 rules.

---

## Scope

### In scope

1. **Security Headers & CSP (`L-01`)**:
   - Implemented `SecurityHeadersMiddleware` in `backend/app/main.py`.
   - Injected `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Content-Security-Policy`.
2. **CPU DOS Protection on Simulation (`SEC-003`)**:
   - Added thread-safe concurrency lock `_simulation_lock` in `backend/app/api/routes_simulation.py`.
   - Returns HTTP 429 Too Many Requests if another transit simulation is actively running.
3. **Configuration & Production Secrets Hardening**:
   - Added `ENVIRONMENT: str = "development"` in `backend/app/config.py`.
   - Added Pydantic `@model_validator` to reject production deployment when SQLite is used, when JWT secrets are weak/default, or when CORS origins contain wildcard `*`.
4. **Timezone Awareness (`L-06`)**:
   - Updated `created_at` in `backend/app/models/plan.py` to `DateTime(timezone=True)` with default `lambda: datetime.now(timezone.utc)`.
5. **Modal Accessibility & Focus Rings (`A11Y-001`)**:
   - Added `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` across `Navbar.jsx`, `OfficeLayout.jsx`, `FleetAndDrivers.jsx`, and `DispatchManifest.jsx`.
   - Added `Escape` key event listeners with clean removal on unmount across all four modals.
   - Bound form `<label>` and `<input>` elements with explicit `htmlFor` and `id` pairs.
   - Added `:focus-visible` ring styling to `frontend/src/index.css`.
6. **Container & Environment Consistency (`M-05`, `M-06`, `M-07`)**:
   - `backend/Dockerfile`: Created `/app/data` and configured `ENV DATABASE_URL="sqlite:////app/data/busify.db"`.
   - `frontend/src/services/api.js`: Read both `VITE_API_BASE_URL` and `VITE_API_URL` with automatic `/api` suffix normalization.
   - `frontend/Dockerfile`: Provided both build args with `/api` path.
   - `backend/requirements.txt`: Synchronized with pinned root `requirements.txt`.
7. **Linter Hardening (`L-07`)**:
   - Expanded `frontend/.oxlintrc.json` with standard correctness rules (`no-debugger`, `no-dupe-keys`, `no-empty`, `no-unused-vars`, etc.).
   - Clean 0 warnings, 0 errors across 105 rules.
8. **Automated Verification**:
   - Created dedicated `backend/app/tests/test_sprint8_hardening.py` with 10 comprehensive tests.

### Out of scope

- Production cloud deployment orchestration (post-sprint).

---

## Acceptance Criteria Verification

- [x] **Criterion 1 (L-01 Security Headers):** Verified headers (`nosniff`, `DENY`, `strict-origin-when-cross-origin`, CSP) present on API and root routes (`test_security_headers_present_on_api`, `test_security_headers_on_root_endpoint`).
- [x] **Criterion 2 (SEC-003 Simulation Concurrency):** Verified concurrent simulation request receives HTTP 429 (`test_simulation_concurrency_lock_returns_429`).
- [x] **Criterion 3 (Production Secrets Guard):** Verified Settings validator rejects SQLite, weak secrets, and wildcard CORS in production (`test_production_rejects_sqlite`, `test_production_rejects_wildcard_cors`, `test_production_rejects_weak_jwt_secret`, `test_production_accepts_valid_configuration`).
- [x] **Criterion 4 (L-06 Timezone Awareness):** Verified `Plan.created_at` produces UTC timezone-aware datetimes (`test_plan_created_at_timezone`).
- [x] **Criterion 5 (A11Y-001 Accessibility):** Verified `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `htmlFor/id` labels, `Escape` key listeners, and `:focus-visible` CSS rules (`test_accessibility_attributes_present_in_source`).
- [x] **Criterion 6 (M-05, M-06, M-07 Consistency):** Verified Dockerfile DB path `/app/data/busify.db`, frontend API URL handling, and requirements sync (`test_docker_and_requirements_consistency`).
- [x] **Criterion 7 (L-07 Linter & Build Quality):** OxLint clean with 0 warnings, 0 errors on 105 rules; Vite build clean in 1.09s.
- [x] **Criterion 8 (Full Regression Suite):** Full backend regression suite passing without regressions.
