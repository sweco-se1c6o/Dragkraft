from __future__ import annotations

import numpy as np
import pytest

from dragkraft.vehicles.scenarios import (
    default_scenario,
    freight_train,
)


def test_freight_train_matches_expected_consist_block() -> None:
    train = freight_train(extra_wagons=21)

    assert train.name == "freight"
    assert train.locomotive_count == 1
    assert train.locomotive_mass_kg == pytest.approx(76_000.0)
    assert train.extra_wagon_count == 21
    assert train.wagon_mass_kg == pytest.approx(21 * 84_000.0)
    assert train.train_mass_kg == pytest.approx(1_840_000.0)
    assert train.dynamic_mass_kg == pytest.approx(1.06 * 1_840_000.0)
    assert train.adhesion_mass_kg == pytest.approx(76_000.0)
    assert train.adhesion_coefficient == pytest.approx(0.6)
    assert train.train_length_m == pytest.approx(1 * 15.4 + 21 * 11.0)
    assert train.resistance_type == 1
    assert train.davis_a_n == pytest.approx(
        94_520.0
        + (1_840_000.0 - 5_620_000.0)
        * (144_840.0 - 94_520.0)
        / (8_520_000.0 - 5_620_000.0)
    )
    assert train.davis_b_n_per_mps == pytest.approx(124.33 * 3.6)
    assert train.davis_c_n_per_mps2 == pytest.approx(5.06 * 3.6**2)
    assert train.traction_model_type == 2
    assert train.max_force_n == pytest.approx(600_000.0)
    assert train.start_force_n == pytest.approx(600_000.0)
    assert train.continuous_power_w == pytest.approx(2 * 5.5833e6)
    assert train.min_deceleration_mps2 == pytest.approx(0.15)
    assert train.max_deceleration_mps2 == pytest.approx(0.7)
    assert train.max_acceleration_mps2 == pytest.approx(1.0)
    assert train.vehicle_max_speed_mps == pytest.approx(60.0 / 3.6)


def test_freight_train_calculates_type2_traction_arrays() -> None:
    train = freight_train(extra_wagons=21)

    speed_points = np.array([0.0, 67.0, 78.0, 100.0, 140.0]) / 3.6
    force_points = 2 * np.array([273.0, 188.0, 183.0, 176.0, 144.0]) * 1000.0
    expected_intervals = np.column_stack((speed_points[:-1], speed_points[1:]))
    expected_force_intervals = np.column_stack((force_points[:-1], force_points[1:]))
    expected_slopes = np.diff(expected_force_intervals, axis=1).ravel() / np.diff(
        expected_intervals,
        axis=1,
    ).ravel()
    expected_intercepts = expected_force_intervals[:, 0] - (
        expected_slopes * expected_intervals[:, 0]
    )

    np.testing.assert_allclose(train.traction_speed_intervals_mps, expected_intervals)
    np.testing.assert_allclose(train.traction_force_intervals_n, expected_force_intervals)
    np.testing.assert_allclose(train.traction_slopes_n_per_mps, expected_slopes)
    np.testing.assert_allclose(train.traction_intercepts_n, expected_intercepts)


def test_freight_train_uses_signal_braking_table_as_active_retardation() -> None:
    train = freight_train(extra_wagons=21)

    expected_intervals = np.column_stack(
        (np.arange(0.0, 200.0, 10.0), np.arange(10.0, 210.0, 10.0))
    ) / 3.6
    expected_deceleration = np.array(
        [
            5,
            15,
            20,
            20,
            25,
            28,
            31,
            33,
            36,
            38,
            40,
            42,
            36,
            37,
            37,
            37,
            37,
            37,
            37,
            37,
            37,
        ],
        dtype=float,
    ) / 100.0

    np.testing.assert_allclose(train.braking_speed_intervals_mps, expected_intervals)
    np.testing.assert_allclose(train.braking_decelerations_mps2, expected_deceleration)


def test_default_scenario_matches_expected_settings() -> None:
    scenario = default_scenario()

    assert scenario.workbook_name == "luleaHamn3.xlsx"
    assert scenario.sheet_name == "NyProfil"
    assert scenario.train_name == "freight"
    assert scenario.extra_wagon_count == 21
    assert scenario.speed_override_kmh == pytest.approx(40.0)
    assert scenario.flip_profiles is True
    assert scenario.altitude_at_start_m == pytest.approx(3.416)
    assert scenario.time_offset_s == pytest.approx(0.0)
    assert scenario.short_time_margin == pytest.approx(1.0)
    assert scenario.use_train_length_delay is True
    assert scenario.use_distance_before_signal is True
    assert scenario.use_tav_distance is True
    assert scenario.freight_signal_advance_s_per_mps == pytest.approx(37.7)
    assert scenario.freight_signal_advance2_s_per_mps == pytest.approx(26.0)
    assert scenario.freight_signal_advance2_m == pytest.approx(355.75)
    assert scenario.switch_speed_mps == pytest.approx(110.0 / 3.6)
    assert scenario.use_min_time_to_hold_speed is False
    assert scenario.min_time_to_hold_speed_s == pytest.approx(30.0)
    assert scenario.speed_tolerance_mps == pytest.approx(0.5 / 3.6)
    assert scenario.min_signal_deceleration_mps2 == pytest.approx(0.13)
    assert scenario.reserve_before_arrival_s == pytest.approx(20.0)
