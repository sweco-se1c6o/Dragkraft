from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go

from dragkraft.domain.result import SimulationResult
from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.train import TrainConfig
from dragkraft.dashboard.figures import display_positions_km


def build_result_summary(
    *,
    result: SimulationResult,
    train: TrainConfig,
    settings: SimulationSettings,
    workbook_path: str | Path,
) -> dict[str, Any]:
    finite_speed = result.speed_profile_mps[np.isfinite(result.speed_profile_mps)]
    max_speed_kmh = float(np.max(finite_speed) * 3.6) if finite_speed.size else 0.0
    return {
        "workbook": str(workbook_path),
        "sheet": settings.sheet_name,
        "vehicle_type": _vehicle_type(train),
        "train_name": train.name,
        "locomotives": train.locomotive_count,
        "wagons": train.extra_wagon_count,
        "adhesion_coefficient": round(train.adhesion_coefficient, 3),
        "train_mass_t": round(train.train_mass_kg / 1000.0, 1),
        "dynamic_mass_t": round(train.dynamic_mass_kg / 1000.0, 1),
        "adhesion_mass_t": round(train.adhesion_mass_kg / 1000.0, 1),
        "train_length_m": round(train.train_length_m, 1),
        "vehicle_max_speed_kmh": round(train.vehicle_max_speed_mps * 3.6, 1),
        "simulated_max_speed_kmh": round(max_speed_kmh, 1),
        "traction_model": f"Type {train.traction_model_type}",
        "resistance_model": f"Type {train.resistance_type}",
        "brake_deceleration_min_mps2": round(float(np.min(train.braking_decelerations_mps2)), 3),
        "brake_deceleration_max_mps2": round(float(np.max(train.braking_decelerations_mps2)), 3),
        "route_length_m": int(result.route.vectors.max_position_m),
        "total_time_s": round(float(result.cumulative_time_s[-1]), 1),
        "timing_points": len(result.timing_passages),
        "blocks": len(result.block_occupation.occupations),
        "flip_profiles": settings.flip_profiles,
    }


def build_scenario_snapshot(
    *,
    label: str,
    result: SimulationResult,
    train: TrainConfig,
    settings: SimulationSettings,
    workbook_path: str | Path,
    max_points: int = 1200,
) -> dict[str, Any]:
    position_km = display_positions_km(result=result, settings=settings)
    summary = build_result_summary(
        result=result,
        train=train,
        settings=settings,
        workbook_path=workbook_path,
    )
    position_indices = _sample_indices(position_km.size, max_points=max_points)
    time_indices = _sample_indices(result.cumulative_time_s.size, max_points=max_points)
    return {
        "label": label,
        "summary": summary,
        "position_km": _rounded_list(position_km[position_indices], digits=5),
        "speed_by_position_kmh": _rounded_list(
            result.speed_profile_mps[position_indices] * 3.6,
            digits=4,
        ),
        "time_s": _rounded_list(result.cumulative_time_s[time_indices], digits=3),
        "speed_by_time_kmh": _rounded_list(
            result.speed_profile_mps[time_indices] * 3.6,
            digits=4,
        ),
    }


def build_comparison_speed_position_figure(
    snapshots: list[dict[str, Any]],
) -> go.Figure:
    fig = _comparison_figure(
        title="Saved Scenarios: Speed by Position",
        x_title="Position [km]",
    )
    for snapshot in snapshots:
        fig.add_trace(
            go.Scatter(
                x=snapshot["position_km"],
                y=snapshot["speed_by_position_kmh"],
                name=snapshot["label"],
                mode="lines",
                line={"width": 2.4},
                hovertemplate=(
                    "Position %{x:.3f} km<br>Speed %{y:.1f} km/h<extra></extra>"
                ),
            )
        )
    return fig


def build_comparison_speed_time_figure(
    snapshots: list[dict[str, Any]],
) -> go.Figure:
    fig = _comparison_figure(
        title="Saved Scenarios: Speed by Time",
        x_title="Time [s]",
    )
    for snapshot in snapshots:
        fig.add_trace(
            go.Scatter(
                x=snapshot["time_s"],
                y=snapshot["speed_by_time_kmh"],
                name=snapshot["label"],
                mode="lines",
                line={"width": 2.4},
                hovertemplate="Time %{x:.1f} s<br>Speed %{y:.1f} km/h<extra></extra>",
            )
        )
    return fig


def build_comparison_rows(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not snapshots:
        return []
    baseline_time = float(snapshots[0]["summary"]["total_time_s"])
    rows = []
    for index, snapshot in enumerate(snapshots, start=1):
        summary = snapshot["summary"]
        total_time = float(summary["total_time_s"])
        rows.append(
            {
                "index": index,
                "label": snapshot["label"],
                "total_time_s": total_time,
                "delta_time_s": round(total_time - baseline_time, 1),
                "route_length_m": summary["route_length_m"],
                "wagons": summary["wagons"],
                "adhesion_coefficient": summary["adhesion_coefficient"],
                "train_mass_t": summary["train_mass_t"],
                "max_speed_kmh": summary["simulated_max_speed_kmh"],
            }
        )
    return rows


def _vehicle_type(train: TrainConfig) -> str:
    if train.name == "freight":
        return "Freight consist"
    return "Custom train consist"


def _sample_indices(size: int, *, max_points: int) -> np.ndarray:
    if size <= max_points:
        return np.arange(size)
    return np.unique(np.linspace(0, size - 1, max_points, dtype=int))


def _rounded_list(values: np.ndarray, *, digits: int) -> list[float | None]:
    finite = np.where(np.isfinite(values), values, np.nan)
    return [
        None if np.isnan(float(value)) else round(float(value), digits)
        for value in finite
    ]


def _comparison_figure(*, title: str, x_title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        title=title,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        xaxis={
            "title": x_title,
            "showgrid": True,
            "gridcolor": "#e6edf5",
        },
        yaxis={
            "title": "Speed [km/h]",
            "showgrid": True,
            "gridcolor": "#e6edf5",
            "zerolinecolor": "#cbd5e1",
        },
        legend={
            "orientation": "h",
            "y": -0.22,
            "x": 0,
            "bgcolor": "rgba(255,255,255,0.82)",
        },
        margin={"l": 58, "r": 36, "t": 58, "b": 86},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#172033", "font": {"color": "#ffffff"}},
    )
    return fig
