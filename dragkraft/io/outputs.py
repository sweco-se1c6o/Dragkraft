from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from dragkraft.domain.result import SimulationResult


def write_simulation_outputs(
    *,
    result: SimulationResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    paths = {
        "summary": output_path / "summary.json",
        "timing_points": output_path / "timing_points.csv",
        "block_occupation": output_path / "block_occupation.csv",
        "speed_profile": output_path / "speed_profile.csv",
    }
    _write_summary(result=result, path=paths["summary"])
    _write_timing_points(result=result, path=paths["timing_points"])
    _write_block_occupation(result=result, path=paths["block_occupation"])
    _write_speed_profile(result=result, path=paths["speed_profile"])
    return paths


def _write_summary(*, result: SimulationResult, path: Path) -> None:
    summary = {
        "total_time_s": float(result.cumulative_time_s[-1]),
        "route_length_m": int(result.speed_profile_mps.size - 1),
        "timing_point_count": len(result.timing_passages),
        "block_count": len(result.block_occupation.occupations),
    }
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def _write_timing_points(*, result: SimulationResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["position_m", "name", "time_s"])
        writer.writeheader()
        for passage in result.timing_passages:
            writer.writerow(
                {
                    "position_m": passage.position_m,
                    "name": passage.name,
                    "time_s": _csv_value(passage.time_s),
                }
            )


def _write_block_occupation(*, result: SimulationResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "signal_position_m",
                "speed_difference_mps",
                "intersection_position_m",
                "booking_time_s",
                "arrival_time_s",
                "release_time_s",
            ],
        )
        writer.writeheader()
        for block in result.block_occupation.occupations:
            writer.writerow(
                {
                    "name": block.name,
                    "signal_position_m": block.signal_position_m,
                    "speed_difference_mps": _csv_value(block.speed_difference_mps),
                    "intersection_position_m": (
                        "" if block.intersection_position_m is None else block.intersection_position_m
                    ),
                    "booking_time_s": _csv_value(block.booking_time_s),
                    "arrival_time_s": _csv_value(block.arrival_time_s),
                    "release_time_s": _csv_value(block.release_time_s),
                }
            )


def _write_speed_profile(*, result: SimulationResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "position_m",
                "speed_mps",
                "time_s_per_m",
                "cumulative_time_s",
            ],
        )
        writer.writeheader()
        for position in range(result.speed_profile_mps.size):
            writer.writerow(
                {
                    "position_m": position,
                    "speed_mps": _csv_value(result.speed_profile_mps[position]),
                    "time_s_per_m": _csv_value(result.time_s_per_m[position]),
                    "cumulative_time_s": _csv_value(result.cumulative_time_s[position]),
                }
            )


def _csv_value(value: float | np.floating) -> str:
    numeric = float(value)
    if math.isnan(numeric):
        return ""
    return str(numeric)
