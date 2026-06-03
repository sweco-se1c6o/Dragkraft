from __future__ import annotations

import numpy as np

from dragkraft.units import km_to_legacy_meters, kmh_to_mps, promille_to_slope


def test_kmh_to_mps() -> None:
    assert kmh_to_mps(40) == 40 / 3.6


def test_promille_to_slope() -> None:
    assert promille_to_slope(12.5) == 0.0125


def test_km_to_legacy_meters_uses_matlab_rounding() -> None:
    result = km_to_legacy_meters(np.array([100.0005, 100.0015]), origin_km=100.0)

    assert result.tolist() == [1, 2]
