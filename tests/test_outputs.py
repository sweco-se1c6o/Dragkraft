from __future__ import annotations

import csv
import json

import numpy as np
import pytest

from dragkraft.domain.result import (
    BlockOccupation,
    BlockOccupationResult,
    SimulationResult,
    TimingPassage,
)
from dragkraft.io.outputs import write_simulation_outputs


def test_write_simulation_outputs_creates_summary_timing_blocks_and_speed_profile(
    tmp_path,
) -> None:
    result = SimulationResult(
        route=None,
        initial_envelope=None,
        acceleration_profile_mps=np.array([np.inf, 1.0, 2.0]),
        running_speed_profile_mps=np.array([np.inf, 1.0, 2.0]),
        speed_profile_mps=np.array([np.inf, 1.0, 0.0]),
        time_s_per_m=np.array([0.0, 1.0, 30.5]),
        cumulative_time_s=np.array([0.0, 1.0, 31.5]),
        timing_passages=(TimingPassage(position_m=2, name="TP", time_s=31.5),),
        block_occupation=BlockOccupationResult(
            occupations=(
                BlockOccupation(
                    name="MB1",
                    signal_position_m=2,
                    speed_difference_mps=np.nan,
                    intersection_position_m=None,
                    booking_time_s=11.5,
                    arrival_time_s=31.5,
                    release_time_s=40.0,
                ),
            ),
            mb_braking_curves_mps=np.array([[np.inf, 1.0, 0.5]]),
        ),
    )

    paths = write_simulation_outputs(result=result, output_dir=tmp_path)

    assert set(paths) == {
        "summary",
        "timing_points",
        "block_occupation",
        "speed_profile",
    }
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary == {
        "total_time_s": pytest.approx(31.5),
        "route_length_m": 2,
        "timing_point_count": 1,
        "block_count": 1,
    }

    with (tmp_path / "timing_points.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows == [{"position_m": "2", "name": "TP", "time_s": "31.5"}]

    with (tmp_path / "block_occupation.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["name"] == "MB1"
    assert rows[0]["intersection_position_m"] == ""
    assert rows[0]["booking_time_s"] == "11.5"

    with (tmp_path / "speed_profile.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[2] == {
        "position_m": "2",
        "speed_mps": "0.0",
        "time_s_per_m": "30.5",
        "cumulative_time_s": "31.5",
    }
