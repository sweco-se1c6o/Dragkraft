from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationSettings:
    workbook_name: str
    sheet_name: str
    train_name: str
    extra_wagon_count: int
    speed_override_kmh: float
    flip_profiles: bool
    altitude_at_start_m: float
    time_offset_s: float
    short_time_margin: float
    use_train_length_delay: bool
    use_distance_before_signal: bool
    use_tav_distance: bool
    freight_signal_advance_s_per_mps: float
    freight_signal_advance2_s_per_mps: float
    freight_signal_advance2_m: float
    switch_speed_mps: float
    use_min_time_to_hold_speed: bool
    min_time_to_hold_speed_s: float
    speed_tolerance_mps: float
    min_signal_deceleration_mps2: float
    reserve_before_arrival_s: float
