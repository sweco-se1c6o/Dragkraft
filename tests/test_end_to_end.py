from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from dragkraft.simulation.orchestrator import simulate_workbook
from dragkraft.vehicles.scenarios import default_scenario, freight_train


LOCAL_WORKBOOK = Path(__file__).resolve().parents[1] / "old" / "luleaHamn3.xlsx"
BASELINE_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "default_scenario"
)


def test_default_scenario_matches_baseline() -> None:
    if not LOCAL_WORKBOOK.exists():
        pytest.skip("reference workbook is local-only because old/ is git-ignored")

    result = simulate_workbook(
        workbook_path=LOCAL_WORKBOOK,
        train=freight_train(),
        settings=default_scenario(),
    )
    summary = _read_summary(BASELINE_DIR / "summary.csv")
    timing_points = _read_rows(BASELINE_DIR / "timing_points.csv")
    blocks = _read_rows(BASELINE_DIR / "block_occupation.csv")
    speed_profile = _read_rows(BASELINE_DIR / "speed_profile.csv")

    assert result.cumulative_time_s[-1] == pytest.approx(
        summary["total_time_s"],
        abs=1.0,
    )
    assert result.route.vectors.max_position_m == int(summary["route_length_m"])
    assert len(result.timing_passages) == int(summary["timing_point_count"])
    assert len(result.block_occupation.occupations) == int(summary["block_count"])

    for actual, expected in zip(result.timing_passages, timing_points, strict=True):
        assert actual.position_m == int(expected["position_m"])
        assert actual.name == expected["name"]
        assert actual.time_s == pytest.approx(float(expected["time_s"]), abs=1.0)

    for actual, expected in zip(
        result.block_occupation.occupations,
        blocks,
        strict=True,
    ):
        assert actual.name == expected["name"]
        assert actual.signal_position_m == int(expected["signal_position_m"])
        assert actual.intersection_position_m == int(
            float(expected["intersection_position_m"])
        )
        assert actual.booking_time_s == pytest.approx(
            float(expected["booking_time_s"]),
            abs=1.0,
        )
        assert actual.arrival_time_s == pytest.approx(
            float(expected["arrival_time_s"]),
            abs=1.0,
        )
        assert actual.release_time_s == pytest.approx(
            float(expected["release_time_s"]),
            abs=1.0,
        )

    expected_speed = np.asarray([float(row["speed_mps"]) for row in speed_profile])
    expected_time = np.asarray([float(row["time_s_per_m"]) for row in speed_profile])
    expected_cumulative = np.asarray(
        [float(row["cumulative_time_s"]) for row in speed_profile]
    )
    expected_gradient = np.asarray(
        [float(row["equivalent_gradient"]) for row in speed_profile]
    )
    expected_curve_force = np.asarray(
        [float(row["curve_force_n"]) for row in speed_profile]
    )

    np.testing.assert_allclose(result.speed_profile_mps[1:], expected_speed, atol=0.01)
    np.testing.assert_allclose(result.time_s_per_m[1:], expected_time, atol=1e-9)
    np.testing.assert_allclose(
        result.cumulative_time_s[1:],
        expected_cumulative,
        atol=1.0,
    )
    np.testing.assert_allclose(
        result.route.equivalent_gradient[1:],
        expected_gradient,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result.route.curve_resistance_n[1:],
        expected_curve_force,
        atol=1e-9,
    )


def test_overheavy_consist_returns_partial_result_with_stall() -> None:
    if not LOCAL_WORKBOOK.exists():
        pytest.skip("reference workbook is local-only because old/ is git-ignored")

    settings = replace(default_scenario(), extra_wagon_count=30)
    train = freight_train(extra_wagons=30)

    result = simulate_workbook(
        workbook_path=LOCAL_WORKBOOK,
        train=train,
        settings=settings,
    )

    # The 30-wagon consist stalls on the grade rather than raising or producing nan.
    assert result.stall is not None
    assert result.stall.position_m == 2581
    # The partial profile is finite up to the stall and zeroed beyond it.
    stall_pos = result.stall.position_m
    assert np.all(np.isfinite(result.cumulative_time_s))
    assert np.isfinite(result.speed_profile_mps[stall_pos])
    assert np.all(result.speed_profile_mps[stall_pos + 1 :] == 0.0)
    # Only infrastructure actually reached is reported.
    assert all(p.position_m <= stall_pos for p in result.timing_passages)
    assert all(
        b.signal_position_m <= stall_pos
        for b in result.block_occupation.occupations
    )


def _read_summary(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as file:
        return {row["key"]: float(row["value"]) for row in csv.DictReader(file)}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
