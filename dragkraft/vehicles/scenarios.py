from __future__ import annotations

import numpy as np

from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.train import TrainConfig


def freight_train(*, extra_wagons: int = 21) -> TrainConfig:
    """Standard freight train consist definition."""
    locomotive_count = 1
    locomotive_mass_kg = locomotive_count * 76e3
    wagon_mass_kg = int(extra_wagons) * 84e3
    train_mass_kg = locomotive_mass_kg + wagon_mass_kg

    traction_speed_points = np.array([0.0, 67.0, 78.0, 100.0, 140.0]) / 3.6
    traction_force_points = 2 * np.array([273.0, 188.0, 183.0, 176.0, 144.0]) * 1e3
    traction_speed_intervals = np.column_stack(
        (traction_speed_points[:-1], traction_speed_points[1:])
    )
    traction_force_intervals = np.column_stack(
        (traction_force_points[:-1], traction_force_points[1:])
    )
    traction_slopes = np.diff(traction_force_intervals, axis=1).ravel() / np.diff(
        traction_speed_intervals,
        axis=1,
    ).ravel()
    traction_intercepts = traction_force_intervals[:, 0] - (
        traction_slopes * traction_speed_intervals[:, 0]
    )

    braking_speed_intervals = np.column_stack(
        (np.arange(0.0, 200.0, 10.0), np.arange(10.0, 210.0, 10.0))
    ) / 3.6
    braking_decelerations = np.array(
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

    return TrainConfig(
        name="freight",
        locomotive_count=locomotive_count,
        locomotive_mass_kg=locomotive_mass_kg,
        extra_wagon_count=int(extra_wagons),
        wagon_mass_kg=wagon_mass_kg,
        train_mass_kg=train_mass_kg,
        dynamic_mass_kg=1.06 * train_mass_kg,
        adhesion_mass_kg=locomotive_mass_kg,
        adhesion_coefficient=0.6,
        train_length_m=locomotive_count * 15.4 + int(extra_wagons) * 11.0,
        resistance_type=1,
        davis_a_n=94_520.0
        + (train_mass_kg - 5_620_000.0)
        * (144_840.0 - 94_520.0)
        / (8_520_000.0 - 5_620_000.0),
        davis_b_n_per_mps=124.33 * 3.6,
        davis_c_n_per_mps2=5.06 * 3.6**2,
        resistance_factor=3.30,
        traction_model_type=2,
        max_force_n=2 * 300e3,
        start_force_n=2 * 300e3,
        start_force_max_speed_mps=5 / 3.6,
        continuous_power_w=2 * 5.5833e6,
        traction_speed_intervals_mps=traction_speed_intervals,
        traction_force_intervals_n=traction_force_intervals,
        traction_intercepts_n=traction_intercepts,
        traction_slopes_n_per_mps=traction_slopes,
        min_deceleration_mps2=0.15,
        max_deceleration_mps2=0.7,
        max_acceleration_mps2=1.0,
        vehicle_max_speed_mps=60.0 / 3.6,
        braking_speed_intervals_mps=braking_speed_intervals,
        braking_decelerations_mps2=braking_decelerations,
    )


def default_scenario() -> SimulationSettings:
    """Default simulation scenario constants."""
    return SimulationSettings(
        workbook_name="luleaHamn3.xlsx",
        sheet_name="NyProfil",
        train_name="freight",
        extra_wagon_count=21,
        speed_override_kmh=40.0,
        flip_profiles=True,
        altitude_at_start_m=3.416,
        time_offset_s=0.0,
        short_time_margin=1.0,
        use_train_length_delay=True,
        use_distance_before_signal=True,
        use_tav_distance=True,
        freight_signal_advance_s_per_mps=37.7,
        freight_signal_advance2_s_per_mps=26.0,
        freight_signal_advance2_m=355.75,
        switch_speed_mps=110.0 / 3.6,
        use_min_time_to_hold_speed=False,
        min_time_to_hold_speed_s=30.0,
        speed_tolerance_mps=0.5 / 3.6,
        min_signal_deceleration_mps2=0.13,
        reserve_before_arrival_s=20.0,
    )
