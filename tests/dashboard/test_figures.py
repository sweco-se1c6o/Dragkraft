from __future__ import annotations

import numpy as np

from dragkraft.dashboard.figures import (
    build_acceleration_figure,
    build_block_occupation_figure,
    build_route_profile_figure,
    build_speed_time_figure,
    display_positions_km,
)
from dragkraft.simulation.orchestrator import simulate_workbook
from dragkraft.vehicles.scenarios import default_scenario, freight_train


def _result():
    settings = default_scenario()
    train = freight_train(extra_wagons=settings.extra_wagon_count)
    return simulate_workbook(
        workbook_path="old/luleaHamn3.xlsx",
        train=train,
        settings=settings,
    )


def test_display_positions_match_flip_and_non_flip_conventions() -> None:
    result = _result()
    settings = default_scenario()

    flipped = display_positions_km(result=result, settings=settings)
    non_flipped = display_positions_km(
        result=result,
        settings=type(settings)(**{**settings.__dict__, "flip_profiles": False}),
    )

    assert flipped[0] == -(result.route.vectors.max_position_m / 1000)
    assert flipped[-1] == 0
    assert non_flipped[0] == 0
    assert non_flipped[-1] == result.route.vectors.max_position_m / 1000


def test_route_profile_figure_contains_engineering_traces() -> None:
    result = _result()
    fig = build_route_profile_figure(
        result=result,
        settings=default_scenario(),
        include_candidate_curves=True,
    )

    names = {trace.name for trace in fig.data}
    assert "STH [km/h]" in names
    assert "Simulated speed [km/h]" in names
    assert "Equivalent gradient [permille]" in names
    assert "Gradient [permille]" in names
    assert "Altitude [m]" in names
    assert "Curve radius [m/10]" in names
    assert any(name.startswith("Constraint ") for name in names if name)
    assert fig.layout.plot_bgcolor == "#f8fafc"


def test_speed_time_figure_uses_cumulative_time_and_kmh() -> None:
    result = _result()
    fig = build_speed_time_figure(result=result)

    trace = fig.data[0]
    assert trace.name == "Simulated speed [km/h]"
    assert np.asarray(trace.x)[0] == result.cumulative_time_s[0]
    assert np.asarray(trace.y)[10] == result.speed_profile_mps[10] * 3.6


def test_acceleration_figure_uses_speed_difference_over_time() -> None:
    result = _result()
    fig = build_acceleration_figure(result=result)

    trace = fig.data[0]
    expected = np.divide(
        np.diff(result.speed_profile_mps),
        np.diff(result.cumulative_time_s),
        out=np.zeros(result.speed_profile_mps.size - 1),
        where=np.diff(result.cumulative_time_s) != 0,
    )
    assert trace.name == "Acceleration [m/s^2]"
    assert len(trace.x) == result.speed_profile_mps.size - 1
    assert np.allclose(np.asarray(trace.y), expected, equal_nan=True)


def test_block_occupation_figure_maps_occupations_to_shapes() -> None:
    result = _result()
    fig = build_block_occupation_figure(
        result=result,
        settings=default_scenario(),
    )

    assert len(fig.layout.shapes) == len(result.block_occupation.occupations)
    assert fig.data[0].name == "Train trajectory"
