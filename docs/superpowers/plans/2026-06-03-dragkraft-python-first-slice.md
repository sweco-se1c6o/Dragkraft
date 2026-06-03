# Dragkraft Python First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first tested Python slice of the Dragkraft MATLAB refactor while preserving the Excel input contract.

**Architecture:** Build a library-first package with dataclass domain models, a fixed-layout Excel reader, unit conversion helpers, and two pure numerical resistance kernels. Keep the legacy `old/` directory local-only and unchanged.

**Tech Stack:** Python 3.11, numpy, openpyxl, pytest, matplotlib, pandas, setuptools.

---

### Task 1: Repository And Environment Foundation

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Create: `docs/superpowers/specs/2026-06-03-dragkraft-python-refactor-design.md`
- Create: `docs/superpowers/plans/2026-06-03-dragkraft-python-first-slice.md`

- [ ] **Step 1: Initialize Git repository**

Run: `git init`

Expected: repository metadata exists in `.git/`.

- [ ] **Step 2: Set local Git identity and remote**

Run:

```powershell
git config user.name sweco-se1c6o
git config user.email umar.aslam@sweco.se
git remote add origin https://github.com/sweco-se1c6o/Dragkraft.git
```

Expected: `git config user.name`, `git config user.email`, and `git remote -v` show the requested values.

- [ ] **Step 3: Create venv and install dependencies**

Run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org numpy openpyxl pytest matplotlib pandas
```

Expected: `.venv\Scripts\python.exe -m pip list` includes `numpy`, `openpyxl`, and `pytest`.

### Task 2: Excel Reader Contract

**Files:**
- Create: `tests/test_excel_reader.py`
- Create: `dragkraft/__init__.py`
- Create: `dragkraft/domain/__init__.py`
- Create: `dragkraft/domain/track.py`
- Create: `dragkraft/io/__init__.py`
- Create: `dragkraft/io/excel_reader.py`

- [ ] **Step 1: Write failing tests**

Test code checks the three legacy workbook sheets, exact block row counts, optional speed override, radius `99999` conversion to infinity, and formula detection.

- [ ] **Step 2: Run tests to verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_excel_reader.py -v`

Expected: FAIL because `dragkraft.io.excel_reader` does not exist yet.

- [ ] **Step 3: Implement minimal reader**

Create dataclasses for fixed workbook blocks and implement `read_track_profile(workbook_path, sheet_name, speed_override_kmh=None)`.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_excel_reader.py -v`

Expected: PASS.

### Task 3: Unit Helpers And Resistance Kernels

**Files:**
- Create: `tests/test_units.py`
- Create: `tests/test_resistance.py`
- Create: `dragkraft/units.py`
- Create: `dragkraft/simulation/__init__.py`
- Create: `dragkraft/simulation/resistance.py`

- [ ] **Step 1: Write failing tests**

Test code covers kilometers-to-rounded-meter conversion, km/h to m/s conversion, equivalent gradient over train length, curve resistance for single and mixed intervals, and infinite radius producing zero resistance.

- [ ] **Step 2: Run tests to verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_units.py tests/test_resistance.py -v`

Expected: FAIL because helper and resistance modules do not exist yet.

- [ ] **Step 3: Implement minimal helpers and kernels**

Create pure functions matching the MATLAB formulas and one-meter indexing assumptions.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_units.py tests/test_resistance.py -v`

Expected: PASS.

### Task 4: Verification And Commit

**Files:**
- All files changed in Tasks 1-3.

- [ ] **Step 1: Run full verification**

Run: `.\.venv\Scripts\python.exe -m pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Inspect Git status**

Run: `git status --short`

Expected: only intentional source, tests, config, docs, and root markdown files are tracked or staged. `old/` and `.venv/` are ignored.

- [ ] **Step 3: Commit**

Run:

```powershell
git add .gitignore pyproject.toml requirements-dev.txt PROJECT_DOCUMENTATION_AND_REFACTOR_PLAN.md NEXT_SESSION_HANDOFF.md docs dragkraft tests
git commit -m "feat: scaffold tested dragkraft python package"
```

Expected: a local commit exists and can later be pushed to `origin`.
