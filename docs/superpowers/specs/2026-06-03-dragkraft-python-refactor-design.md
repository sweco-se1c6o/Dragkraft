# Dragkraft Python Refactor Design

## Approved Direction

Use `PROJECT_DOCUMENTATION_AND_REFACTOR_PLAN.md` as the source design for the MATLAB-to-Python refactor. The first implementation slice creates a Python package, preserves the existing Excel workbook layout exactly, and ports only pure calculation units that can be verified independently before attempting full scenario parity.

## Scope

- Keep `old/` unchanged and Git-ignored.
- Use `old/luleaHamn3.xlsx` locally as the legacy workbook fixture.
- Preserve sheets `DagensProfil`, `NyProfil`, and `SpeedTest`.
- Preserve row 4 headers, row 5 data start, fixed column blocks, first blank row termination, workbook units, formula cached-value behavior, and `99999` curve-radius handling.
- Make the legacy speed override explicit as `speed_override_kmh`.
- Add machine-testable Python modules before plotting or UI work.

## Architecture

The first slice uses a library-first structure:

- `dragkraft.domain`: dataclasses for workbook records and track profile data.
- `dragkraft.io.excel_reader`: fixed-layout Excel parsing with explicit cached-formula checks.
- `dragkraft.units`: small conversion helpers.
- `dragkraft.simulation.resistance`: pure equivalent-gradient and curve-resistance kernels.

The legacy MATLAB files remain the behavioral reference. The Python code avoids global state and returns typed values from pure functions wherever possible.

## Testing

Use `.venv` and `pytest`. Write failing tests before production code. The first tests cover workbook sheet/block counts, speed override behavior, `99999` radius conversion, cached formula protection, equivalent gradient, and curve resistance. End-to-end MATLAB parity remains a later slice after baseline export fixtures exist.

## Repository Constraints

The repository remote is `https://github.com/sweco-se1c6o/Dragkraft.git`. Local Git identity is `sweco-se1c6o <umar.aslam@sweco.se>`. Dependency installs must use trusted hosts, captured in `requirements-dev.txt`.
