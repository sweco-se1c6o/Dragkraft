from __future__ import annotations

import numpy as np

from dragkraft.simulation.profile import build_sth_profile, build_tunnel_factor


def test_build_sth_profile_uses_matlab_position_slices() -> None:
    result = build_sth_profile(
        speeds_mps=np.array([10.0, 20.0]),
        positions_m=np.array([[0, 3], [3, 5]]),
    )

    assert result.tolist() == [float("inf"), 10.0, 10.0, 10.0, 20.0, 20.0]


def test_build_tunnel_factor_fills_inclusive_legacy_slices() -> None:
    result = build_tunnel_factor(
        tunnel_rows_m=np.array([[2, 4, 7.5]]),
        max_position_m=5,
    )

    assert result.tolist() == [0.0, 0.0, 7.5, 7.5, 7.5, 0.0]
