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


def test_braking_curve_uses_max_speed_plus_one_loop_limit() -> None:
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
    assert np.isfinite(result[1])
    assert np.isinf(result[0])


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
