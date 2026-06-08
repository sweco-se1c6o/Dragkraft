from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike


def equivalent_gradient(
    *,
    boundaries_m: ArrayLike,
    gradients: ArrayLike,
    x_positions_m: ArrayLike,
    train_length_m: float,
) -> np.ndarray:
    """Calculate train-length-aware equivalent gradients."""
    boundaries = np.asarray(boundaries_m, dtype=float)
    gradient_values = np.asarray(gradients, dtype=float)
    positions = np.asarray(x_positions_m, dtype=float)

    return np.asarray(
        [
            _weighted_interval_value(
                boundaries=boundaries,
                values=gradient_values,
                x_position=position,
                train_length_m=train_length_m,
            )
            for position in positions
        ],
        dtype=float,
    )


def curve_resistance(
    *,
    boundaries_m: ArrayLike,
    radii_m: ArrayLike,
    x_positions_m: ArrayLike,
    train_length_m: float,
    train_mass_kg: float,
) -> np.ndarray:
    """Calculate curve resistance force in newtons over the train length."""
    boundaries = np.asarray(boundaries_m, dtype=float)
    radii = np.asarray(radii_m, dtype=float)
    forces = np.asarray([_curve_force(radius, train_mass_kg) for radius in radii])
    positions = np.asarray(x_positions_m, dtype=float)

    return np.asarray(
        [
            _weighted_interval_value(
                boundaries=boundaries,
                values=forces,
                x_position=position,
                train_length_m=train_length_m,
            )
            for position in positions
        ],
        dtype=float,
    )


def _weighted_interval_value(
    *,
    boundaries: np.ndarray,
    values: np.ndarray,
    x_position: float,
    train_length_m: float,
) -> float:
    interval_start = x_position - train_length_m
    interval_end = x_position
    active = np.flatnonzero(
        (interval_start < boundaries[1:]) & (interval_end >= boundaries[:-1])
    )

    if active.size == 0:
        return math.nan
    if active.size == 1:
        return float(values[active[0]])

    weighted = 0.0
    for active_index, interval_index in enumerate(active):
        if active_index == 0:
            length = boundaries[interval_index + 1] - interval_start
        elif active_index == active.size - 1:
            length = interval_end - boundaries[interval_index]
        else:
            next_interval_index = active[active_index + 1]
            length = boundaries[next_interval_index] - boundaries[interval_index]
        weighted += values[interval_index] * length

    return float(weighted / train_length_m)


def _curve_force(radius_m: float, train_mass_kg: float) -> float:
    if math.isinf(radius_m):
        return 0.0
    if radius_m < 300:
        return 4.91 / (radius_m - 30.0) * train_mass_kg
    return 6.3 / (radius_m - 55.0) * train_mass_kg
