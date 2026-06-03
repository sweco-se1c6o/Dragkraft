from __future__ import annotations

import math

import numpy as np
import pytest

from dragkraft.simulation.resistance import equivalent_gradient, curve_resistance


def test_equivalent_gradient_uses_single_active_interval_value() -> None:
    result = equivalent_gradient(
        boundaries_m=np.array([0.0, 100.0, 200.0]),
        gradients=np.array([0.010, 0.020]),
        x_positions_m=np.array([50.0]),
        train_length_m=100.0,
    )

    assert result.tolist() == [0.010]


def test_equivalent_gradient_weights_multiple_intervals_over_train_length() -> None:
    result = equivalent_gradient(
        boundaries_m=np.array([0.0, 100.0, 200.0]),
        gradients=np.array([0.010, 0.020]),
        x_positions_m=np.array([150.0]),
        train_length_m=100.0,
    )

    assert result.tolist() == [pytest.approx(0.015)]


def test_curve_resistance_uses_single_active_interval_force() -> None:
    mass_kg = 1000.0

    result = curve_resistance(
        boundaries_m=np.array([0.0, 100.0, 200.0]),
        radii_m=np.array([250.0, math.inf]),
        x_positions_m=np.array([50.0]),
        train_length_m=100.0,
        train_mass_kg=mass_kg,
    )

    assert result.tolist() == [pytest.approx(4.91 / (250.0 - 30.0) * mass_kg)]


def test_curve_resistance_weights_multiple_intervals_over_train_length() -> None:
    mass_kg = 1000.0

    result = curve_resistance(
        boundaries_m=np.array([0.0, 100.0, 200.0]),
        radii_m=np.array([250.0, math.inf]),
        x_positions_m=np.array([150.0]),
        train_length_m=100.0,
        train_mass_kg=mass_kg,
    )

    expected_curve_force = 4.91 / (250.0 - 30.0) * mass_kg
    assert result.tolist() == [pytest.approx(expected_curve_force / 2)]


def test_curve_resistance_treats_infinite_radius_as_zero_force() -> None:
    result = curve_resistance(
        boundaries_m=np.array([0.0, 100.0]),
        radii_m=np.array([math.inf]),
        x_positions_m=np.array([50.0]),
        train_length_m=100.0,
        train_mass_kg=1000.0,
    )

    assert result.tolist() == [0.0]
