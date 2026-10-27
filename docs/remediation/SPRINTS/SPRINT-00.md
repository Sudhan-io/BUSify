# Sprint-0 — Baseline, Loading States, Dead Code Removal

**Status:** DONE
**Objective:** Establish an honest, verifiable baseline before any navigation or UX restructuring.  
**User-visible outcome:** No hardcoded operational numbers appear while data loads. API failures show inline messages. Page title is correct.

---

## Context

Read before starting:
- `docs/remediation/MASTER_PLAN.md` (sprint sequence)
- `docs/remediation/ARCHITECTURE_AND_CONTRACTS.md` (file layout)
- `docs/remediation/SPRINT_EXECUTION_GUIDE.md` (process rules)
- `docs/remediation/DEFECT_REGISTER.md` (defect inventory)

---

## Scope

### In scope

- Remove hardcoded fallback numbers from `OfficeDashboard.jsx` that appear as operational data.
- Render the `loading` boolean as a spinner/skeleton in `OfficeDashboard.jsx`.
- Render API errors as inline alerts in `OfficeDashboard.jsx` (not console-only).
- Render loading state in `StudentView.jsx`.
- Replace `alert()` calls with in-app error UI.
- Fix page `<title>` and add meta description to `frontend/index.html`.
- Remove confirmed dead files: `App.css` (unimported), `tailwind.config.js` (no `@config` in `index.css`).
- Record baseline test results (pass/fail/skip counts and test command).

### Out of scope (do these in later sprints)

- Navigation structure or routing (Sprint-1).
- Algorithm changes.
- Backend changes.
- Accessibility (Sprint-8).
- Institution persistence (Sprint-2).

---

## Prerequisites

- Sprint-0 has no prerequisites — it is the first sprint.
- Verify git is clean before starting: `git status` must show no unexpected modifications.

---

## Files likely to change

| File | Change |
|:---|:---|
| `frontend/src/views/OfficeDashboard.jsx` | Remove fallback literals; render loading spinner and error alerts |
| `frontend/src/views/StudentView.jsx` | Render loading state |
| `frontend/index.html` | Fix `<title>`, add `<meta name="description">` |
| `frontend/src/App.css` | Delete (confirm it is not imported anywhere first) |
| `frontend/tailwind.config.js` | Delete (confirm `index.css` has no `@config` directive) |

**Do NOT change:** Any backend file. Any algorithm file. `busify.db`. `.env`.

---

## Ordered Implementation Tasks

### Task 0.1 — Verify environment

1. Run `cd frontend && npm run build`. Must succeed with 0 errors.
2. Run `npm run lint`. Record warning count. Must be 0 errors.
3. Run backend tests (see §Verification Commands). Record pass/fail/skip.
4. Record results in `SPRINT_STATUS.md`.

**Completion criterion:** Results recorded in `SPRINT_STATUS.md`.

---

### Task 0.2 — Remove hardcoded fallback numbers from OfficeDashboard hero

**Target:** `frontend/src/views/OfficeDashboard.jsx:269-270`

```jsx
// CURRENT (shows "50 Active Buses" / "2750 Confirmed Seats • 0 Standing" as default)
<strong>{manifestData?.total_active_buses || 50} Active Buses.</strong>
<span>{manifestData?.total_seats_deployed || 2750} Confirmed Seats • 0 Standing</span>
```

Replace with:
```jsx
<strong>
  {loading ? '— ' : (manifestData?.total_active_buses ?? '—')} Active Buses.
</strong>
<span>
  {loading ? '— seats' : `${manifestData?.total_seats_deployed ?? '—'} Confirmed Seats`}
  {' • '}
  {loading ? '—' : (manifestData?.total_standing ?? '—')} Standing
</span>
```

**Completion criterion:** Hero section shows `—` while loading, real data when loaded, never `50`/`2750` as a default.

---

### Task 0.3 — Render loading spinner in OfficeDashboard KPI cards

**Target:** `frontend/src/views/OfficeDashboard.jsx` — the four `<MetricCard>` components at lines ~332-364.

When `loading` is true, each MetricCard should receive a loading indicator or show a spinner. The simplest approach: add a `loading` prop to `MetricCard` and render a pulsing skeleton when true.

Check `MetricCard.jsx` first to understand its props, then add `loading` support.

**Completion criterion:** During the initial page load, KPI cards show a spinner/skeleton, not hardcoded values.

---

### Task 0.4 — Add inline error state to OfficeDashboard

**Target:** `frontend/src/views/OfficeDashboard.jsx:82` — `catch (err)` block in `loadData()`.

Add a `manifestError` state variable. In the catch block: `setManifestError(describeError(err))`. Render it as an inline alert above the KPI cards section (not an `alert()` dialog).

Pattern already exists in `StudentView.jsx:177-183` — follow the same `role="alert"` pattern.

**Completion criterion:** If the backend is unreachable, `OfficeDashboard` renders a red inline alert with the error message. The tables show empty states, not stale data.

---

### Task 0.5 — Replace `alert()` with inline errors in OfficeDashboard

**Targets:**
- `OfficeDashboard.jsx:213` — bus save failure: `alert(err.response?.data?.detail || "Failed to save bus details.")`
- `OfficeDashboard.jsx:222 / 232` — bus delete failure: `alert(err.response?.data?.detail || "Failed to remove bus.")`

Add a `busError` state. Render it below the bus form or above the fleet table using the same alert pattern. Remove the `alert()` calls.

**Completion criterion:** Bus save/delete errors appear inline; no browser `alert()` dialogs.

---

### Task 0.6 — Render loading state in StudentView

**Target:** `frontend/src/views/StudentView.jsx`

`loading` state exists at line 21. Verify where it is used in the JSX. Add a loading indicator to the boarding pass section (lines ~175-215) so it is clear the pass is loading, not empty.

**Completion criterion:** During profile load, the boarding pass card shows a spinner or `Loading...` indicator, not a blank card.

---

### Task 0.7 — Fix page title and add meta description

**Target:** `frontend/index.html`

Change `<title>frontend</title>` to `<title>BUSify | Transit Intelligence</title>`.  
Add `<meta name="description" content="Intelligent demand-aware bus fleet allocation and routing platform for college transit management.">`.

**Completion criterion:** Browser tab shows "BUSify | Transit Intelligence".

---

### Task 0.8 — Remove dead files (only after confirming they are unused)

Before deleting, run:
```powershell
# Confirm App.css is not imported
Select-String -Path "frontend/src" -Pattern "App\.css" -Recurse
# Confirm tailwind.config.js has no @config in index.css
Select-String -Path "frontend/src/index.css" -Pattern "@config"
```

If no imports found: delete `frontend/src/App.css` and `frontend/tailwind.config.js`.

**Do NOT delete** `frontend/src/assets/` if any assets are referenced in JSX (check first).

**Completion criterion:** Deleted files confirmed unused by grep. Build succeeds after deletion.

---

## Test Cases

| Test | Command | Expected result |
|:---|:---|:---|
| Frontend build | `npm run build` | 0 errors, success |
| Frontend lint | `npm run lint` | 0 errors |
| Backend test suite | `python -m pytest backend/app/tests/ -v --tb=short` | Record actual counts |
| Hardcoded `50` | `Select-String -Path frontend/src/views/OfficeDashboard.jsx -Pattern "\|\| 50"` | 0 matches |
| Hardcoded `2750` | `Select-String -Path frontend/src/views/OfficeDashboard.jsx -Pattern "\|\| 2750"` | 0 matches |
| `alert()` removed | `Select-String -Path frontend/src/views/OfficeDashboard.jsx -Pattern "window\.alert\|^  alert("` | 0 matches |

---

## Acceptance Criteria

All must be verified before marking Sprint-0 DONE:

- [x] `npm run build` succeeds with 0 errors.
- [x] `npm run lint` reports 0 errors.
- [x] Hero section shows `—` during loading, not `50`/`2750`.
- [x] KPI cards show a loading state during initial data fetch.
- [x] Bus save/delete errors appear as inline alerts, not `alert()` dialogs.
- [x] `StudentView` boarding pass shows a loading indicator.
- [x] Page title reads "BUSify | Transit Intelligence".
- [x] Baseline backend test results recorded in `SPRINT_STATUS.md` (pass/fail/skip counts).

---

## Regression Risks

| Risk | Mitigation |
|:---|:---|
| Removing `|| 50` changes what renders when `manifestData` is `null` | Show `—` explicitly; add null-check before every KPI consumer |
| Deleting `App.css` breaks styles if it was imported | Grep for imports before deleting |
| Adding `manifestError` state requires careful placement in the 1278-line file | Read lines 66-90 fully before editing the effect |

---

## Definition of Done

1. All acceptance criteria checked.
2. Test results recorded in `SPRINT_STATUS.md`.
3. DEFECT_REGISTER.md updated: DATA-001, NAV-002 moved to DONE if fixed.
4. Handoff note written at bottom of `SPRINT_STATUS.md`.

---

## Handoff Instructions for Next Session

If this sprint is IN PROGRESS when the session ends:

- Record which tasks are complete and which are not in `SPRINT_STATUS.md`.
- List any files modified.
- List any new defects discovered.
- The next session must read `SPRINT_STATUS.md` before touching any file.
