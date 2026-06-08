from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from dragkraft.simulation.envelope import build_initial_speed_envelope
from dragkraft.simulation.profile import ProfileVectors
from dragkraft.vehicles.scenarios import default_scenario, freight_train


def test_build_initial_speed_envelope_combines_sth_transition_and_stop_rows() -> None:
    vectors = _sample_vectors()
    train = replace(
        freight_train(extra_wagons=21),
        train_length_m=3.0,
        braking_speed_intervals_mps=np.array([[0.0, 100.0]]),
        braking_decelerations_mps2=np.array([0.5]),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=1.0,
    )
    settings = replace(
        default_scenario(),
        freight_signal_advance_s_per_mps=2.0,
        switch_speed_mps=10.0,
    )

    result = build_initial_speed_envelope(
        vectors=vectors,
        train=train,
        settings=settings,
        equivalent_gradient=np.zeros(vectors.max_position_m + 1),
    )

    assert result.candidate_profiles_mps.shape == (4, 61)
    assert result.candidate_profiles_mps[0, 1:21].tolist() == [2.0] * 20
    assert result.candidate_profiles_mps[0, 21:51].tolist() == [4.0] * 30
    assert result.candidate_profiles_mps[0, 51:61].tolist() == [1.0] * 10
    assert result.candidate_profiles_mps[1, 20:24].tolist() == [2.0] * 4
    assert result.candidate_profiles_mps[2, 48] == pytest.approx(1.0)
    assert result.candidate_profiles_mps[2, 49:51].tolist() == [1.0, 1.0]
    assert np.isfinite(result.candidate_profiles_mps[2, 47])
    assert result.candidate_profiles_mps[3, 55] == pytest.approx(0.5)
    assert result.speed_envelope_mps[50] == pytest.approx(1.0)
    assert result.speed_envelope_mps[55] == pytest.approx(0.5)


def _sample_vectors() -> ProfileVectors:
    return ProfileVectors(
        origin_km=10.0,
        max_position_m=60,
        speed_limit_positions_m=np.array([[0, 20], [20, 50], [50, 60]]),
        speed_limits_mps=np.array([2.0, 4.0, 1.0]),
        gradient_positions_m=np.array([0, 60]),
        gradient_slopes=np.array([0.0]),
        tunnel_rows_m=np.empty((0, 3)),
        timing_point_positions_m=np.array([], dtype=int),
        timing_point_names=(),
        stop_positions_m=np.array([55]),
        stop_names=("Stop",),
        stop_times_s=np.array([30.0]),
        curve_positions_m=np.array([0, 60]),
        curve_radii_m=np.array([float("inf")]),
        signal_positions_m=np.array([], dtype=int),
        signal_names=(),
        signal_release_speeds_mps=np.array([]),
        signal_overlaps_m=np.array([]),
        signal_release_times_s=np.array([]),
        signal_setting_times_s=np.array([]),
    )
