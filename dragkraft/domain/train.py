from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TrainConfig:
    name: str
    locomotive_count: int
    locomotive_mass_kg: float
    extra_wagon_count: int
    wagon_mass_kg: float
    train_mass_kg: float
    dynamic_mass_kg: float
    adhesion_mass_kg: float
    adhesion_coefficient: float
    train_length_m: float
    resistance_type: int
    davis_a_n: float
    davis_b_n_per_mps: float
    davis_c_n_per_mps2: float
    resistance_factor: float
    traction_model_type: int
    max_force_n: float
    start_force_n: float
    start_force_max_speed_mps: float
    continuous_power_w: float
    traction_speed_intervals_mps: np.ndarray
    traction_force_intervals_n: np.ndarray
    traction_intercepts_n: np.ndarray
    traction_slopes_n_per_mps: np.ndarray
    min_deceleration_mps2: float
    max_deceleration_mps2: float
    max_acceleration_mps2: float
    vehicle_max_speed_mps: float
    braking_speed_intervals_mps: np.ndarray
    braking_decelerations_mps2: np.ndarray
