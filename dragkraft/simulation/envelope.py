from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.train import TrainConfig
from dragkraft.simulation.braking import braking_curve
from dragkraft.simulation.profile import LegacyProfileVectors, build_sth_profile


@dataclass(frozen=True)
class InitialSpeedEnvelope:
    candidate_profiles_mps: np.ndarray
    speed_envelope_mps: np.ndarray


def build_initial_speed_envelope(
    *,
    vectors: LegacyProfileVectors,
    train: TrainConfig,
    settings: SimulationSettings,
    equivalent_gradient: ArrayLike,
) -> InitialSpeedEnvelope:
    max_position = int(vectors.max_position_m)
    gradients = np.asarray(equivalent_gradient, dtype=float)
    max_speed = float(np.max(vectors.speed_limits_mps))
    rows = [
        build_sth_profile(
            speeds_mps=vectors.speed_limits_mps,
            positions_m=vectors.speed_limit_positions_m,
        )
    ]

    for index in range(len(vectors.speed_limits_mps) - 1):
        row = np.full(max_position + 1, np.inf, dtype=float)
        current_speed = float(vectors.speed_limits_mps[index])
        next_speed = float(vectors.speed_limits_mps[index + 1])
        boundary = int(vectors.speed_limit_positions_m[index, 1])

        if current_speed < next_speed:
            if settings.use_train_length_delay:
                end = min(max_position, boundary + int(train.train_length_m))
                row[boundary : end + 1] = current_speed
        else:
            offset = _advance_offset_for_speed(next_speed, settings)
            if settings.use_distance_before_signal:
                start = max(1, boundary + offset)
                row[start : boundary + 1] = next_speed
            row = np.minimum(
                row,
                braking_curve(
                    target_position_m=boundary,
                    start_offset_m=offset,
                    retardation_mps2=train.braking_decelerations_mps2,
                    speed_intervals_mps=train.braking_speed_intervals_mps,
                    target_speed_mps=next_speed,
                    max_speed_mps=max_speed,
                    equivalent_gradient=gradients,
                    min_deceleration_mps2=train.min_deceleration_mps2,
                    max_deceleration_mps2=train.max_deceleration_mps2,
                    max_position_m=max_position,
                ),
            )
        rows.append(row)

    for stop_position in vectors.stop_positions_m:
        rows.append(
            braking_curve(
                target_position_m=int(stop_position),
                start_offset_m=0,
                retardation_mps2=train.braking_decelerations_mps2,
                speed_intervals_mps=train.braking_speed_intervals_mps,
                target_speed_mps=0.0,
                max_speed_mps=max_speed,
                equivalent_gradient=gradients,
                min_deceleration_mps2=train.min_deceleration_mps2,
                max_deceleration_mps2=train.max_deceleration_mps2,
                max_position_m=max_position,
            )
        )

    candidates = np.vstack(rows)
    return InitialSpeedEnvelope(
        candidate_profiles_mps=candidates,
        speed_envelope_mps=np.min(candidates, axis=0),
    )


def _advance_offset_for_speed(
    target_speed_mps: float,
    settings: SimulationSettings,
) -> int:
    if not settings.use_distance_before_signal:
        return 0
    if not settings.use_tav_distance:
        return -400
    if target_speed_mps < settings.switch_speed_mps:
        return -_legacy_round(target_speed_mps * settings.freight_signal_advance_s_per_mps)
    return -_legacy_round(
        target_speed_mps * settings.freight_signal_advance2_s_per_mps
        + settings.freight_signal_advance2_m
    )


def _legacy_round(value: float) -> int:
    numeric = float(value)
    return int(np.sign(numeric) * np.floor(abs(numeric) + 0.5 + 1e-9))
