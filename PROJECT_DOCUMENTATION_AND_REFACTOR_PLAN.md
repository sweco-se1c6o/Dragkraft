# Dragkraft Legacy Project Documentation and Refactor Plan

## Purpose

This project currently contains a MATLAB-based train performance simulation in the `old` folder. The code reads a fixed-layout Excel workbook, builds a route profile, calculates braking and acceleration constrained by train physics and infrastructure, then reports travel times, timing point passage times, and signal block occupation times.

The refactor goal should be a modern Python implementation that preserves the existing Excel input contract: same workbook structure, same sheets, same columns, same row start, and the same interpretation of distances, speeds, stops, curves, tunnels, timing points, and signal/block data.

## Legacy Inventory

| File | Role |
| --- | --- |
| `old/dragkraft.m` | Main script and orchestration. Reads Excel, defines scenario/train settings, builds route vectors, calculates speed envelope, plots results, and calculates signal block occupation. |
| `old/acc3.m` | Main forward acceleration kernel. Applies tractive effort, power limit, adhesion, train resistance, gradient, tunnel resistance, curve resistance, max acceleration, line speed, and vehicle speed. |
| `old/dec.m` | Backward braking curve kernel for speed reductions and stops. Writes into global `hastighet`. |
| `old/decMB.m` | Backward braking curve kernel for signal/block calculations. Writes into global `mbBreakCurves`. |
| `old/blockBelagg.m` | Calculates signal/block booking, arrival, and release times using MB braking curves. |
| `old/ekvivalentLutning.m` | Calculates equivalent gradient at each meter by averaging gradient over the train length. |
| `old/kurvmotstand.m` | Calculates curve resistance at each meter using a Rockl/OpenTrack-style radius formula, averaged over train length when multiple curve intervals are active. |
| `old/makeSTHprofile.m` | Fills the base speed profile row in global `hastighet` from speed limit segments. |
| `old/plotProfile.m` | Plots STH, simulated speed, and optional braking curves. |
| `old/acc2.m` | Older/debug acceleration function. It is not used by the active main script. |
| `old/luleaHamn3.xlsx` | Fixed-layout input workbook with sheets `DagensProfil`, `NyProfil`, and `SpeedTest`. |

## Current Default Scenario

The active script uses:

| Setting | Current value |
| --- | --- |
| Workbook | `old/luleaHamn3.xlsx` |
| Sheet | `NyProfil` |
| Direction | `flipProfiles = true` |
| `maxHastighet` | `40` km/h |
| `antalExtraVagnar` | `21` |
| `altitudeAtStart` | `3.416` m |
| `kortidsmarginal` | `1.00` |
| Stop distance settings | `tagLangdsFordrojing = true`, `avstandForeSignal = true`, `tavstand = true` |
| Freight signal advance constants | `tavfs = 37.7`, `tavfs2 = 26`, `tavfs2m = 355.75`, `swSpeed = 110/3.6` |
| Braking tolerance | `vTol = 0.5/3.6` m/s |
| Signal minimum deceleration | `minDecSignal = 0.13` m/s2 |

Important: `trainType = 20` is set, but the active `switch trainType` is commented out. The executable train definition is effectively the first active freight/train block near the top of `dragkraft.m`.

Current active train definition:

| Parameter | Current behavior |
| --- | --- |
| Locomotives | `antalLok = 1` |
| Locomotive mass | `76e3` kg |
| Wagon mass | `antalExtraVagnar * 84e3` kg |
| Total train mass | `massaLok + massaVagnar` |
| Dynamic mass | `1.06 * tagMassa` |
| Adhesion mass | `massaLok` |
| Adhesion coefficient | `0.6` |
| Train length | `antalLok * 15.4 + antalExtraVagnar * 11` m |
| Resistance type | `1`, Davis formula |
| Traction model | `2`, piecewise linear force by speed interval |
| Vehicle speed cap | `60/3.6` m/s |
| Acceleration cap | `1` m/s2 |
| Service braking limits | `minDec = 0.15`, `maxDec = 0.7` m/s2 |

Also important: after reading the workbook, the script overwrites the speed column with `maxHastighet`:

```matlab
sthData = cell2mat(r(5:end, 2:4));
sthData(:, end) = maxHastighet
```

For parity, the Python version should make this an explicit scenario option, for example `speed_override_kmh: 40`. The workbook column should still be parsed because other scenarios may need to use it directly.

## Excel Input Contract

All workbook sheets inspected have the same layout. Row 4 contains headers. Data starts at row 5. Each data block is read until the first blank/NaN row in that block. The modern reader must preserve this behavior.

| Logical data | Excel columns | MATLAB columns | Required fields |
| --- | --- | --- | --- |
| Speed limits, STH | `B:D` | `2:4` | from km, to km, speed km/h |
| Gradients | `G:I` | `7:9` | from km, to km, gradient per mille |
| Tunnels | `L:N` | `12:14` | from km, to km, tunnel factor |
| Timing points | `Q:R` | `17:18` | position km, name |
| Stops | `T:V` | `20:22` | stop position km, name, stop time seconds |
| Curves | `Y:AA` | `25:27` | from km, to km, radius m |
| Signals / MB | `AD:AI` | `30:35` | signal position km, name, release speed km/h, overlap m, release time s, setting time s |

Workbook sheets:

| Sheet | Speed rows | Gradient rows | Tunnel rows | Timing rows | Stop rows | Curve rows | Signal rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `DagensProfil` | 4 | 18 | 1 | 2 | 1 | 26 | 2 |
| `NyProfil` | 4 | 18 | 1 | 2 | 1 | 26 | 2 |
| `SpeedTest` | 4 | 2 | 1 | 2 | 0 | 3 | 2 |

Workbook notes:

- Some input cells contain Excel formulas, especially chained `from = previous to` cells.
- MATLAB `xlsread` on Windows generally receives evaluated values from Excel. In Python, use `openpyxl` or a similar reader with cached formula values, and validate that formula cells have cached values.
- Distances in the workbook are in kilometers. The simulation converts to rounded meter positions with `round((km - route_start_km) * 1000)`.
- Speed is converted from km/h to m/s with `/ 3.6`.
- Gradient is converted from per mille to dimensionless slope with `/ 1000`.
- Curve radius `99999` is treated as straight track and converted to infinity.
- Names are read from adjacent columns only for the number of numeric rows found in the primary position column.

## Legacy Data Flow

The active MATLAB flow is:

1. Select scenario settings in `dragkraft.m`.
2. Read workbook sheet with `xlsread`.
3. Read fixed column blocks from row 5 until first blank/NaN row.
4. Override all speed limit values with `maxHastighet`.
5. Convert route quantities from workbook units to simulation units.
6. Optionally flip the profile direction:
   - Speed segments are reversed.
   - Gradient positions are reversed and gradient signs are inverted.
   - Curves, stops, signals, timing points, and tunnels are reversed.
7. Define train mass, length, traction, braking, resistance, adhesion, and signal constants.
8. Allocate global `hastighet`, a matrix of candidate speed profiles.
9. Build `tunnelFactor`, a per-meter vector.
10. Fill the base STH profile using `makeSTHprofile`.
11. Calculate equivalent gradient per meter with `ekvivalentLutning`.
12. Calculate curve resistance per meter with `kurvmotstand`.
13. For each speed limit transition:
    - If speed increases, optionally hold previous speed over train length.
    - If speed decreases, place an advance-distance offset and calculate a braking curve with `dec`.
14. For each stop, calculate a braking curve to zero speed with `dec`.
15. Take the minimum across candidate rows to get an initial speed envelope.
16. Calculate initial time per meter and acceleration/deceleration hint vector.
17. Run `acc3` forward from the start to build the achievable acceleration profile.
18. Take the minimum across candidate rows again and cap by vehicle speed.
19. Calculate `tid = 1 ./ hastighetsprofil`, add stop dwell time, and cumulative time `tidc`.
20. Plot profile, timing, and acceleration figures.
21. Calculate signal/block booking, arrival, and release times with `blockBelagg`.

## Core Numerical Behavior

### One-meter discretization

The simulation is position-stepped at one meter resolution. MATLAB positions are effectively used as 1-based array indexes. In Python, either allocate arrays with a dummy element at index 0 or implement a consistent conversion layer. For parity, a padded array is safest during the first port.

### Speed envelope

The final speed profile is a minimum envelope:

```text
final_speed[position] = min(all candidate speed constraints at that position)
```

Candidate rows include:

- Base speed limit profile.
- Braking curves for STH reductions.
- Braking curves for stops.
- Forward acceleration profile.

### Braking

`dec.m` and `decMB.m` integrate backward from a target position and target speed. Deceleration is selected by speed interval:

```text
a = braking_value_for_speed + 9.82 * equivalent_gradient[position]
a = clamp(a, minDec, maxDec)
v_next = v + a / ((v + sqrt(2*a + v^2)) / 2)
```

For `v == 0`, the stored speed at the position is `sqrt(2*a)/2`.

### Acceleration

`acc3.m` integrates forward. It calculates tractive force by either:

- Type 1: minimum of max tractive force and continuous power divided by speed, with a low-speed start force interpolation.
- Type 2: piecewise linear tractive force over speed intervals.

Then it applies adhesion:

```text
adhesion_force = (2.1 / (v + 12.2) + 0.161) * adhesionCoef * adhesionMass * 9.81
tractive_force = min(tractive_force, adhesion_force)
```

Then it subtracts resistance:

- Resistance type 1: Davis `A + B*v + C*v^2`.
- Resistance type 2: Strahl-style formula.
- Resistance type 3: mixed locomotive plus wagons formula.

All active resistance modes also subtract:

- Grade force: `tagMassa * 9.81 * ekvLutning[position]`
- Tunnel resistance: `tunnelFactor[position] * v^2`
- Curve resistance: `kurvKraft[position]`

Acceleration is:

```text
a = min(net_force / tagDynMassa, maxAcc)
```

Speed is advanced per meter and constrained by:

- Current target speed envelope.
- Vehicle maximum speed.
- Optional minimum time to hold speed behavior.

### Equivalent gradient

`ekvivalentLutning.m` computes the weighted average gradient over the interval:

```text
[current_position - train_length, current_position]
```

This means the gradient is train-length aware, not just a point lookup.

### Curve resistance

`kurvmotstand.m` uses a radius-dependent formula:

```text
if radius < 300:
    force = 4.91 / (radius - 30) * train_mass
else:
    force = 6.3 / (radius - 55) * train_mass
```

When the train spans multiple curve intervals, the force is weighted over the active train-length interval.

### Signal/block occupation

`blockBelagg.m` calculates five columns per signal:

| Column | Meaning |
| --- | --- |
| 1 | Speed difference at first intersection between train speed profile and MB braking curve. |
| 2 | Position index of that intersection. |
| 3 | Booking/pre-reservation time. If no intersection is found, uses arrival time minus `reserveBeforeArrrival`. |
| 4 | Arrival time at signal. |
| 5 | Release time after signal, train length, overlap, and release delay have passed. |

The MB braking curve is raised to at least the configured release speed:

```matlab
mbBreakCurves(kbp, :) = max(mbReleaseSpeed(kbp)/3.6, mbBreakCurves(kbp, :));
```

## Current Outputs

The legacy script primarily outputs to the MATLAB console and figures:

- Total travel time in seconds.
- Timing point passage times.
- Timing point names with passage times.
- Difference between last and first timing point.
- Signal/block booking, arrival, and release times.
- Figures for profile, timing, acceleration, equivalent gradient, curve resistance, and optional braking curves.

It does not currently write stable machine-readable output files. The refactor should add CSV/JSON outputs while preserving plots.

## Key Refactor Risks

1. Hidden Excel assumptions: fixed columns, row 5 start, first blank row termination, formulas, and cached values must be preserved.
2. Direction flipping: flipping reverses several arrays and inverts gradients. This is easy to get subtly wrong.
3. MATLAB indexing: the code uses rounded meter positions directly as 1-based indexes.
4. Global mutable arrays: `hastighet` and `mbBreakCurves` are global side effects today.
5. Hardcoded active train: `trainType` looks configurable but is not actually used by the active executable path.
6. Speed override: workbook speeds are parsed but then overwritten by `maxHastighet`.
7. Plotting mixed with calculation: plotting calls and figures are embedded in numerical functions, especially `acc3`.
8. Formula caches: Python readers usually do not calculate Excel formulas. The workbook must be pre-calculated or formulas must be evaluated separately.
9. Boundary safety: signal release uses `mbPos + round(tagLangd) + mbOverlap`; this can exceed array bounds for future inputs if not validated.
10. Legacy comments preserve many vehicle definitions, but much of that section is inactive. The refactor should separate active behavior from historical/reference definitions.

## Proposed Python Stack

Recommended first version:

- Python 3.11 or newer.
- `numpy` for numerical arrays.
- `openpyxl` for fixed-layout Excel reading.
- `pandas` for tabular outputs and optional input diagnostics.
- `matplotlib` for parity plots.
- `pydantic` or standard `dataclasses` for typed domain models. Start with `dataclasses` unless validation needs become heavier.
- `typer` for a simple CLI.
- `pytest` for unit, fixture, and golden-master tests.
- `ruff` for linting and formatting.
- `pyproject.toml` for packaging.

Optional later UI:

- Streamlit if the goal is a fast engineering dashboard.
- FastAPI plus a frontend if the goal is a multi-user web application.

The first refactor should be a library plus CLI, not a UI-first rewrite. That keeps the numerical behavior testable.

## Proposed Architecture

```text
dragkraft/
  __init__.py
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
    legacy_cases.py
  reporting/
    plots.py
tests/
  fixtures/
  test_excel_reader.py
  test_equivalent_gradient.py
  test_curve_resistance.py
  test_braking.py
  test_acceleration.py
  test_end_to_end_legacy_nyprofil.py
```

### Domain models

Use typed models for:

- `SpeedLimitSegment(from_km, to_km, speed_kmh)`
- `GradientSegment(from_km, to_km, gradient_promille)`
- `TunnelSegment(from_km, to_km, factor)`
- `CurveSegment(from_km, to_km, radius_m)`
- `TimingPoint(position_km, name)`
- `Stop(position_km, name, stop_time_s)`
- `SignalBlock(position_km, name, release_speed_kmh, overlap_m, release_time_s, setting_time_s)`
- `TrackProfile(...)`
- `TrainConfig(...)`
- `SimulationSettings(...)`
- `SimulationResult(speed_mps, time_s_per_m, cumulative_time_s, timing_passages, block_times, diagnostics)`

### Module responsibilities

| Module | Responsibility |
| --- | --- |
| `io.excel_reader` | Read workbook using the legacy fixed ranges and row termination rules. Return domain objects in workbook units. |
| `units` | Unit conversions and position indexing helpers. |
| `simulation.profile` | Convert route data into one-meter vectors, apply optional flip, and build base STH profile. |
| `simulation.resistance` | Equivalent gradient, curve resistance, tunnel factor, and train resistance formulas. |
| `simulation.braking` | Pure braking curve generation for speed reductions, stops, and MB curves. |
| `simulation.acceleration` | Pure acceleration generation with traction, adhesion, resistance, and speed caps. |
| `simulation.blocks` | Signal/block booking, arrival, and release calculations. |
| `simulation.orchestrator` | Sequence the full simulation. No plotting and no Excel-specific logic. |
| `vehicles.catalog` | Active train definitions and old train cases converted to named configs. |
| `reporting.plots` | Matplotlib plots from `SimulationResult`. |
| `io.outputs` | Write CSV/JSON summaries for timings, speed profiles, and block occupation. |
| `cli` | Command-line entrypoint. |

## Suggested CLI

Example:

```powershell
python -m dragkraft run old/luleaHamn3.xlsx --sheet NyProfil --train legacy-freight-20 --max-speed-kmh 40 --flip --out runs/nyprofil
```

Expected outputs:

- `runs/nyprofil/summary.json`
- `runs/nyprofil/timing_points.csv`
- `runs/nyprofil/block_occupation.csv`
- `runs/nyprofil/speed_profile.csv`
- `runs/nyprofil/profile.png`
- `runs/nyprofil/acceleration.png`

## Migration Plan

### Phase 1: Baseline and documentation

1. Keep the legacy files unchanged.
2. Capture MATLAB baseline outputs for the current default scenario:
   - Total time.
   - Timing point passage times.
   - `mbTid` block table.
   - Final `hastighetsprofil`.
   - `tidc`.
   - `ekvLutning`.
   - `kurvKraft`.
3. Save those as golden fixtures in `tests/fixtures/legacy_nyprofil/`.
4. Add this project document to the repo.

MATLAB R2015a appears to be installed locally, so the baseline can likely be produced with a small non-invasive wrapper script or by adding temporary export statements in a copied script. Do not edit the original baseline source destructively.

### Phase 2: Project scaffold

1. Create `pyproject.toml`.
2. Add package structure under `dragkraft/`.
3. Add `pytest` tests and a smoke CLI.
4. Add fixture workbook path handling.

### Phase 3: Excel reader

1. Implement fixed block reads for `B:D`, `G:I`, `L:N`, `Q:R`, `T:V`, `Y:AA`, and `AD:AI`.
2. Validate row 5 start and first blank row termination.
3. Validate required numeric columns and names.
4. Detect formula cells without cached values and fail with a clear error.
5. Add tests against all three workbook sheets.

### Phase 4: Pure numerical kernels

Port and test these in isolation:

1. `makeSTHprofile` -> base speed profile builder.
2. `ekvivalentLutning` -> equivalent gradient vector.
3. `kurvmotstand` -> curve resistance vector.
4. `dec` and `decMB` -> one pure braking curve function with output target array supplied by caller.
5. `acc3` -> pure acceleration function returning an acceleration speed candidate vector.
6. `blockBelagg` -> pure block occupation function returning a table/model.

### Phase 5: Orchestrator parity

1. Implement full sequence from Excel to final result.
2. Preserve one-meter discretization and MATLAB-like indexing.
3. Preserve current default behavior, including speed override and direction flip.
4. Compare against golden MATLAB baseline with tolerances:
   - Speeds: within about `0.01` m/s initially, tightened after debugging.
   - Timing point times: within `1` second.
   - Block times: within `1` second.
   - Total time: within `1` second.

### Phase 6: Reporting

1. Add CSV/JSON machine-readable outputs.
2. Recreate core plots in `matplotlib`.
3. Keep plotting outside numerical functions.
4. Include diagnostics such as route length, train config, input sheet, speed override, and whether formulas were cached.

### Phase 7: Cleanup and extension

1. Move inactive train definitions into `vehicles/legacy_cases.py` or config files.
2. Add named scenario files, for example `scenarios/nyprofil_freight_40.yaml`.
3. Add stronger validation for future Excel changes.
4. Optionally build a Streamlit or web UI after the CLI/library is stable.

## Acceptance Criteria

The refactor should be considered successful when:

1. The Python CLI can run the existing `old/luleaHamn3.xlsx` workbook without changing its layout.
2. The default `NyProfil` scenario reproduces MATLAB baseline timings and block occupation within agreed tolerances.
3. The Excel reader supports `DagensProfil`, `NyProfil`, and `SpeedTest`.
4. Numerical functions are pure and covered by tests.
5. The project has stable CSV/JSON outputs in addition to plots.
6. Train, route, scenario, and reporting concerns are separated.
7. The legacy files remain available for comparison until parity is signed off.

## Recommended Next Step

Create a MATLAB baseline export for the current default scenario, then scaffold the Python package and implement the Excel reader first. The Excel reader is the highest-leverage starting point because it locks down the user-facing data contract before any numerical rewrite begins.
