from __future__ import annotations

import numpy as np

from dragkraft.domain.result import SimulationResult, TimingPassage
from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.track import TrackProfile
from dragkraft.domain.train import TrainConfig
from dragkraft.simulation.acceleration import forward_acceleration_profile
from dragkraft.simulation.envelope import build_initial_speed_envelope
from dragkraft.simulation.route import (
    build_acceleration_callback,
    prepare_route_vectors,
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
    acceleration = forward_acceleration_profile(
        start_position_m=1,
        start_speed_mps=min(
            initial.speed_envelope_mps[1],
            train.vehicle_max_speed_mps,
        ),
        max_position_m=route.vectors.max_position_m,
        speed_envelope_mps=initial.speed_envelope_mps,
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
    return SimulationResult(
        route=route,
        initial_envelope=initial,
        acceleration_profile_mps=acceleration,
        running_speed_profile_mps=running_speed,
        speed_profile_mps=speed_profile,
        time_s_per_m=time_s_per_m,
        cumulative_time_s=cumulative_time,
        timing_passages=timing_passages,
    )
