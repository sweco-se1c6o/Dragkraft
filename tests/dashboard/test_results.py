from __future__ import annotations

from dragkraft.dashboard.results import (
    build_comparison_rows,
    build_comparison_speed_position_figure,
    build_comparison_speed_time_figure,
    build_result_summary,
    build_scenario_snapshot,
)
from dragkraft.simulation.orchestrator import simulate_workbook
from dragkraft.vehicles.scenarios import default_scenario, freight_train


def test_build_result_summary_includes_train_vehicle_and_run_details() -> None:
    settings = default_scenario()
    train = freight_train(extra_wagons=settings.extra_wagon_count)
    result = simulate_workbook(
        workbook_path="old/luleaHamn3.xlsx",
        train=train,
        settings=settings,
    )

    summary = build_result_summary(
        result=result,
        train=train,
        settings=settings,
        workbook_path="old/luleaHamn3.xlsx",
    )

    assert summary["vehicle_type"] == "Freight consist"
    assert summary["train_name"] == "freight"
    assert summary["locomotives"] == 1
    assert summary["wagons"] == 21
    assert summary["adhesion_coefficient"] == 0.6
    assert summary["train_mass_t"] == 1840.0
    assert summary["train_length_m"] == 246.4
    assert summary["route_length_m"] == result.route.vectors.max_position_m
    assert summary["timing_points"] == len(result.timing_passages)
    assert summary["blocks"] == len(result.block_occupation.occupations)


def test_build_scenario_snapshot_keeps_compact_comparison_series() -> None:
    settings = default_scenario()
    train = freight_train(extra_wagons=settings.extra_wagon_count)
    result = simulate_workbook(
        workbook_path="old/luleaHamn3.xlsx",
        train=train,
        settings=settings,
    )

    snapshot = build_scenario_snapshot(
        label="Base",
        result=result,
        train=train,
        settings=settings,
        workbook_path="old/luleaHamn3.xlsx",
        max_points=200,
    )

    assert snapshot["label"] == "Base"
    assert len(snapshot["position_km"]) <= 200
    assert len(snapshot["position_km"]) == len(snapshot["speed_by_position_kmh"])
    assert len(snapshot["time_s"]) <= 200
    assert snapshot["summary"]["wagons"] == 21


def test_comparison_builders_overlay_saved_scenarios() -> None:
    snapshots = [
        {
            "label": "A",
            "position_km": [0.0, 1.0],
            "speed_by_position_kmh": [0.0, 40.0],
            "time_s": [0.0, 120.0],
            "speed_by_time_kmh": [0.0, 40.0],
            "summary": {
                "total_time_s": 120.0,
                "route_length_m": 1000,
                "wagons": 21,
                "adhesion_coefficient": 0.6,
                "train_mass_t": 1840.0,
                "simulated_max_speed_kmh": 40.0,
            },
        },
        {
            "label": "B",
            "position_km": [0.0, 1.0],
            "speed_by_position_kmh": [0.0, 35.0],
            "time_s": [0.0, 140.0],
            "speed_by_time_kmh": [0.0, 35.0],
            "summary": {
                "total_time_s": 140.0,
                "route_length_m": 1000,
                "wagons": 30,
                "adhesion_coefficient": 0.45,
                "train_mass_t": 2600.0,
                "simulated_max_speed_kmh": 35.0,
            },
        },
    ]

    position_fig = build_comparison_speed_position_figure(snapshots)
    time_fig = build_comparison_speed_time_figure(snapshots)
    rows = build_comparison_rows(snapshots)

    assert [trace.name for trace in position_fig.data] == ["A", "B"]
    assert [trace.name for trace in time_fig.data] == ["A", "B"]
    assert rows[1]["delta_time_s"] == 20.0
    assert rows[1]["adhesion_coefficient"] == 0.45
