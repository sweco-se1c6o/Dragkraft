from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def build_sth_profile(*, speeds_mps: ArrayLike, positions_m: ArrayLike) -> np.ndarray:
    """Build the base STH row using MATLAB's position-slice convention."""
    speeds = np.asarray(speeds_mps, dtype=float)
    positions = np.asarray(positions_m, dtype=int)
    max_position = int(np.max(positions))
    profile = np.full(max_position + 1, np.inf, dtype=float)
    for speed, (start, end) in zip(speeds, positions, strict=True):
        profile[start + 1 : end + 1] = speed
    return profile


def build_tunnel_factor(*, tunnel_rows_m: ArrayLike, max_position_m: int) -> np.ndarray:
    """Build a padded tunnel-factor vector from rounded legacy meter rows."""
    rows = np.asarray(tunnel_rows_m, dtype=float)
    factors = np.zeros(int(max_position_m) + 1, dtype=float)
    for start, end, factor in rows:
        factors[int(start) : int(end) + 1] = factor
    return factors
