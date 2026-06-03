# Dragkraft

Python refactor of a legacy MATLAB train performance simulation for Dragkraft.

The goal is numerical parity with the MATLAB implementation while preserving the existing Excel input contract exactly. The current Python code can run the default legacy `NyProfil` scenario, write CSV/JSON outputs, and compare that run against captured MATLAB baseline fixtures.

## Current Status

Implemented:

- Fixed-layout Excel reader for the legacy workbook sheets.
- Unit conversion helpers for speed, gradient, and rounded meter positions.
- Base STH profile and tunnel-factor vector helpers.
- Equivalent-gradient and curve-resistance kernels.
- Backward braking curve kernel shared by `dec.m` and `decMB.m`.
- Acceleration force helpers from `acc3.m`.
- Forward acceleration stepping loop.
- Active legacy freight train and default `NyProfil` scenario config.
- Initial speed-envelope builder for STH transitions and stops.
- Route preparation for tunnel, equivalent-gradient, and curve-resistance vectors.
- Acceleration callback wiring traction, adhesion, resistance, gradient, tunnel, and curve terms.
- Pure signal/block occupation kernel for MB braking curves, booking, arrival, and release times.
- Simulation result includes timing-point passages and signal/block occupation rows.
- CSV/JSON output writer for summary, timing points, block occupation, and speed profile.
- CLI entrypoint for running a workbook and writing outputs.
- MATLAB baseline fixtures for the default `NyProfil` scenario.
- End-to-end parity test for default `NyProfil` timing, speed, gradient, curve force, and block occupation.

Still pending:

- Additional scenario parity coverage beyond the default `NyProfil` case.
- Optional plotting/reporting polish.

## Excel Input Contract

The reader preserves the legacy workbook layout:

- Sheets: `DagensProfil`, `NyProfil`, `SpeedTest`.
- Headers on row 4.
- Data starts on row 5.
- Each block is read until the first blank row in that block.
- Fixed column blocks:
  - `B:D`: speed limits
  - `G:I`: gradients
  - `L:N`: tunnels
  - `Q:R`: timing points
  - `T:V`: stops
  - `Y:AA`: curves
  - `AD:AI`: signal/block data

Workbook distances are in kilometers and converted to rounded meter positions. Speeds are converted from km/h to m/s. Gradients are converted from promille to dimensionless slope. Curve radius `99999` means straight track and is converted to infinity.

## Repository Layout

```text
dragkraft/
  __main__.py
  cli.py
  io/
    excel_reader.py
    outputs.py
  domain/
    track.py
    train.py
    scenario.py
  simulation/
    acceleration.py
    blocks.py
    braking.py
    envelope.py
    orchestrator.py
    profile.py
    route.py
    resistance.py
  units.py
  vehicles/
    legacy_cases.py
tests/
docs/tools/
```

The legacy MATLAB files and workbook are kept locally in `old/`, but that folder is intentionally Git-ignored.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install development dependencies using the trusted-host configuration in `requirements-dev.txt`:

```powershell
python -m pip install -r requirements-dev.txt
```

## Tests

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Some Excel-reader tests use the local legacy workbook at `old/luleaHamn3.xlsx`. If that local-only workbook is absent, those tests are skipped.

The default `NyProfil` parity test uses tracked MATLAB baseline CSV fixtures under `tests/fixtures/matlab_nyprofil_default/`. Re-export them with MATLAB when the legacy reference changes. First prepare a temp legacy run directory with an `xlsread` shim, then run the MATLAB command printed by the script:

```powershell
.\.venv\Scripts\python.exe tools\prepare_matlab_baseline_run.py
```

## CLI

Run the default legacy-style scenario and write CSV/JSON outputs:

```powershell
.\.venv\Scripts\python.exe -m dragkraft run old/luleaHamn3.xlsx --sheet NyProfil --train legacy-freight-20 --max-speed-kmh 40 --flip --out runs/nyprofil
```

## Development Notes

- Preserve the Excel workbook layout exactly.
- Keep `old/` unchanged and local-only.
- Prefer pure numerical functions with tests before adding orchestration.
- Preserve MATLAB one-meter indexing behavior during parity work.
- Do not treat this refactor as complete until Python reproduces the MATLAB baseline for the default `NyProfil` scenario within agreed tolerances.
