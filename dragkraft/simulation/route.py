from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from dragkraft.domain.track import TrackProfile
from dragkraft.domain.train import TrainConfig
from dragkraft.simulation.acceleration import (
    acceleration_rate,
    adhesion_limited_force,
    net_force,
    traction_force_type1,
    traction_force_type2,
)
from dragkraft.simulation.profile import (
    ProfileVectors,
    build_profile_vectors,
    build_tunnel_factor,
)
from dragkraft.simulation.resistance import curve_resistance, equivalent_gradient


@dataclass(frozen=True)
class PreparedRoute:
    vectors: ProfileVectors
    x_positions_m: np.ndarray
    tunnel_factor: np.ndarray
    equivalent_gradient: np.ndarray
    curve_resistance_n: np.ndarray


def prepare_route_vectors(
    *,
    profile: TrackProfile,
    train: TrainConfig,
    flip: bool,
) -> PreparedRoute:
    vectors = build_profile_vectors(profile, flip=flip)
    x_positions_m = np.arange(vectors.max_position_m + 1, dtype=int)
    tunnel_factor = build_tunnel_factor(
        tunnel_rows_m=vectors.tunnel_rows_m,
        max_position_m=vectors.max_position_m,
    )
    equivalent = equivalent_gradient(
        boundaries_m=vectors.gradient_positions_m,
        gradients=vectors.gradient_slopes,
        x_positions_m=x_positions_m,
        train_length_m=train.train_length_m,
    )
    curve_force = curve_resistance(
        boundaries_m=vectors.curve_positions_m,
        radii_m=vectors.curve_radii_m,
        x_positions_m=x_positions_m,
        train_length_m=train.train_length_m,
        train_mass_kg=train.train_mass_kg,
    )
    return PreparedRoute(
        vectors=vectors,
        x_positions_m=x_positions_m,
        tunnel_factor=tunnel_factor,
        equivalent_gradient=equivalent,
        curve_resistance_n=curve_force,
    )


def build_acceleration_callback(
    *,
    route: PreparedRoute,
    train: TrainConfig,
) -> Callable[[int, float], float]:
    def acceleration_at(position_m: int, speed_mps: float) -> float:
        traction = _traction_force(train=train, speed_mps=speed_mps)
        traction = adhesion_limited_force(
            requested_force_n=traction,
            speed_mps=speed_mps,
            adhesion_coefficient=train.adhesion_coefficient,
            adhesion_mass_kg=train.adhesion_mass_kg,
        )
        force = net_force(
            traction_force_n=traction,
            speed_mps=speed_mps,
            resistance_type=train.resistance_type,
            davis_a_n=train.davis_a_n,
            davis_b_n_per_mps=train.davis_b_n_per_mps,
            davis_c_n_per_mps2=train.davis_c_n_per_mps2,
            train_mass_kg=train.train_mass_kg,
            dynamic_mass_kg=train.dynamic_mass_kg,
            equivalent_gradient=route.equivalent_gradient[position_m],
            tunnel_factor=route.tunnel_factor[position_m],
            curve_force_n=route.curve_resistance_n[position_m],
            resistance_factor=train.resistance_factor,
            wagon_count=train.extra_wagon_count,
            locomotive_mass_kg=train.locomotive_mass_kg,
        )
        return acceleration_rate(
            net_force_n=force,
            dynamic_mass_kg=train.dynamic_mass_kg,
            max_acceleration_mps2=train.max_acceleration_mps2,
        )

    return acceleration_at


def _traction_force(*, train: TrainConfig, speed_mps: float) -> float:
    if train.traction_model_type == 1:
        return traction_force_type1(
            speed_mps=speed_mps,
            max_force_n=train.max_force_n,
            continuous_power_w=train.continuous_power_w,
            start_force_n=train.start_force_n,
            start_force_max_speed_mps=train.start_force_max_speed_mps,
        )
    if train.traction_model_type == 2:
        return traction_force_type2(
            speed_mps,
            train.traction_intercepts_n,
            train.traction_slopes_n_per_mps,
            train.traction_speed_intervals_mps,
        )
    raise ValueError(f"Unsupported traction model type {train.traction_model_type}")
