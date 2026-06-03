# Next Session Handoff

## Start Here

Use the Superpowers workflows for this project. Begin by invoking the relevant skill workflow for structured development, then use planning, test-driven development, systematic debugging, code review, and verification workflows as needed while refactoring the MATLAB code.

Suggested opening instruction for the next session:

```text
Use Superpowers for this work. Start by understanding the project handoff and the existing MATLAB code, then plan and implement the MATLAB-to-Python refactor carefully with tests and verification.
```

## Project Summary

This project is a legacy MATLAB train performance simulation that should be refactored into a modern Python stack while preserving the existing Excel input format exactly.

The current source is in `old/`. The main script is `old/dragkraft.m`. It reads `old/luleaHamn3.xlsx`, builds a railway route profile, calculates speed limits, braking curves, acceleration, travel times, timing point passage times, and signal block occupation times.

The main project analysis and refactor plan has already been written in:

```text
PROJECT_DOCUMENTATION_AND_REFACTOR_PLAN.md
```

Read that document first before changing code.

## Important Legacy Files

- `old/dragkraft.m`: main MATLAB orchestration script.
- `old/acc3.m`: forward acceleration calculation.
- `old/dec.m`: backward braking curve calculation for speed reductions and stops.
- `old/decMB.m`: backward braking curve calculation for signal/block curves.
- `old/blockBelagg.m`: signal/block booking, arrival, and release time calculation.
- `old/ekvivalentLutning.m`: equivalent gradient over train length.
- `old/kurvmotstand.m`: curve resistance over train length.
- `old/makeSTHprofile.m`: base speed profile builder.
- `old/plotProfile.m`: plotting.
- `old/luleaHamn3.xlsx`: required Excel input workbook.

## Excel Contract To Preserve

The Python refactor must keep the workbook layout unchanged:

- Sheets: `DagensProfil`, `NyProfil`, `SpeedTest`.
- Headers are on row 4.
- Data starts at row 5.
- Each block is read until the first blank row in that block.
- Distances are in kilometers and converted to rounded meter positions.
- Speeds are in km/h and converted to m/s.
- Gradients are in promille and converted to dimensionless slope.
- Curve radius `99999` means straight track and becomes infinity.

Fixed column blocks:

- `B:D`: speed limits.
- `G:I`: gradients.
- `L:N`: tunnels.
- `Q:R`: timing points.
- `T:V`: stops.
- `Y:AA`: curves.
- `AD:AI`: signal/block data.

## Current Default Scenario

The active MATLAB run currently uses:

- Workbook: `old/luleaHamn3.xlsx`
- Sheet: `NyProfil`
- `flipProfiles = true`
- `maxHastighet = 40`
- `antalExtraVagnar = 21`
- `kortidsmarginal = 1.00`

Important detail: the workbook speed column is read, but then overwritten in MATLAB:

```matlab
sthData(:, end) = maxHastighet
```

In Python, make this an explicit scenario option such as `speed_override_kmh`.

Another important detail: `trainType = 20` is set, but the active `switch trainType` is commented out. The currently executed train configuration is effectively hardcoded near the top of `dragkraft.m`.

## Recommended Next Steps

1. Read `PROJECT_DOCUMENTATION_AND_REFACTOR_PLAN.md`.
2. Read the active executable sections of `old/dragkraft.m`, especially Excel parsing, profile flipping, train definition, and lines around the simulation sequence.
3. Create a MATLAB baseline export for the current default scenario before rewriting behavior.
4. Scaffold a Python package with a CLI and tests.
5. Implement the Excel reader first, preserving the legacy fixed layout.
6. Port the pure numerical kernels one at a time:
   - base STH profile
   - equivalent gradient
   - curve resistance
   - braking curves
   - acceleration
   - signal/block occupation
7. Compare Python results against the MATLAB baseline.

## Testing Strategy

Use test-driven development. The safest sequence is:

1. Unit tests for the Excel reader using all workbook sheets.
2. Unit tests for `ekvivalentLutning` and `kurvmotstand`.
3. Unit tests for braking curve generation.
4. Unit tests for acceleration force/resistance calculations.
5. End-to-end golden test for the current `NyProfil` scenario.

The first version should prioritize numerical parity over UI or extra features.

## Architecture Direction

Target Python structure:

```text
dragkraft/
  cli.py
  config.py
  units.py
  io/
    excel_reader.py
    outputs.py
  domain/
    track.py
    train.py
    scenario.py
    result.py
  simulation/
    orchestrator.py
    profile.py
    braking.py
    acceleration.py
    resistance.py
    blocks.py
  vehicles/
    catalog.py
  reporting/
    plots.py
tests/
```

Use `numpy`, `openpyxl`, `pytest`, and `matplotlib` initially. Add `pandas`, `typer`, or a UI only when the core simulation is stable.

## Working Rules

- Do not alter the Excel layout.
- Do not delete or rewrite the legacy MATLAB files during the first refactor phase.
- Preserve one-meter discretization and MATLAB indexing behavior carefully.
- Separate calculation from plotting.
- Avoid global state in Python.
- Keep outputs machine-readable: JSON/CSV plus optional plots.
- Verify every numerical port against either small unit fixtures or the MATLAB baseline.

