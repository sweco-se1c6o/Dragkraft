from __future__ import annotations

import numpy as np
import pytest

from dragkraft.simulation.acceleration import (
    acceleration_rate,
    adhesion_limited_force,
    forward_acceleration_profile,
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


def test_adhesion_limited_force_applies_2022_formula() -> None:
    force = adhesion_limited_force(
        requested_force_n=10_000.0,
        speed_mps=2.0,
        adhesion_coefficient=0.6,
        adhesion_mass_kg=76_000.0,
    )

    expected_limit = (2.1 / (2.0 + 12.2) + 0.161) * 0.6 * 76_000.0 * 9.81
    assert force == pytest.approx(min(10_000.0, expected_limit))


def test_net_force_resistance_type1_matches_davis_formula() -> None:
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


def test_net_force_resistance_type2_matches_strahl_formula() -> None:
    force = net_force(
        traction_force_n=1000.0,
        speed_mps=2.0,
        resistance_type=2,
        davis_a_n=10.0,
        davis_b_n_per_mps=3.0,
        davis_c_n_per_mps2=2.0,
        train_mass_kg=100.0,
        dynamic_mass_kg=120.0,
        equivalent_gradient=0.01,
        tunnel_factor=5.0,
        curve_force_n=7.0,
        resistance_factor=3.3,
        wagon_count=2,
        locomotive_mass_kg=20.0,
    )

    expected = 1000.0 - 9.81 * (3.3 * 100.0 / 1000.0 + 2 * 0.03 * (2.0 * 3.6) ** 2)
    expected -= 100.0 * 9.81 * 0.01
    expected -= 5.0 * 2.0**2
    expected -= 7.0
    assert force == pytest.approx(expected)


def test_net_force_resistance_type3_matches_mixed_formula() -> None:
    force = net_force(
        traction_force_n=1000.0,
        speed_mps=2.0,
        resistance_type=3,
        davis_a_n=10.0,
        davis_b_n_per_mps=3.0,
        davis_c_n_per_mps2=2.0,
        train_mass_kg=100.0,
        dynamic_mass_kg=120.0,
        equivalent_gradient=0.01,
        tunnel_factor=5.0,
        curve_force_n=7.0,
        resistance_factor=3.3,
        wagon_count=2,
        locomotive_mass_kg=20.0,
    )

    v_kmh = 2.0 * 3.6
    expected = 1000.0 - 9.81 * (3.3 * 20.0 / 1000.0 + 2 * 0.03 * v_kmh**2)
    expected -= (9.81 * (100.0 - 20.0) / 1000.0) * (
        2.2 - 80.0 / (v_kmh + 38.0) + 0.00032 * v_kmh**2
    )
    expected -= 100.0 * 9.81 * 0.01
    expected -= 5.0 * 2.0**2
    expected -= 7.0
    assert force == pytest.approx(expected)


def test_acceleration_rate_caps_net_force_over_dynamic_mass() -> None:
    assert acceleration_rate(
        net_force_n=50.0,
        dynamic_mass_kg=10.0,
        max_acceleration_mps2=1.5,
    ) == pytest.approx(1.5)


def test_forward_acceleration_profile_writes_zero_speed_half_step_then_average_speed() -> None:
    result = forward_acceleration_profile(
        start_position_m=1,
        start_speed_mps=0.0,
        max_position_m=2,
        speed_envelope_mps=np.full(3, np.inf),
        vehicle_max_speed_mps=np.inf,
        acceleration_at=lambda position, speed: 1.0,
    )

    assert result.stall is None
    assert result.profile[1] == pytest.approx(2**0.5 / 2)
    assert result.profile[2] == pytest.approx(2**0.5 / 2)


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

    assert result.profile[3] == pytest.approx(1.0)


def test_forward_acceleration_profile_reports_partial_profile_when_train_stalls() -> None:
    result = forward_acceleration_profile(
        start_position_m=1,
        start_speed_mps=0.2,
        max_position_m=3,
        speed_envelope_mps=np.full(4, np.inf),
        vehicle_max_speed_mps=np.inf,
        acceleration_at=lambda position, speed: -0.1,
    )

    assert result.stall is not None
    assert result.stall.position_m == 1
    assert result.stall.speed_mps == pytest.approx(0.2)
    # The reached position keeps its speed; everything beyond stays unfilled.
    assert result.profile[1] == pytest.approx(0.2)
    assert not np.isfinite(result.profile[2])
    assert "Train stalled at position 1 m" in result.stall.describe()
