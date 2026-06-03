from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike


def braking_curve(
    *,
    target_position_m: int,
    start_offset_m: int,
    retardation_mps2: ArrayLike,
    speed_intervals_mps: ArrayLike,
    target_speed_mps: float,
    max_speed_mps: float,
    equivalent_gradient: ArrayLike,
    min_deceleration_mps2: float,
    max_deceleration_mps2: float,
    max_position_m: int,
) -> np.ndarray:
    """Calculate a MATLAB-compatible backward braking curve."""
    curve = np.full(int(max_position_m) + 1, np.inf, dtype=float)
    retardation = np.asarray(retardation_mps2, dtype=float)
    intervals = np.asarray(speed_intervals_mps, dtype=float)
    gradients = np.asarray(equivalent_gradient, dtype=float)
    speed = float(target_speed_mps)
    offset = int(start_offset_m)
    target_position = int(target_position_m)

    while speed <= float(max_speed_mps) + 1.0:
        position = target_position + offset
        if position < 1:
            break

        acceleration = _deceleration_for_speed(speed, retardation, intervals)
        acceleration += 9.82 * gradients[position]
        acceleration = max(acceleration, float(min_deceleration_mps2))
        acceleration = min(acceleration, float(max_deceleration_mps2))
        curve[position] = math.sqrt(2.0 * acceleration) / 2.0 if speed == 0 else speed

        offset -= 1
        next_speed = math.sqrt(2.0 * acceleration + speed**2)
        speed += acceleration / ((speed + next_speed) / 2.0)

    return curve


def _deceleration_for_speed(
    speed_mps: float,
    retardation: np.ndarray,
    intervals: np.ndarray,
) -> float:
    active = (intervals[:, 1] > speed_mps) & (intervals[:, 0] <= speed_mps)
    if not np.any(active):
        raise ValueError(f"No retardation interval contains speed {speed_mps}")
    return float(retardation[np.flatnonzero(active)[0]])
