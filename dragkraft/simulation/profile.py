from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from dragkraft.domain.track import TrackProfile
from dragkraft.units import km_to_meters, kmh_to_mps, promille_to_slope


@dataclass(frozen=True)
class ProfileVectors:
    """Meter-based route vectors using an integer-meter coordinate convention."""

    origin_km: float
    max_position_m: int
    speed_limit_positions_m: np.ndarray
    speed_limits_mps: np.ndarray
    gradient_positions_m: np.ndarray
    gradient_slopes: np.ndarray
    tunnel_rows_m: np.ndarray
    timing_point_positions_m: np.ndarray
    timing_point_names: tuple[str, ...]
    stop_positions_m: np.ndarray
    stop_names: tuple[str, ...]
    stop_times_s: np.ndarray
    curve_positions_m: np.ndarray
    curve_radii_m: np.ndarray
    signal_positions_m: np.ndarray
    signal_names: tuple[str, ...]
    signal_release_speeds_mps: np.ndarray
    signal_overlaps_m: np.ndarray
    signal_release_times_s: np.ndarray
    signal_setting_times_s: np.ndarray


def build_profile_vectors(
    profile: TrackProfile,
    *,
    flip: bool,
) -> ProfileVectors:
    """Convert a workbook profile into the meter vectors used by the kernels."""
    origin_km = profile.speed_limits[0].from_km
    speed_positions = km_to_meters(
        [(segment.from_km, segment.to_km) for segment in profile.speed_limits],
        origin_km=origin_km,
    )
    max_position = int(np.max(speed_positions))
    speed_limits = np.asarray(
        [kmh_to_mps(segment.speed_kmh) for segment in profile.speed_limits],
        dtype=float,
    )

    gradient_origin_km = profile.gradients[0].from_km
    gradient_positions = km_to_meters(
        [segment.from_km for segment in profile.gradients]
        + [profile.gradients[-1].to_km],
        origin_km=gradient_origin_km,
    )
    gradient_slopes = np.asarray(
        [promille_to_slope(segment.gradient_promille) for segment in profile.gradients],
        dtype=float,
    )

    curve_origin_km = profile.curves[0].from_km
    curve_positions = km_to_meters(
        [segment.from_km for segment in profile.curves] + [profile.curves[-1].to_km],
        origin_km=curve_origin_km,
    )
    curve_radii = np.asarray(
        [segment.radius_m for segment in profile.curves],
        dtype=float,
    )

    tunnel_positions = km_to_meters(
        [(segment.from_km, segment.to_km) for segment in profile.tunnels],
        origin_km=origin_km,
    )
    tunnel_factors = np.asarray(
        [segment.factor for segment in profile.tunnels],
        dtype=float,
    )
    tunnel_rows = np.column_stack((tunnel_positions, tunnel_factors))

    vectors = ProfileVectors(
        origin_km=origin_km,
        max_position_m=max_position,
        speed_limit_positions_m=speed_positions,
        speed_limits_mps=speed_limits,
        gradient_positions_m=gradient_positions,
        gradient_slopes=gradient_slopes,
        tunnel_rows_m=tunnel_rows,
        timing_point_positions_m=km_to_meters(
            [point.position_km for point in profile.timing_points],
            origin_km=origin_km,
        ),
        timing_point_names=tuple(point.name for point in profile.timing_points),
        stop_positions_m=km_to_meters(
            [stop.position_km for stop in profile.stops],
            origin_km=origin_km,
        ),
        stop_names=tuple(stop.name for stop in profile.stops),
        stop_times_s=np.asarray(
            [stop.stop_time_s for stop in profile.stops],
            dtype=float,
        ),
        curve_positions_m=curve_positions,
        curve_radii_m=curve_radii,
        signal_positions_m=km_to_meters(
            [signal.position_km for signal in profile.signals],
            origin_km=origin_km,
        ),
        signal_names=tuple(signal.name for signal in profile.signals),
        signal_release_speeds_mps=np.asarray(
            [kmh_to_mps(signal.release_speed_kmh) for signal in profile.signals],
            dtype=float,
        ),
        signal_overlaps_m=np.asarray(
            [signal.overlap_m for signal in profile.signals],
            dtype=float,
        ),
        signal_release_times_s=np.asarray(
            [signal.release_time_s for signal in profile.signals],
            dtype=float,
        ),
        signal_setting_times_s=np.asarray(
            [signal.setting_time_s for signal in profile.signals],
            dtype=float,
        ),
    )
    if flip:
        return _flip_profile_vectors(vectors)
    return vectors


def _flip_profile_vectors(vectors: ProfileVectors) -> ProfileVectors:
    max_position = vectors.max_position_m
    tunnel_positions = np.flip(
        max_position - vectors.tunnel_rows_m[:, :2],
        axis=(0, 1),
    )
    tunnel_rows = np.column_stack((tunnel_positions, vectors.tunnel_rows_m[:, 2][::-1]))
    return ProfileVectors(
        origin_km=vectors.origin_km,
        max_position_m=max_position,
        speed_limit_positions_m=np.flip(
            max_position - vectors.speed_limit_positions_m,
            axis=(0, 1),
        ),
        speed_limits_mps=vectors.speed_limits_mps[::-1],
        gradient_positions_m=(max_position - vectors.gradient_positions_m)[::-1],
        gradient_slopes=(-vectors.gradient_slopes)[::-1],
        tunnel_rows_m=tunnel_rows,
        timing_point_positions_m=(
            max_position - vectors.timing_point_positions_m
        )[::-1],
        timing_point_names=tuple(reversed(vectors.timing_point_names)),
        stop_positions_m=(max_position - vectors.stop_positions_m)[::-1],
        stop_names=tuple(reversed(vectors.stop_names)),
        stop_times_s=vectors.stop_times_s[::-1],
        curve_positions_m=(max_position - vectors.curve_positions_m)[::-1],
        curve_radii_m=vectors.curve_radii_m[::-1],
        signal_positions_m=(max_position - vectors.signal_positions_m)[::-1],
        signal_names=tuple(reversed(vectors.signal_names)),
        signal_release_speeds_mps=vectors.signal_release_speeds_mps[::-1],
        signal_overlaps_m=vectors.signal_overlaps_m[::-1],
        signal_release_times_s=vectors.signal_release_times_s[::-1],
        signal_setting_times_s=vectors.signal_setting_times_s[::-1],
    )


def build_sth_profile(*, speeds_mps: ArrayLike, positions_m: ArrayLike) -> np.ndarray:
    """Build the base STH row using the position-slice convention."""
    speeds = np.asarray(speeds_mps, dtype=float)
    positions = np.asarray(positions_m, dtype=int)
    max_position = int(np.max(positions))
    profile = np.full(max_position + 1, np.inf, dtype=float)
    for speed, (start, end) in zip(speeds, positions, strict=True):
        profile[start + 1 : end + 1] = speed
    return profile


def build_tunnel_factor(*, tunnel_rows_m: ArrayLike, max_position_m: int) -> np.ndarray:
    """Build a padded tunnel-factor vector from rounded meter rows."""
    rows = np.asarray(tunnel_rows_m, dtype=float)
    factors = np.zeros(int(max_position_m) + 1, dtype=float)
    for start, end, factor in rows:
        factors[int(start) : int(end) + 1] = factor
    return factors
