from __future__ import annotations

from dataclasses import replace

import math

import numpy as np
import pytest

from dragkraft.domain.track import (
    CurveSegment,
    GradientSegment,
    SignalBlock,
    SpeedLimitSegment,
    Stop,
    TimingPoint,
    TrackProfile,
    TunnelSegment,
)
from dragkraft.domain.train import TrainConfig
from dragkraft.simulation.orchestrator import simulate_profile
from dragkraft.vehicles.legacy_cases import default_nyprofil_scenario


def test_simulate_profile_wires_envelope_acceleration_time_and_timing_points() -> None:
    settings = replace(
        default_nyprofil_scenario(),
        flip_profiles=False,
        short_time_margin=1.0,
        use_distance_before_signal=False,
        use_train_length_delay=False,
        time_offset_s=10.0,
    )

    result = simulate_profile(
        profile=_sample_profile(),
        train=_sample_train(),
        settings=settings,
    )

    assert result.route.vectors.max_position_m == 5
    assert result.initial_envelope.candidate_profiles_mps[0, 1:6].tolist() == [2.0] * 5
    assert result.initial_envelope.speed_envelope_mps[4] < 2.0
    assert result.acceleration_profile_mps[1] == pytest.approx(
        result.initial_envelope.speed_envelope_mps[1]
    )
    assert result.speed_profile_mps[1] == pytest.approx(result.acceleration_profile_mps[1])
    assert result.speed_profile_mps[4] == 0.0
    assert result.running_speed_profile_mps[4] > 0.0
    assert result.time_s_per_m[4] == pytest.approx(
        1.0 / result.running_speed_profile_mps[4] + 30.0
    )
    assert result.cumulative_time_s[0] == pytest.approx(10.0)
    assert result.timing_passages[0].name == "TP"
    assert result.timing_passages[0].position_m == 3
    assert result.timing_passages[0].time_s == pytest.approx(result.cumulative_time_s[3])


def _sample_profile() -> TrackProfile:
    return TrackProfile(
        sheet_name="Example",
        speed_limits=(SpeedLimitSegment(10.0, 10.005, 7.2),),
        gradients=(GradientSegment(10.0, 10.005, 0.0),),
        tunnels=(TunnelSegment(10.0, 10.005, 0.0),),
        timing_points=(TimingPoint(10.003, "TP"),),
        stops=(Stop(10.004, "Stop", 30.0),),
        curves=(CurveSegment(10.0, 10.005, math.inf),),
        signals=(SignalBlock(10.004, "MB1", 5.0, 12.0, 3.0, 4.0),),
    )


def _sample_train() -> TrainConfig:
    return TrainConfig(
        name="sample",
        locomotive_count=1,
        locomotive_mass_kg=20.0,
        extra_wagon_count=1,
        wagon_mass_kg=80.0,
        train_mass_kg=100.0,
        dynamic_mass_kg=100.0,
        adhesion_mass_kg=20.0,
        adhesion_coefficient=100.0,
        train_length_m=1.0,
        resistance_type=1,
        davis_a_n=0.0,
        davis_b_n_per_mps=0.0,
        davis_c_n_per_mps2=0.0,
        resistance_factor=0.0,
        traction_model_type=2,
        max_force_n=100.0,
        start_force_n=100.0,
        start_force_max_speed_mps=2.0,
        continuous_power_w=1000.0,
        traction_speed_intervals_mps=np.array([[0.0, 10.0]]),
        traction_force_intervals_n=np.array([[100.0, 100.0]]),
        traction_intercepts_n=np.array([100.0]),
        traction_slopes_n_per_mps=np.array([0.0]),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=1.0,
        max_acceleration_mps2=1.0,
        vehicle_max_speed_mps=2.0,
        braking_speed_intervals_mps=np.array([[0.0, 10.0]]),
        braking_decelerations_mps2=np.array([0.5]),
    )
