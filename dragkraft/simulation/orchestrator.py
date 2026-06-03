from __future__ import annotations

from pathlib import Path

import numpy as np

from dragkraft.domain.result import SimulationResult, TimingPassage
from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.track import TrackProfile
from dragkraft.domain.train import TrainConfig
from dragkraft.io.excel_reader import read_track_profile
from dragkraft.simulation.acceleration import forward_acceleration_profile
from dragkraft.simulation.blocks import block_occupation
from dragkraft.simulation.envelope import build_initial_speed_envelope
from dragkraft.simulation.route import (
    build_acceleration_callback,
    prepare_route_vectors,
)


def simulate_workbook(
    *,
    workbook_path: str | Path,
    train: TrainConfig,
    settings: SimulationSettings,
) -> SimulationResult:
    profile = read_track_profile(
        workbook_path,
        settings.sheet_name,
        speed_override_kmh=settings.speed_override_kmh,
    )
    return simulate_profile(
        profile=profile,
        train=train,
        settings=settings,
    )


def simulate_profile(
    *,
    profile: TrackProfile,
    train: TrainConfig,
    settings: SimulationSettings,
) -> SimulationResult:
    route = prepare_route_vectors(
        profile=profile,
        train=train,
        flip=settings.flip_profiles,
    )
    initial = build_initial_speed_envelope(
        vectors=route.vectors,
        train=train,
        settings=settings,
        equivalent_gradient=route.equivalent_gradient,
    )
    acceleration_envelope = initial.speed_envelope_mps.copy()
    acceleration_envelope[route.vectors.stop_positions_m.astype(int)] = 0.0
    acceleration = forward_acceleration_profile(
        start_position_m=1,
        start_speed_mps=min(
            acceleration_envelope[1],
            train.vehicle_max_speed_mps,
        ),
        max_position_m=route.vectors.max_position_m,
        speed_envelope_mps=acceleration_envelope,
        vehicle_max_speed_mps=train.vehicle_max_speed_mps,
        acceleration_at=build_acceleration_callback(route=route, train=train),
    )
    running_speed = np.minimum(
        np.minimum(initial.speed_envelope_mps, acceleration),
        train.vehicle_max_speed_mps,
    )
    running_speed = running_speed / settings.short_time_margin
    running_speed[0] = np.inf

    time_s_per_m = np.zeros_like(running_speed)
    active = np.isfinite(running_speed) & (running_speed > 0)
    time_s_per_m[active] = 1.0 / running_speed[active]
    for position, stop_time in zip(
        route.vectors.stop_positions_m,
        route.vectors.stop_times_s,
        strict=True,
    ):
        time_s_per_m[int(position)] += float(stop_time)

    cumulative_time = np.cumsum(time_s_per_m) + settings.time_offset_s
    speed_profile = running_speed.copy()
    speed_profile[route.vectors.stop_positions_m.astype(int)] = 0.0
    timing_passages = tuple(
        TimingPassage(
            position_m=int(position),
            name=name,
            time_s=float(cumulative_time[int(position)]),
        )
        for position, name in zip(
            route.vectors.timing_point_positions_m,
            route.vectors.timing_point_names,
            strict=True,
        )
    )
    blocks = block_occupation(
        signal_positions_m=route.vectors.signal_positions_m,
        signal_names=route.vectors.signal_names,
        release_speeds_mps=route.vectors.signal_release_speeds_mps,
        overlaps_m=route.vectors.signal_overlaps_m,
        release_times_s=route.vectors.signal_release_times_s,
        setting_times_s=route.vectors.signal_setting_times_s,
        speed_profile_mps=speed_profile,
        cumulative_time_s=cumulative_time,
        retardation_mps2=train.braking_decelerations_mps2,
        speed_intervals_mps=train.braking_speed_intervals_mps,
        max_speed_mps=float(np.max(route.vectors.speed_limits_mps)),
        train_length_m=train.train_length_m,
        equivalent_gradient=route.equivalent_gradient,
        min_deceleration_mps2=settings.min_signal_deceleration_mps2,
        max_deceleration_mps2=train.max_deceleration_mps2,
        speed_tolerance_mps=settings.speed_tolerance_mps,
        reserve_before_arrival_s=settings.reserve_before_arrival_s,
    )
    return SimulationResult(
        route=route,
        initial_envelope=initial,
        acceleration_profile_mps=acceleration,
        running_speed_profile_mps=running_speed,
        speed_profile_mps=speed_profile,
        time_s_per_m=time_s_per_m,
        cumulative_time_s=cumulative_time,
        timing_passages=timing_passages,
        block_occupation=blocks,
    )
