from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def kmh_to_mps(speed_kmh: float) -> float:
    return float(speed_kmh) / 3.6


def promille_to_slope(gradient_promille: float) -> float:
    return float(gradient_promille) / 1000.0


def km_to_legacy_meters(values_km: ArrayLike, *, origin_km: float) -> np.ndarray:
    """Convert route kilometers to MATLAB-style rounded meter positions."""
    meters = (np.asarray(values_km, dtype=float) - float(origin_km)) * 1000.0
    rounded = np.sign(meters) * np.floor(np.abs(meters) + 0.5 + 1e-9)
    return rounded.astype(int)
