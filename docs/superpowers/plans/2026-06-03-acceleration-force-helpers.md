# Acceleration Force Helpers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the traction, adhesion, resistance, and acceleration-rate formulas from `old/acc3.m` into tested pure Python helpers.

**Architecture:** Add `dragkraft.simulation.acceleration` for force and acceleration-rate functions only. The full per-meter forward acceleration loop remains a later task that can call these helpers.

**Tech Stack:** Python 3.11, numpy, pytest.

---

### Task 1: Acceleration Force Helpers

**Files:**
- Create: `tests/test_acceleration.py`
- Create: `dragkraft/simulation/acceleration.py`

- [ ] **Step 1: Write failing tests**

Create tests covering:

```python
from __future__ import annotations

import numpy as np
import pytest

from dragkraft.simulation.acceleration import (
    adhesion_limited_force,
    acceleration_rate,
    net_force,
    traction_force_type1,
    traction_force_type2,
)


def test_type1_traction_interpolates_start_force_below_start_speed() -> None:
    force = traction_force_type1(
        speed_mps=1.0,
        max_force_n=100.0,
        continuous_power_w=1000.0,
        start_force_n=50.0,
        start_force_max_speed_mps=2.0,
    )

    assert force == pytest.approx(75.0)


def test_type1_traction_uses_power_limit_above_start_speed() -> None:
    force = traction_force_type1(
        speed_mps=10.0,
        max_force_n=200.0,
        continuous_power_w=1000.0,
        start_force_n=50.0,
        start_force_max_speed_mps=2.0,
    )

    assert force == pytest.approx(100.0)


def test_type2_traction_uses_active_linear_interval_and_last_interval_at_cap() -> None:
    intervals = np.array([[0.0, 10.0], [10.0, 20.0]])
    aa = np.array([100.0, 50.0])
    bb = np.array([-2.0, -1.0])

    assert traction_force_type2(5.0, aa, bb, intervals) == pytest.approx(90.0)
    assert traction_force_type2(25.0, aa, bb, intervals) == pytest.approx(25.0)


def test_adhesion_limited_force_applies_acc3_formula() -> None:
    force = adhesion_limited_force(
        requested_force_n=10_000.0,
        speed_mps=2.0,
        adhesion_coefficient=0.6,
        adhesion_mass_kg=76_000.0,
    )

    expected_limit = (2.1 / (2.0 + 12.2) + 0.161) * 0.6 * 76_000.0 * 9.81
    assert force == pytest.approx(min(10_000.0, expected_limit))


def test_net_force_resistance_type1_matches_acc3_davis_formula() -> None:
    force = net_force(
        traction_force_n=1000.0,
        speed_mps=2.0,
        resistance_type=1,
        davis_a_n=10.0,
        davis_b_n_per_mps=3.0,
        davis_c_n_per_mps2=2.0,
        train_mass_kg=100.0,
        dynamic_mass_kg=120.0,
        equivalent_gradient=0.01,
        tunnel_factor=5.0,
        curve_force_n=7.0,
        resistance_factor=3.3,
        wagon_count=1,
        locomotive_mass_kg=20.0,
    )

    expected = 1000.0 - 10.0 - 3.0 * 2.0 - 2.0 * 2.0**2
    expected -= 100.0 * 9.81 * 0.01
    expected -= 5.0 * 2.0**2
    expected -= 7.0
    assert force == pytest.approx(expected)


def test_acceleration_rate_caps_net_force_over_dynamic_mass() -> None:
    assert acceleration_rate(net_force_n=50.0, dynamic_mass_kg=10.0, max_acceleration_mps2=1.5) == pytest.approx(1.5)
```

- [ ] **Step 2: Run tests to verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_acceleration.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'dragkraft.simulation.acceleration'`.

- [ ] **Step 3: Implement minimal helpers**

Create pure functions in `dragkraft/simulation/acceleration.py` matching the formulas asserted by the tests.

- [ ] **Step 4: Run acceleration tests to verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_acceleration.py -v`

Expected: PASS.

- [ ] **Step 5: Run full tests and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
git add docs/superpowers/plans/2026-06-03-acceleration-force-helpers.md tests/test_acceleration.py dragkraft/simulation/acceleration.py
git commit -m "feat: add acceleration force helpers"
```

Expected: all tests pass and a third local commit exists on `refactor/profile-braking-kernels`.
