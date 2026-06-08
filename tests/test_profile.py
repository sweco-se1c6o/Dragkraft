from __future__ import annotations

import math

import numpy as np
import pytest

from dragkraft.domain.track import (
    CurveSegment,
    GradientSegment,
    SignalBlock,
    SpeedLimitSegment,
    Stop,
    TimingPoint,
    TrackProfile,
    TunnelSegment,
)
from dragkraft.simulation.profile import (
    build_profile_vectors,
    build_sth_profile,
    build_tunnel_factor,
)


def test_build_sth_profile_uses_position_slices() -> None:
    result = build_sth_profile(
        speeds_mps=np.array([10.0, 20.0]),
        positions_m=np.array([[0, 3], [3, 5]]),
    )

    assert result.tolist() == [float("inf"), 10.0, 10.0, 10.0, 20.0, 20.0]


def test_build_tunnel_factor_fills_inclusive_slices() -> None:
    result = build_tunnel_factor(
        tunnel_rows_m=np.array([[2, 4, 7.5]]),
        max_position_m=5,
    )

    assert result.tolist() == [0.0, 0.0, 7.5, 7.5, 7.5, 0.0]


def test_build_profile_vectors_converts_workbook_units_without_flip() -> None:
    vectors = build_profile_vectors(_sample_track_profile(), flip=False)

    assert vectors.max_position_m == 5
    assert vectors.speed_limit_positions_m.tolist() == [[0, 3], [3, 5]]
    assert vectors.speed_limits_mps.tolist() == pytest.approx([10.0, 20.0])
    assert vectors.gradient_positions_m.tolist() == [0, 2, 5]
    assert vectors.gradient_slopes.tolist() == pytest.approx([0.005, -0.003])
    assert vectors.tunnel_rows_m.tolist() == [[1.0, 4.0, 7.5]]
    assert vectors.timing_point_positions_m.tolist() == [2]
    assert vectors.timing_point_names == ("TP",)
    assert vectors.stop_positions_m.tolist() == [4]
    assert vectors.stop_names == ("Stop",)
    assert vectors.stop_times_s.tolist() == pytest.approx([30.0])
    assert vectors.curve_positions_m.tolist() == [0, 2, 5]
    assert vectors.curve_radii_m.tolist() == [250.0, math.inf]
    assert vectors.signal_positions_m.tolist() == [1, 4]
    assert vectors.signal_names == ("MB1", "MB2")
    assert vectors.signal_release_speeds_mps.tolist() == pytest.approx(
        [5.0 / 3.6, 10.0 / 3.6]
    )


def test_build_profile_vectors_flips_positions_values_and_names() -> None:
    vectors = build_profile_vectors(_sample_track_profile(), flip=True)

    assert vectors.max_position_m == 5
    assert vectors.speed_limit_positions_m.tolist() == [[0, 2], [2, 5]]
    assert vectors.speed_limits_mps.tolist() == pytest.approx([20.0, 10.0])
    assert vectors.gradient_positions_m.tolist() == [0, 3, 5]
    assert vectors.gradient_slopes.tolist() == pytest.approx([0.003, -0.005])
    assert vectors.curve_positions_m.tolist() == [0, 3, 5]
    assert vectors.curve_radii_m.tolist() == [math.inf, 250.0]
    assert vectors.timing_point_positions_m.tolist() == [3]
    assert vectors.stop_positions_m.tolist() == [1]
    assert vectors.signal_positions_m.tolist() == [1, 4]
    assert vectors.signal_names == ("MB2", "MB1")
    assert vectors.signal_release_speeds_mps.tolist() == pytest.approx(
        [10.0 / 3.6, 5.0 / 3.6]
    )


def _sample_track_profile() -> TrackProfile:
    return TrackProfile(
        sheet_name="Example",
        speed_limits=(
            SpeedLimitSegment(10.0, 10.003, 36.0),
            SpeedLimitSegment(10.003, 10.005, 72.0),
        ),
        gradients=(
            GradientSegment(10.0, 10.002, 5.0),
            GradientSegment(10.002, 10.005, -3.0),
        ),
        tunnels=(TunnelSegment(10.001, 10.004, 7.5),),
        timing_points=(TimingPoint(10.002, "TP"),),
        stops=(Stop(10.004, "Stop", 30.0),),
        curves=(
            CurveSegment(10.0, 10.002, 250.0),
            CurveSegment(10.002, 10.005, math.inf),
        ),
        signals=(
            SignalBlock(10.001, "MB1", 5.0, 12.0, 3.0, 4.0),
            SignalBlock(10.004, "MB2", 10.0, 13.0, 5.0, 6.0),
        ),
    )
