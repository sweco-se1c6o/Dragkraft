# Profile Braking Kernels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the next pure MATLAB kernels for STH profile creation, tunnel-factor vectors, and backward braking curves.

**Architecture:** Add small pure functions under `dragkraft.simulation.profile` and `dragkraft.simulation.braking`. Keep MATLAB-like one-meter indexing explicit by using padded arrays where index `0` is unused, so positions copied from MATLAB remain readable during parity work.

**Tech Stack:** Python 3.11, numpy, pytest.

---

### Task 1: Profile And Tunnel Helpers

**Files:**
- Create: `tests/test_profile.py`
- Create: `dragkraft/simulation/profile.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_profile.py` with:

```python
from __future__ import annotations

import numpy as np

from dragkraft.simulation.profile import build_sth_profile, build_tunnel_factor


def test_build_sth_profile_uses_matlab_position_slices() -> None:
    result = build_sth_profile(
        speeds_mps=np.array([10.0, 20.0]),
        positions_m=np.array([[0, 3], [3, 5]]),
    )

    assert result.tolist() == [float("inf"), 10.0, 10.0, 10.0, 20.0, 20.0]


def test_build_tunnel_factor_fills_inclusive_legacy_slices() -> None:
    result = build_tunnel_factor(
        tunnel_rows_m=np.array([[2, 4, 7.5]]),
        max_position_m=5,
    )

    assert result.tolist() == [0.0, 0.0, 7.5, 7.5, 7.5, 0.0]
```

- [ ] **Step 2: Run profile tests to verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_profile.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'dragkraft.simulation.profile'`.

- [ ] **Step 3: Implement minimal profile helpers**

Create `dragkraft/simulation/profile.py` with:

```python
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def build_sth_profile(*, speeds_mps: ArrayLike, positions_m: ArrayLike) -> np.ndarray:
    speeds = np.asarray(speeds_mps, dtype=float)
    positions = np.asarray(positions_m, dtype=int)
    max_position = int(np.max(positions))
    profile = np.full(max_position + 1, np.inf, dtype=float)
    for speed, (start, end) in zip(speeds, positions, strict=True):
        profile[start + 1 : end + 1] = speed
    return profile


def build_tunnel_factor(*, tunnel_rows_m: ArrayLike, max_position_m: int) -> np.ndarray:
    rows = np.asarray(tunnel_rows_m, dtype=float)
    factors = np.zeros(int(max_position_m) + 1, dtype=float)
    for start, end, factor in rows:
        factors[int(start) : int(end) + 1] = factor
    return factors
```

- [ ] **Step 4: Run profile tests to verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_profile.py -v`

Expected: PASS.

- [ ] **Step 5: Commit profile helpers**

Run:

```powershell
git add docs/superpowers/plans/2026-06-03-profile-braking-kernels.md tests/test_profile.py dragkraft/simulation/profile.py
git commit -m "feat: add profile envelope helpers"
```

Expected: local commit exists on `refactor/profile-braking-kernels`.

### Task 2: Pure Backward Braking Curve

**Files:**
- Create: `tests/test_braking.py`
- Create: `dragkraft/simulation/braking.py`

- [ ] **Step 1: Write failing braking tests**

Create `tests/test_braking.py` with:

```python
from __future__ import annotations

import numpy as np
import pytest

from dragkraft.simulation.braking import braking_curve


def test_braking_curve_writes_zero_speed_position_as_half_step_speed() -> None:
    result = braking_curve(
        target_position_m=4,
        start_offset_m=0,
        retardation_mps2=np.array([0.2]),
        speed_intervals_mps=np.array([[0.0, 100.0]]),
        target_speed_mps=0.0,
        max_speed_mps=2.0,
        equivalent_gradient=np.zeros(5),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=1.0,
        max_position_m=4,
    )

    assert result[4] == pytest.approx((2 * 0.2) ** 0.5 / 2)


def test_braking_curve_steps_backward_until_speed_exceeds_max_speed() -> None:
    result = braking_curve(
        target_position_m=4,
        start_offset_m=0,
        retardation_mps2=np.array([0.2]),
        speed_intervals_mps=np.array([[0.0, 100.0]]),
        target_speed_mps=0.0,
        max_speed_mps=1.0,
        equivalent_gradient=np.zeros(5),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=1.0,
        max_position_m=4,
    )

    assert np.isfinite(result[4])
    assert np.isfinite(result[3])
    assert np.isfinite(result[2])
    assert np.isinf(result[1])


def test_braking_curve_clamps_gradient_adjusted_deceleration() -> None:
    result = braking_curve(
        target_position_m=2,
        start_offset_m=0,
        retardation_mps2=np.array([0.2]),
        speed_intervals_mps=np.array([[0.0, 100.0]]),
        target_speed_mps=0.0,
        max_speed_mps=0.5,
        equivalent_gradient=np.array([0.0, 0.0, 0.1]),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=0.3,
        max_position_m=2,
    )

    assert result[2] == pytest.approx((2 * 0.3) ** 0.5 / 2)
```

- [ ] **Step 2: Run braking tests to verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_braking.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'dragkraft.simulation.braking'`.

- [ ] **Step 3: Implement minimal braking kernel**

Create `dragkraft/simulation/braking.py` with:

```python
from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike


def braking_curve(
    *,
    target_position_m: int,
    start_offset_m: int,
    retardation_mps2: ArrayLike,
    speed_intervals_mps: ArrayLike,
    target_speed_mps: float,
    max_speed_mps: float,
    equivalent_gradient: ArrayLike,
    min_deceleration_mps2: float,
    max_deceleration_mps2: float,
    max_position_m: int,
) -> np.ndarray:
    curve = np.full(int(max_position_m) + 1, np.inf, dtype=float)
    retardation = np.asarray(retardation_mps2, dtype=float)
    intervals = np.asarray(speed_intervals_mps, dtype=float)
    gradients = np.asarray(equivalent_gradient, dtype=float)
    speed = float(target_speed_mps)
    offset = int(start_offset_m)
    target_position = int(target_position_m)
    while speed <= float(max_speed_mps) + 1.0:
        position = target_position + offset
        if position < 1:
            break
        acceleration = _deceleration_for_speed(speed, retardation, intervals)
        acceleration += 9.82 * gradients[position]
        acceleration = max(acceleration, float(min_deceleration_mps2))
        acceleration = min(acceleration, float(max_deceleration_mps2))
        curve[position] = math.sqrt(2.0 * acceleration) / 2.0 if speed == 0 else speed
        offset -= 1
        next_speed = math.sqrt(2.0 * acceleration + speed**2)
        speed += acceleration / ((speed + next_speed) / 2.0)
    return curve


def _deceleration_for_speed(speed_mps: float, retardation: np.ndarray, intervals: np.ndarray) -> float:
    active = (intervals[:, 1] > speed_mps) & (intervals[:, 0] <= speed_mps)
    if not np.any(active):
        raise ValueError(f"No retardation interval contains speed {speed_mps}")
    return float(retardation[np.flatnonzero(active)[0]])
```

- [ ] **Step 4: Run braking tests to verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_braking.py -v`

Expected: PASS.

- [ ] **Step 5: Run full tests and commit braking kernel**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
git add tests/test_braking.py dragkraft/simulation/braking.py
git commit -m "feat: add pure braking curve kernel"
```

Expected: all tests pass and a second local commit exists on `refactor/profile-braking-kernels`.
