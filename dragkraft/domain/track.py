from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpeedLimitSegment:
    from_km: float
    to_km: float
    speed_kmh: float


@dataclass(frozen=True)
class GradientSegment:
    from_km: float
    to_km: float
    gradient_promille: float


@dataclass(frozen=True)
class TunnelSegment:
    from_km: float
    to_km: float
    factor: float


@dataclass(frozen=True)
class TimingPoint:
    position_km: float
    name: str


@dataclass(frozen=True)
class Stop:
    position_km: float
    name: str
    stop_time_s: float


@dataclass(frozen=True)
class CurveSegment:
    from_km: float
    to_km: float
    radius_m: float


@dataclass(frozen=True)
class SignalBlock:
    position_km: float
    name: str
    release_speed_kmh: float
    overlap_m: float
    release_time_s: float
    setting_time_s: float


@dataclass(frozen=True)
class TrackProfile:
    sheet_name: str
    speed_limits: tuple[SpeedLimitSegment, ...]
    gradients: tuple[GradientSegment, ...]
    tunnels: tuple[TunnelSegment, ...]
    timing_points: tuple[TimingPoint, ...]
    stops: tuple[Stop, ...]
    curves: tuple[CurveSegment, ...]
    signals: tuple[SignalBlock, ...]
