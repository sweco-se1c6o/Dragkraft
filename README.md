# Dragkraft

Dragkraft is a train performance simulation. It reads a track profile from an
Excel workbook, integrates train motion at one-meter resolution under traction,
adhesion, resistance, gradient, tunnel, and curve constraints, and reports
travel times, timing-point passages, and signal/block occupation. Results can be
written to CSV/JSON or explored interactively in a Dash dashboard.

## Features

- Fixed-layout Excel reader for the workbook track sheets.
- Unit conversion helpers for speed, gradient, and rounded meter positions.
- Base STH profile and tunnel-factor vector helpers.
- Equivalent-gradient and curve-resistance kernels.
- Backward braking curve kernel.
- Acceleration force helpers (traction, adhesion, resistance) and the forward
  per-meter acceleration loop.
- Standard freight train and a default `NyProfil` scenario configuration.
- Initial speed-envelope builder for STH transitions and stops.
- Route preparation for tunnel, equivalent-gradient, and curve-resistance vectors.
- Pure signal/block occupation kernel for braking curves, booking, arrival, and
  release times.
- Simulation results include timing-point passages and signal/block occupation.
- Graceful handling of an over-heavy consist: the run returns a partial result
  up to the stall position instead of failing.
- CSV/JSON output writer for summary, timing points, block occupation, and the
  speed profile.
- CLI for running a workbook and a Dash dashboard for interactive runs and
  scenario comparison.

## Excel Input Contract

The reader expects a fixed workbook layout:

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

Workbook distances are in kilometers and converted to rounded meter positions.
Speeds are converted from km/h to m/s. Gradients are converted from promille to
dimensionless slope. Curve radius `99999` means straight track and is converted
to infinity.

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
    result.py
  simulation/
    acceleration.py
    blocks.py
    braking.py
    envelope.py
    orchestrator.py
    profile.py
    route.py
    resistance.py
  dashboard/
    app.py
    callbacks.py
    figures.py
    forms.py
    results.py
    uploads.py
  units.py
  vehicles/
    scenarios.py
tests/
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install development dependencies (the trusted-host flags in
`requirements-dev.txt` are needed behind a TLS-intercepting proxy):

```powershell
python -m pip install -r requirements-dev.txt
```

## Tests

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Some tests use a local workbook at `old/luleaHamn3.xlsx`. If that local-only
workbook is absent, those tests are skipped. The default `NyProfil` end-to-end
test compares against tracked baseline CSV fixtures under
`tests/fixtures/default_scenario/`.

## CLI

Run the default scenario and write CSV/JSON outputs:

```powershell
.\.venv\Scripts\python.exe -m dragkraft run old/luleaHamn3.xlsx --sheet NyProfil --train freight --max-speed-kmh 40 --flip --out runs/nyprofil
```

Launch the interactive dashboard:

```powershell
.\.venv\Scripts\python.exe -m dragkraft dashboard
```

Then open http://127.0.0.1:8050 in a browser.
