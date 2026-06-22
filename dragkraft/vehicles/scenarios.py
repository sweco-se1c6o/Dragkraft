from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.train import TrainConfig


@dataclass(frozen=True)
class TrainSpec:
    """A named locomotive consist ported from the legacy vehicle library.

    Masses and lengths are totals for the locomotive(s); wagon values are
    per-wagon so a consist can be scaled by the wagon count.
    """

    key: str
    label: str
    description: str
    locomotive_count: int
    locomotive_mass_kg: float
    locomotive_length_m: float
    wagon_mass_kg: float
    wagon_length_m: float
    default_wagons: int
    davis_b_n_per_mps: float
    davis_c_n_per_mps2: float
    vehicle_max_speed_kmh: float
    traction_speed_points_kmh: tuple[float, ...]
    traction_force_points_n: tuple[float, ...]
    type1_max_force_n: float
    type1_start_force_n: float
    type1_start_speed_kmh: float
    type1_power_w: float


# Shared signal braking table (goods, lambda 90 / 650 m) used by every consist.
_BRAKING_DECELERATIONS = (
    np.array(
        [5, 15, 20, 20, 25, 28, 31, 33, 36, 38, 40, 42, 36, 37, 37, 37, 37, 37, 37, 37, 37],
        dtype=float,
    )
    / 100.0
)


def _braking_speed_intervals() -> np.ndarray:
    return np.column_stack((np.arange(0.0, 200.0, 10.0), np.arange(10.0, 210.0, 10.0))) / 3.6


def _davis_a(train_mass_kg: float) -> float:
    """Davis A term, scaled proportionally between the two reference IORE trains."""
    return 94_520.0 + (train_mass_kg - 5_620_000.0) * (144_840.0 - 94_520.0) / (
        8_520_000.0 - 5_620_000.0
    )


TRAIN_LIBRARY: dict[str, TrainSpec] = {
    "freight": TrainSpec(
        key="freight",
        label="Freight — 2×EL19 (TRAXX)",
        description="Single TRAXX locomotive hauling 84 t wagons. The default, parity-validated consist.",
        locomotive_count=1,
        locomotive_mass_kg=76e3,
        locomotive_length_m=15.4,
        wagon_mass_kg=84e3,
        wagon_length_m=11.0,
        default_wagons=21,
        davis_b_n_per_mps=124.33 * 3.6,
        davis_c_n_per_mps2=5.06 * 3.6**2,
        vehicle_max_speed_kmh=60.0,
        traction_speed_points_kmh=(0.0, 67.0, 78.0, 100.0, 140.0),
        traction_force_points_n=tuple(2 * np.array([273.0, 188.0, 183.0, 176.0, 144.0]) * 1e3),
        type1_max_force_n=2 * 300e3,
        type1_start_force_n=2 * 300e3,
        type1_start_speed_kmh=5.0,
        type1_power_w=2 * 5.5833e6,
    ),
    "green-cargo": TrainSpec(
        key="green-cargo",
        label="Green Cargo Co-Co (TransMontana)",
        description="Twin Softronic TransMontana 6-axle locomotives. Higher power, 160 km/h.",
        locomotive_count=2,
        locomotive_mass_kg=2 * 123.6e3,
        locomotive_length_m=2 * 20.7,
        wagon_mass_kg=4 * 32.5e3,
        wagon_length_m=11.0,
        default_wagons=21,
        davis_b_n_per_mps=124.33 * 3.6,
        davis_c_n_per_mps2=5.06 * 3.6**2,
        vehicle_max_speed_kmh=160.0,
        traction_speed_points_kmh=(0.0, 70.0, 100.0, 120.0, 140.0, 160.0),
        traction_force_points_n=tuple(2 * np.array([402.0, 275.0, 258.0, 230.0, 198.0, 175.0]) * 1e3),
        type1_max_force_n=2 * 388e3,
        type1_start_force_n=2 * 435e3,
        type1_start_speed_kmh=70.0,
        type1_power_w=8.1e6,
    ),
    "iore": TrainSpec(
        key="iore",
        label="IORE ore train",
        description="Permanent double-unit IORE ore-haul locomotive (360 t). Very high tractive effort.",
        locomotive_count=2,
        locomotive_mass_kg=360e3,
        locomotive_length_m=2 * 22.9,
        wagon_mass_kg=4 * 32.5e3,
        wagon_length_m=11.0,
        default_wagons=21,
        davis_b_n_per_mps=124.33 * 3.6,
        davis_c_n_per_mps2=5.06 * 3.6**2,
        vehicle_max_speed_kmh=80.0,
        traction_speed_points_kmh=(0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 75.0, 80.0),
        traction_force_points_n=tuple(
            np.array([999.0, 999.0, 922.0, 851.0, 797.0, 716.0, 620.0, 510.12, 461.07, 421.83]) * 1e3
        ),
        type1_max_force_n=2 * 388e3,
        type1_start_force_n=2 * 435e3,
        type1_start_speed_kmh=70.0,
        type1_power_w=8.1e6,
    ),
    "td": TrainSpec(
        key="td",
        label="Td locomotive (2×)",
        description="Two Td locomotives hauling 115 t wagons.",
        locomotive_count=2,
        locomotive_mass_kg=2 * 76e3,
        locomotive_length_m=2 * 15.4,
        wagon_mass_kg=115e3,
        wagon_length_m=11.0,
        default_wagons=21,
        davis_b_n_per_mps=50.0 * 3.6,
        davis_c_n_per_mps2=4.14 * 3.6**2,
        vehicle_max_speed_kmh=160.0,
        traction_speed_points_kmh=(0.0, 1.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0),
        traction_force_points_n=tuple(
            2
            * np.array(
                [186.9, 184.38, 166.32, 146.26, 121.50, 95.58, 69.65, 61.15, 52.65, 44.15]
            )
            * 1e3
        ),
        type1_max_force_n=2 * 186.39e3,
        type1_start_force_n=2 * 186.39e3,
        type1_start_speed_kmh=80.0,
        type1_power_w=8.1e6,
    ),
}


def _type2_traction(speed_points_kmh, force_points_n):
    speeds = np.asarray(speed_points_kmh, dtype=float) / 3.6
    forces = np.asarray(force_points_n, dtype=float)
    speed_intervals = np.column_stack((speeds[:-1], speeds[1:]))
    force_intervals = np.column_stack((forces[:-1], forces[1:]))
    slopes = np.diff(force_intervals, axis=1).ravel() / np.diff(speed_intervals, axis=1).ravel()
    intercepts = force_intervals[:, 0] - slopes * speed_intervals[:, 0]
    return speed_intervals, force_intervals, intercepts, slopes


def build_train(
    key: str,
    *,
    extra_wagons: int | None = None,
    adhesion_coefficient: float = 0.6,
    locomotive_mass_kg: float | None = None,
    locomotive_length_m: float | None = None,
    wagon_mass_kg: float | None = None,
    wagon_length_m: float | None = None,
) -> TrainConfig:
    """Build a TrainConfig for a named consist in :data:`TRAIN_LIBRARY`.

    The mass/length keyword arguments override the library defaults when given
    (locomotive values are totals across all locomotives; wagon values are
    per-wagon), so a preset can be re-weighted or re-sized without switching to
    the fully custom builder.
    """
    spec = TRAIN_LIBRARY[key]
    wagons = spec.default_wagons if extra_wagons is None else int(extra_wagons)
    loco_mass = spec.locomotive_mass_kg if locomotive_mass_kg is None else float(locomotive_mass_kg)
    loco_length = (
        spec.locomotive_length_m if locomotive_length_m is None else float(locomotive_length_m)
    )
    wagon_mass_each = spec.wagon_mass_kg if wagon_mass_kg is None else float(wagon_mass_kg)
    wagon_length_each = spec.wagon_length_m if wagon_length_m is None else float(wagon_length_m)
    wagon_mass = wagons * wagon_mass_each
    train_mass = loco_mass + wagon_mass
    speed_intervals, force_intervals, intercepts, slopes = _type2_traction(
        spec.traction_speed_points_kmh, spec.traction_force_points_n
    )
    return TrainConfig(
        name=spec.key,
        locomotive_count=spec.locomotive_count,
        locomotive_mass_kg=loco_mass,
        extra_wagon_count=wagons,
        wagon_mass_kg=wagon_mass,
        train_mass_kg=train_mass,
        dynamic_mass_kg=1.06 * train_mass,
        adhesion_mass_kg=loco_mass,
        adhesion_coefficient=float(adhesion_coefficient),
        train_length_m=loco_length + wagons * wagon_length_each,
        resistance_type=1,
        davis_a_n=_davis_a(train_mass),
        davis_b_n_per_mps=spec.davis_b_n_per_mps,
        davis_c_n_per_mps2=spec.davis_c_n_per_mps2,
        resistance_factor=3.30,
        traction_model_type=2,
        max_force_n=spec.type1_max_force_n,
        start_force_n=spec.type1_start_force_n,
        start_force_max_speed_mps=spec.type1_start_speed_kmh / 3.6,
        continuous_power_w=spec.type1_power_w,
        traction_speed_intervals_mps=speed_intervals,
        traction_force_intervals_n=force_intervals,
        traction_intercepts_n=intercepts,
        traction_slopes_n_per_mps=slopes,
        min_deceleration_mps2=0.15,
        max_deceleration_mps2=0.7,
        max_acceleration_mps2=1.0,
        vehicle_max_speed_mps=spec.vehicle_max_speed_kmh / 3.6,
        braking_speed_intervals_mps=_braking_speed_intervals(),
        braking_decelerations_mps2=_BRAKING_DECELERATIONS.copy(),
    )


def custom_train(*, extra_wagons: int, adhesion_coefficient: float, params: dict[str, Any]) -> TrainConfig:
    """Build a user-defined consist using a type-1 (force + power) traction model."""

    def num(key: str, default: float) -> float:
        value = params.get(key)
        if value is None or value == "":
            return float(default)
        return float(value)

    wagons = int(extra_wagons)
    locomotive_count = max(1, int(num("custom_locomotive_count", 1)))
    locomotive_mass = num("custom_locomotive_mass_t", 76.0) * 1000.0
    wagon_mass_each = num("custom_wagon_mass_t", 84.0) * 1000.0
    wagon_mass = wagons * wagon_mass_each
    train_mass = locomotive_mass + wagon_mass
    max_force = num("custom_max_force_kn", 600.0) * 1000.0

    return TrainConfig(
        name="custom",
        locomotive_count=locomotive_count,
        locomotive_mass_kg=locomotive_mass,
        extra_wagon_count=wagons,
        wagon_mass_kg=wagon_mass,
        train_mass_kg=train_mass,
        dynamic_mass_kg=1.06 * train_mass,
        adhesion_mass_kg=locomotive_mass,
        adhesion_coefficient=float(adhesion_coefficient),
        train_length_m=num("custom_locomotive_length_m", 15.4) * locomotive_count
        + wagons * num("custom_wagon_length_m", 11.0),
        resistance_type=1,
        davis_a_n=num("custom_davis_a_n", _davis_a(train_mass)),
        davis_b_n_per_mps=num("custom_davis_b_n_per_mps", 124.33 * 3.6),
        davis_c_n_per_mps2=num("custom_davis_c_n_per_mps2", 5.06 * 3.6**2),
        resistance_factor=3.30,
        traction_model_type=1,
        max_force_n=max_force,
        start_force_n=num("custom_start_force_kn", num("custom_max_force_kn", 600.0)) * 1000.0,
        start_force_max_speed_mps=num("custom_start_speed_kmh", 5.0) / 3.6,
        continuous_power_w=num("custom_power_kw", 5000.0) * 1000.0,
        traction_speed_intervals_mps=np.array([[0.0, 1e9]]),
        traction_force_intervals_n=np.array([[max_force, max_force]]),
        traction_intercepts_n=np.array([max_force]),
        traction_slopes_n_per_mps=np.array([0.0]),
        min_deceleration_mps2=0.15,
        max_deceleration_mps2=num("custom_max_deceleration_mps2", 0.7),
        max_acceleration_mps2=num("custom_max_acceleration_mps2", 1.0),
        vehicle_max_speed_mps=num("custom_vehicle_max_speed_kmh", 100.0) / 3.6,
        braking_speed_intervals_mps=_braking_speed_intervals(),
        braking_decelerations_mps2=_BRAKING_DECELERATIONS.copy(),
    )


def freight_train(*, extra_wagons: int = 21) -> TrainConfig:
    """Standard freight train consist (kept for backwards compatibility)."""
    return build_train("freight", extra_wagons=extra_wagons)


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
