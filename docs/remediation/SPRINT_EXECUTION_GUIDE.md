# BUSify — Sprint Execution Guide

**Purpose:** Instructions for a fresh agent session (including Gemini 3.8 Flash) to load context, identify what to do, execute only authorized work, and produce a clean handoff.

**Read this first, every session. Do not skip any step.**

---

## Step 1 — Load required context (every session)

Read these files in order. Do not proceed until all four are loaded.

1. `docs/remediation/MASTER_PLAN.md` — architecture summary, sprint sequence, success criteria.
2. `docs/remediation/ARCHITECTURE_AND_CONTRACTS.md` — file layout, metric definitions, API contracts, unknowns.
3. `docs/remediation/DEFECT_REGISTER.md` — stable-ID defect inventory.
4. `docs/remediation/SPRINT_STATUS.md` — which sprint is active, what is incomplete, blockers.
5. `docs/remediation/DECISIONS.md` — architecture decisions already made (avoid relitigating).

Also read `docs/OUTSTANDING_ISSUES.md` §1 (environment traps) before running any command.

---

## Step 2 — Verify repository state

Before touching any code:

```powershell
# Verify working tree
cd d:\PROJECTS\BUSify
git status        # confirm no uncommitted unexpected changes

# Verify frontend builds
cd frontend
npm run build     # must succeed
npm run lint      # 0 errors required

# Verify backend tests (skip if Python env not set up — document this)
cd d:\PROJECTS\BUSify
$env:PYTHONPATH = "."
python -m pytest backend/app/tests/ -v --tb=short
```

Record test results in `SPRINT_STATUS.md` for the active sprint.

---

## Step 3 — Identify the active sprint

Read `SPRINT_STATUS.md`. Find the first sprint with status `NOT STARTED` or `IN PROGRESS` where all prerequisites are `DONE`.

Open the sprint's specification file:
- Sprint-0: `docs/remediation/SPRINTS/SPRINT-00.md`
- Sprint-1: `docs/remediation/SPRINTS/SPRINT-01.md`
- etc.

Read the sprint file completely before touching any code.

---

## Step 4 — Execute sprint tasks

Follow these rules:

1. **Work only within the sprint's explicit scope.** Do not fix bugs not listed in the sprint's task list, even if you see them. Record them in `DEFECT_REGISTER.md` and move on.
2. **Read the target file before editing it.** Never edit based on memory or previous session summaries — inspect the actual current file first.
3. **Make one cohesive change at a time.** Complete a task, verify it, then move to the next.
4. **Never fabricate test results.** Run tests, record actual output.
5. **Never mark a task complete without evidence.** "Looks right" is not evidence.
6. **When a test fails**, do not skip it. Diagnose the failure, fix the root cause or record it as a blocker.
7. **When blocked**, record the blocker in `SPRINT_STATUS.md` and stop that task. Do not guess past a blocker.

---

## Step 5 — Verification

After completing all tasks in the sprint:

```powershell
# Frontend
cd frontend
npm run build     # must succeed, 0 errors
npm run lint      # 0 errors

# Backend
cd d:\PROJECTS\BUSify
$env:PYTHONPATH = "."
python -m pytest backend/app/tests/ -v --tb=short
```

Check every acceptance criterion in the sprint file. Check them one by one. Record pass/fail in `SPRINT_STATUS.md`.

---

## Step 6 — Update documentation

After all acceptance criteria pass:

1. Mark the sprint `DONE` in `SPRINT_STATUS.md`. Record the evidence.
2. Move any defects you fixed from OPEN to DONE in `DEFECT_REGISTER.md`.
3. Record any new defects you discovered in `DEFECT_REGISTER.md` (do not fix them now unless they are blockers).
4. Record any significant decisions in `DECISIONS.md`.

---

## Step 7 — Produce a handoff

At the end of the session, write a brief handoff note at the bottom of `SPRINT_STATUS.md`:

```
## Handoff Note — [sprint] — [date]

Completed tasks: [list]
Modified files: [list]
Tests: [N passed, M failed, K skipped] — [test command used]
Outstanding defects from this sprint: [IDs]
Next task for next session: [exact first task from next sprint]
```

---

## Non-negotiable constraints (do not override)

1. Do not replace real backend computations with hardcoded numbers.
2. Do not delete or disable existing tests without recording a reason in `DECISIONS.md`.
3. Do not change the `.env` file or commit secrets.
4. Do not add `busify.db` to `.gitignore` (see M-24 in `DEFECT_REGISTER.md`).
5. Do not add a wildcard to `CORS_ALLOWED_ORIGINS`.
6. Do not change the auth role system without updating `DECISIONS.md`.
7. Do not modify algorithm files (`optimizer.py`, `vrp_solver.py`, `lightgbm_model.py`) unless the sprint explicitly scopes it.
8. Do not merge sprint work into production code without running verification commands and recording results.

---

## Recovery from a failed test

1. Read the full test output.
2. Find the failing line and the assertion.
3. Read the production code at the failing path.
4. Determine: is the test wrong (incorrect expectation) or is the code wrong (regression)?
5. If the code is wrong: fix the code, rerun the test.
6. If the test is wrong: record in `DECISIONS.md` with rationale, update the test.
7. Do not suppress or skip a test without documenting why.

---

## Environment setup (run once per machine)

```powershell
# Backend
cd d:\PROJECTS\BUSify
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # use ROOT requirements.txt, not backend/requirements.txt

# Frontend (already set up — node_modules present)
cd frontend
npm install   # only if node_modules is missing
```

Known issue: target Python is 3.12; global Python may be 3.10. Use a venv to isolate.
