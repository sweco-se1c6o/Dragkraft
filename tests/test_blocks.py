from __future__ import annotations

import math

import numpy as np
import pytest

from dragkraft.simulation.blocks import block_occupation


def test_block_occupation_uses_first_mb_curve_intersection_for_booking_time() -> None:
    speed_profile = np.full(11, 2.0)
    cumulative_time = np.arange(11, dtype=float) * 10.0

    result = block_occupation(
        signal_positions_m=np.array([5]),
        signal_names=("MB1",),
        release_speeds_mps=np.array([0.0]),
        overlaps_m=np.array([1.0]),
        release_times_s=np.array([3.0]),
        setting_times_s=np.array([4.0]),
        speed_profile_mps=speed_profile,
        cumulative_time_s=cumulative_time,
        retardation_mps2=np.array([0.5]),
        speed_intervals_mps=np.array([[0.0, 10.0]]),
        max_speed_mps=2.0,
        train_length_m=2.0,
        equivalent_gradient=np.zeros(11),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=math.inf,
        speed_tolerance_mps=0.2,
        reserve_before_arrival_s=20.0,
    )

    row = result.occupations[0]
    assert row.name == "MB1"
    assert row.signal_position_m == 5
    assert row.intersection_position_m == 1
    assert row.speed_difference_mps == pytest.approx(0.0)
    assert row.booking_time_s == pytest.approx(6.0)
    assert row.arrival_time_s == pytest.approx(50.0)
    assert row.release_time_s == pytest.approx(83.0)
    assert result.mb_braking_curves_mps.shape == (1, 11)
    assert result.mb_braking_curves_mps[0, 1] == pytest.approx(2.0)


def test_block_occupation_falls_back_to_reserve_before_arrival_without_intersection() -> None:
    speed_profile = np.full(11, 10.0)
    cumulative_time = np.arange(11, dtype=float) * 10.0

    result = block_occupation(
        signal_positions_m=np.array([5]),
        signal_names=("MB1",),
        release_speeds_mps=np.array([0.0]),
        overlaps_m=np.array([1.0]),
        release_times_s=np.array([3.0]),
        setting_times_s=np.array([4.0]),
        speed_profile_mps=speed_profile,
        cumulative_time_s=cumulative_time,
        retardation_mps2=np.array([0.5]),
        speed_intervals_mps=np.array([[0.0, 20.0]]),
        max_speed_mps=2.0,
        train_length_m=2.0,
        equivalent_gradient=np.zeros(11),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=math.inf,
        speed_tolerance_mps=0.2,
        reserve_before_arrival_s=20.0,
    )

    row = result.occupations[0]
    assert math.isnan(row.speed_difference_mps)
    assert row.intersection_position_m is None
    assert row.booking_time_s == pytest.approx(30.0)
    assert row.arrival_time_s == pytest.approx(50.0)
    assert row.release_time_s == pytest.approx(83.0)
