# Forward Acceleration Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the per-meter forward acceleration stepping behavior from `old/acc3.m` into a pure Python loop.

**Architecture:** Add `forward_acceleration_profile` to `dragkraft.simulation.acceleration`. The function receives an acceleration callback so traction/resistance formulas remain testable separately and the stepping loop can later be used by the orchestrator.

**Tech Stack:** Python 3.11, numpy, pytest.

---

### Task 1: Forward Acceleration Profile

**Files:**
- Modify: `tests/test_acceleration.py`
- Modify: `dragkraft/simulation/acceleration.py`

- [ ] **Step 1: Write failing tests**

Add tests that import `forward_acceleration_profile` and assert:

```python
def test_forward_acceleration_profile_writes_zero_speed_half_step_then_average_speed() -> None:
    result = forward_acceleration_profile(
        start_position_m=1,
        start_speed_mps=0.0,
        max_position_m=2,
        speed_envelope_mps=np.full(3, np.inf),
        vehicle_max_speed_mps=np.inf,
        acceleration_at=lambda position, speed: 1.0,
    )

    assert result[1] == pytest.approx(2**0.5 / 2)
    assert result[2] == pytest.approx(2**0.5 / 2)


def test_forward_acceleration_profile_uses_speed_envelope_for_next_step() -> None:
    envelope = np.full(4, np.inf)
    envelope[2] = 0.5
    result = forward_acceleration_profile(
        start_position_m=1,
        start_speed_mps=0.0,
        max_position_m=3,
        speed_envelope_mps=envelope,
        vehicle_max_speed_mps=np.inf,
        acceleration_at=lambda position, speed: 1.0,
    )

    assert result[3] == pytest.approx(1.0)
```

- [ ] **Step 2: Run tests to verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_acceleration.py -v`

Expected: FAIL with `ImportError: cannot import name 'forward_acceleration_profile'`.

- [ ] **Step 3: Implement minimal loop**

Add `forward_acceleration_profile` to `dragkraft/simulation/acceleration.py` using the same update order as `acc3.m`: calculate acceleration, write current profile value, increment position, compute `v1`, compute average `v2`, then cap the next speed by the envelope and vehicle max.

- [ ] **Step 4: Run acceleration tests to verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_acceleration.py -v`

Expected: PASS.

- [ ] **Step 5: Run full tests and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
git add docs/superpowers/plans/2026-06-03-forward-acceleration-loop.md tests/test_acceleration.py dragkraft/simulation/acceleration.py
git commit -m "feat: add forward acceleration loop"
```

Expected: all tests pass and a fourth local commit exists on `refactor/profile-braking-kernels`.
