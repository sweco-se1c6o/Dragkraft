from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike

from dragkraft.domain.result import BlockOccupation, BlockOccupationResult
from dragkraft.simulation.braking import braking_curve


def block_occupation(
    *,
    signal_positions_m: ArrayLike,
    signal_names: tuple[str, ...],
    release_speeds_mps: ArrayLike,
    overlaps_m: ArrayLike,
    release_times_s: ArrayLike,
    setting_times_s: ArrayLike,
    speed_profile_mps: ArrayLike,
    cumulative_time_s: ArrayLike,
    retardation_mps2: ArrayLike,
    speed_intervals_mps: ArrayLike,
    max_speed_mps: float,
    train_length_m: float,
    equivalent_gradient: ArrayLike,
    min_deceleration_mps2: float,
    max_deceleration_mps2: float,
    speed_tolerance_mps: float,
    reserve_before_arrival_s: float,
) -> BlockOccupationResult:
    positions = np.asarray(signal_positions_m, dtype=int)
    release_speeds = np.asarray(release_speeds_mps, dtype=float)
    overlaps = np.asarray(overlaps_m, dtype=float)
    release_times = np.asarray(release_times_s, dtype=float)
    setting_times = np.asarray(setting_times_s, dtype=float)
    speed_profile = np.asarray(speed_profile_mps, dtype=float)
    cumulative_time = np.asarray(cumulative_time_s, dtype=float)

    curves = np.full((positions.size, speed_profile.size), np.inf, dtype=float)
    rows: list[BlockOccupation] = []
    for index, position in enumerate(positions):
        curve = braking_curve(
            target_position_m=int(position),
            start_offset_m=0,
            retardation_mps2=retardation_mps2,
            speed_intervals_mps=speed_intervals_mps,
            target_speed_mps=0.0,
            max_speed_mps=max_speed_mps,
            equivalent_gradient=equivalent_gradient,
            min_deceleration_mps2=min_deceleration_mps2,
            max_deceleration_mps2=max_deceleration_mps2,
            max_position_m=speed_profile.size - 1,
        )
        curve = np.maximum(float(release_speeds[index]), curve)
        curves[index, :] = curve

        speed_diff = np.full(speed_profile.shape, np.inf, dtype=float)
        finite = np.isfinite(speed_profile) & np.isfinite(curve)
        speed_diff[finite] = np.abs(speed_profile[finite] - curve[finite])
        matches = np.flatnonzero(speed_diff <= float(speed_tolerance_mps))
        if matches.size:
            intersection = int(matches[0])
            difference = float(speed_diff[intersection])
            booking = float(cumulative_time[intersection] - setting_times[index])
        else:
            intersection = None
            difference = math.nan
            booking = float(cumulative_time[position] - reserve_before_arrival_s)

        release_position = int(position + round(float(train_length_m)) + overlaps[index])
        rows.append(
            BlockOccupation(
                name=signal_names[index],
                signal_position_m=int(position),
                speed_difference_mps=difference,
                intersection_position_m=intersection,
                booking_time_s=booking,
                arrival_time_s=float(cumulative_time[position]),
                release_time_s=float(
                    cumulative_time[release_position] + release_times[index]
                ),
            )
        )

    return BlockOccupationResult(
        occupations=tuple(rows),
        mb_braking_curves_mps=curves,
    )
