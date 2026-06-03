from __future__ import annotations

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
from dragkraft.simulation.route import build_acceleration_callback, prepare_route_vectors


def test_prepare_route_vectors_wires_profile_tunnel_gradient_and_curve_kernels() -> None:
    train = _sample_train()

    result = prepare_route_vectors(
        profile=_sample_profile(),
        train=train,
        flip=False,
    )

    assert result.vectors.max_position_m == 6
    assert result.x_positions_m.tolist() == [0, 1, 2, 3, 4, 5, 6]
    assert result.tunnel_factor.tolist() == [0.0, 0.0, 7.5, 7.5, 7.5, 0.0, 0.0]
    assert result.equivalent_gradient[1] == pytest.approx(0.010)
    assert result.equivalent_gradient[4] == pytest.approx(
        (0.010 * 2.0 + 0.020 * 1.0) / 3.0
    )
    expected_curve_force = 4.91 / (250.0 - 30.0) * train.train_mass_kg
    assert result.curve_resistance_n[1] == pytest.approx(expected_curve_force)
    assert result.curve_resistance_n[4] == pytest.approx(expected_curve_force * 2.0 / 3.0)


def test_build_acceleration_callback_combines_type2_adhesion_and_resistance_terms() -> None:
    train = _sample_train()
    route = prepare_route_vectors(profile=_sample_profile(), train=train, flip=False)

    callback = build_acceleration_callback(route=route, train=train)

    result = callback(2, 2.0)

    requested = 1000.0 - 10.0 * 2.0
    adhesion_limit = (2.1 / (2.0 + 12.2) + 0.161) * 0.6 * 20.0 * 9.81
    traction = min(requested, adhesion_limit)
    expected_net = traction - (10.0 + 3.0 * 2.0 + 2.0 * 2.0**2)
    expected_net -= train.train_mass_kg * 9.81 * route.equivalent_gradient[2]
    expected_net -= route.tunnel_factor[2] * 2.0**2
    expected_net -= route.curve_resistance_n[2]
    assert result == pytest.approx(min(expected_net / train.dynamic_mass_kg, 2.0))


def _sample_profile() -> TrackProfile:
    return TrackProfile(
        sheet_name="Example",
        speed_limits=(SpeedLimitSegment(10.0, 10.006, 36.0),),
        gradients=(
            GradientSegment(10.0, 10.003, 10.0),
            GradientSegment(10.003, 10.006, 20.0),
        ),
        tunnels=(TunnelSegment(10.002, 10.004, 7.5),),
        timing_points=(TimingPoint(10.003, "TP"),),
        stops=(Stop(10.005, "Stop", 30.0),),
        curves=(
            CurveSegment(10.0, 10.003, 250.0),
            CurveSegment(10.003, 10.006, math.inf),
        ),
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
        dynamic_mass_kg=120.0,
        adhesion_mass_kg=20.0,
        adhesion_coefficient=0.6,
        train_length_m=3.0,
        resistance_type=1,
        davis_a_n=10.0,
        davis_b_n_per_mps=3.0,
        davis_c_n_per_mps2=2.0,
        resistance_factor=3.3,
        traction_model_type=2,
        max_force_n=1000.0,
        start_force_n=500.0,
        start_force_max_speed_mps=2.0,
        continuous_power_w=5000.0,
        traction_speed_intervals_mps=np.array([[0.0, 10.0]]),
        traction_force_intervals_n=np.array([[1000.0, 900.0]]),
        traction_intercepts_n=np.array([1000.0]),
        traction_slopes_n_per_mps=np.array([-10.0]),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=1.0,
        max_acceleration_mps2=2.0,
        vehicle_max_speed_mps=20.0,
        braking_speed_intervals_mps=np.array([[0.0, 20.0]]),
        braking_decelerations_mps2=np.array([0.5]),
    )
