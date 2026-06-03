from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from dragkraft.simulation.orchestrator import simulate_workbook
from dragkraft.vehicles.legacy_cases import default_nyprofil_scenario, legacy_freight_20


LEGACY_WORKBOOK = Path(__file__).resolve().parents[1] / "old" / "luleaHamn3.xlsx"
BASELINE_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "matlab_nyprofil_default"
)


def test_default_nyprofil_matches_matlab_baseline() -> None:
    if not LEGACY_WORKBOOK.exists():
        pytest.skip("legacy workbook is local-only because old/ is git-ignored")

    result = simulate_workbook(
        workbook_path=LEGACY_WORKBOOK,
        train=legacy_freight_20(),
        settings=default_nyprofil_scenario(),
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


def _read_summary(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as file:
        return {row["key"]: float(row["value"]) for row in csv.DictReader(file)}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
