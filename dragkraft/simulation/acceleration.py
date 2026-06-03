from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike


def traction_force_type1(
    *,
    speed_mps: float,
    max_force_n: float,
    continuous_power_w: float,
    start_force_n: float,
    start_force_max_speed_mps: float,
) -> float:
    """Calculate acc3 traction model type 1 force."""
    speed = float(speed_mps)
    if speed == 0:
        force = float(max_force_n)
    else:
        force = min(float(max_force_n), float(continuous_power_w) / speed)
    if speed < float(start_force_max_speed_mps):
        force = float(start_force_n) + (
            float(max_force_n) - float(start_force_n)
        ) * speed / float(start_force_max_speed_mps)
    return float(force)


def traction_force_type2(
    speed_mps: float,
    aa: ArrayLike,
    bb: ArrayLike,
    speed_intervals_mps: ArrayLike,
) -> float:
    """Calculate acc3 traction model type 2 piecewise-linear force."""
    speed = float(speed_mps)
    intercepts = np.asarray(aa, dtype=float)
    slopes = np.asarray(bb, dtype=float)
    intervals = np.asarray(speed_intervals_mps, dtype=float)
    active = (speed >= intervals[:, 0]) & (speed < intervals[:, 1])
    if speed >= intervals[-1, 1]:
        active[-1] = True
    if not np.any(active):
        raise ValueError(f"No traction interval contains speed {speed}")
    index = int(np.flatnonzero(active)[0])
    return float(intercepts[index] + slopes[index] * speed)


def adhesion_limited_force(
    *,
    requested_force_n: float,
    speed_mps: float,
    adhesion_coefficient: float,
    adhesion_mass_kg: float,
) -> float:
    """Apply acc3's 2022 adhesion limit formula."""
    limit = (
        2.1 / (float(speed_mps) + 12.2) + 0.161
    ) * float(adhesion_coefficient) * float(adhesion_mass_kg) * 9.81
    return float(min(float(requested_force_n), limit))


def net_force(
    *,
    traction_force_n: float,
    speed_mps: float,
    resistance_type: int,
    davis_a_n: float,
    davis_b_n_per_mps: float,
    davis_c_n_per_mps2: float,
    train_mass_kg: float,
    dynamic_mass_kg: float,
    equivalent_gradient: float,
    tunnel_factor: float,
    curve_force_n: float,
    resistance_factor: float,
    wagon_count: int,
    locomotive_mass_kg: float,
) -> float:
    """Calculate net force using one of acc3's active resistance branches."""
    del dynamic_mass_kg
    speed = float(speed_mps)
    train_mass = float(train_mass_kg)
    common = train_mass * 9.81 * float(equivalent_gradient)
    common += float(tunnel_factor) * speed**2
    common += float(curve_force_n)

    if resistance_type == 1:
        resistance = (
            float(davis_a_n)
            + float(davis_b_n_per_mps) * speed
            + float(davis_c_n_per_mps2) * speed**2
        )
    elif resistance_type == 2:
        resistance = 9.81 * (
            float(resistance_factor) * train_mass / 1000.0
            + int(wagon_count) * 0.03 * (speed * 3.6) ** 2
        )
    elif resistance_type == 3:
        locomotive_mass = float(locomotive_mass_kg)
        speed_kmh = speed * 3.6
        locomotive_resistance = 9.81 * (
            float(resistance_factor) * locomotive_mass / 1000.0
            + int(wagon_count) * 0.03 * speed_kmh**2
        )
        wagon_resistance = (9.81 * (train_mass - locomotive_mass) / 1000.0) * (
            2.2 - 80.0 / (speed_kmh + 38.0) + 0.00032 * speed_kmh**2
        )
        resistance = locomotive_resistance + wagon_resistance
    else:
        raise ValueError(f"Unsupported resistance type {resistance_type}")

    return float(float(traction_force_n) - resistance - common)


def acceleration_rate(
    *,
    net_force_n: float,
    dynamic_mass_kg: float,
    max_acceleration_mps2: float,
) -> float:
    acceleration = float(net_force_n) / float(dynamic_mass_kg)
    return float(min(acceleration, float(max_acceleration_mps2)))


def forward_acceleration_profile(
    *,
    start_position_m: int,
    start_speed_mps: float,
    max_position_m: int,
    speed_envelope_mps: ArrayLike,
    vehicle_max_speed_mps: float,
    acceleration_at: Callable[[int, float], float],
) -> np.ndarray:
    """Run acc3's forward per-meter integration loop with pure inputs."""
    max_position = int(max_position_m)
    profile = np.full(max_position + 1, np.inf, dtype=float)
    envelope = np.asarray(speed_envelope_mps, dtype=float)
    position = int(start_position_m)
    speed = float(start_speed_mps)
    average_speed = speed

    while position <= max_position:
        acceleration = float(acceleration_at(position, speed))
        if speed == 0:
            profile[position] = np.sqrt(2.0 * acceleration) / 2.0
        else:
            profile[position] = average_speed

        position += 1
        if position <= max_position:
            next_speed = np.sqrt(2.0 * acceleration + speed**2)
            average_speed = (speed + next_speed) / 2.0
            speed = min(
                speed + acceleration / average_speed,
                envelope[position],
                float(vehicle_max_speed_mps),
            )

    return profile
