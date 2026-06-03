from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dragkraft.simulation.envelope import InitialSpeedEnvelope
from dragkraft.simulation.route import PreparedRoute


@dataclass(frozen=True)
class TimingPassage:
    position_m: int
    name: str
    time_s: float


@dataclass(frozen=True)
class SimulationResult:
    route: PreparedRoute
    initial_envelope: InitialSpeedEnvelope
    acceleration_profile_mps: np.ndarray
    running_speed_profile_mps: np.ndarray
    speed_profile_mps: np.ndarray
    time_s_per_m: np.ndarray
    cumulative_time_s: np.ndarray
    timing_passages: tuple[TimingPassage, ...]
