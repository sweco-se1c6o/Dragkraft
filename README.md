# Dragkraft

Python refactor of a legacy MATLAB train performance simulation for Dragkraft.

The goal is numerical parity with the MATLAB implementation while preserving the existing Excel input contract exactly. The current Python code is an incremental refactor: core input parsing and several pure numerical kernels are implemented and tested, but the full end-to-end simulation is not complete yet.

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

Still pending:

- MATLAB baseline export fixtures.
- Full orchestrator parity against MATLAB baseline.
- CLI entrypoint.
- End-to-end parity tests against MATLAB.

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

## Development Notes

- Preserve the Excel workbook layout exactly.
- Keep `old/` unchanged and local-only.
- Prefer pure numerical functions with tests before adding orchestration.
- Preserve MATLAB one-meter indexing behavior during parity work.
- Do not treat this refactor as complete until Python reproduces the MATLAB baseline for the default `NyProfil` scenario within agreed tolerances.
