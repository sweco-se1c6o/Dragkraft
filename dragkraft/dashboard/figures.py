from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from dragkraft.domain.result import SimulationResult
from dragkraft.domain.scenario import SimulationSettings


PLOT_TEMPLATE = "plotly_white"
PLOT_COLORS = {
    "speed": "#2457d6",
    "speed_fill": "rgba(36, 87, 214, 0.08)",
    "sth": "#1f2937",
    "constraint": "#d94848",
    "gradient": "#138a65",
    "gradient_soft": "#52a884",
    "altitude": "#7c3aed",
    "curve": "#d97706",
    "signal": "#b91c1c",
    "grid": "#e6edf5",
    "paper": "#ffffff",
    "plot": "#f8fafc",
}


def display_positions_km(
    *,
    result: SimulationResult,
    settings: SimulationSettings,
) -> np.ndarray:
    positions_m = result.route.x_positions_m.astype(float)
    if settings.flip_profiles:
        positions_m = positions_m - result.route.vectors.max_position_m
    return positions_m / 1000.0


def build_route_profile_figure(
    *,
    result: SimulationResult,
    settings: SimulationSettings,
    include_candidate_curves: bool,
) -> go.Figure:
    x_km = display_positions_km(result=result, settings=settings)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_km,
            y=_finite(result.initial_envelope.candidate_profiles_mps[0] * 3.6),
            name="STH [km/h]",
            line={"color": PLOT_COLORS["sth"], "width": 2.5},
            hovertemplate="Position %{x:.3f} km<br>STH %{y:.1f} km/h<extra></extra>",
        )
    )
    if include_candidate_curves:
        for index, profile in enumerate(
            result.initial_envelope.candidate_profiles_mps[1:],
            start=1,
        ):
            fig.add_trace(
                go.Scatter(
                    x=x_km,
                    y=_finite(profile * 3.6),
                    name=f"Constraint {index} [km/h]",
                    line={"color": PLOT_COLORS["constraint"], "width": 1, "dash": "dot"},
                    opacity=0.28,
                    hovertemplate=(
                        "Position %{x:.3f} km<br>"
                        f"Constraint {index} "
                        "%{y:.1f} km/h<extra></extra>"
                    ),
                )
            )
    fig.add_trace(
        go.Scatter(
            x=x_km,
            y=_finite(result.speed_profile_mps * 3.6),
            name="Simulated speed [km/h]",
            fill="tozeroy",
            fillcolor=PLOT_COLORS["speed_fill"],
            line={"color": PLOT_COLORS["speed"], "width": 3.5},
            hovertemplate="Position %{x:.3f} km<br>Speed %{y:.1f} km/h<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_km,
            y=result.route.equivalent_gradient * 1000.0,
            name="Equivalent gradient [permille]",
            line={"color": PLOT_COLORS["gradient"], "width": 1.7},
            yaxis="y2",
            hovertemplate="Position %{x:.3f} km<br>Eq gradient %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_km,
            y=_raw_gradient_promille(result),
            name="Gradient [permille]",
            line={"color": PLOT_COLORS["gradient_soft"], "width": 1.2, "dash": "dash"},
            yaxis="y2",
            hovertemplate="Position %{x:.3f} km<br>Gradient %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_km,
            y=_altitude_m(result=result, settings=settings),
            name="Altitude [m]",
            line={"color": PLOT_COLORS["altitude"], "width": 1.6},
            yaxis="y2",
            hovertemplate="Position %{x:.3f} km<br>Altitude %{y:.2f} m<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_km,
            y=_curve_radius_display(result),
            name="Curve radius [m/10]",
            line={"color": PLOT_COLORS["curve"], "width": 1},
            yaxis="y2",
            hovertemplate="Position %{x:.3f} km<br>Radius/10 %{y:.1f}<extra></extra>",
        )
    )
    _add_position_markers(fig, result=result, settings=settings)
    _add_tunnel_bars(fig, result=result, settings=settings)
    if result.stall is not None:
        fig.add_vline(
            x=_display_position_for_m(
                position_m=result.stall.position_m,
                result=result,
                settings=settings,
            ),
            line={"color": PLOT_COLORS["constraint"], "width": 2, "dash": "dash"},
            annotation_text=f"Stall {result.stall.position_m} m",
            annotation_position="top",
        )
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title="Route Profile",
        paper_bgcolor=PLOT_COLORS["paper"],
        plot_bgcolor=PLOT_COLORS["plot"],
        xaxis_title="Position [km]",
        xaxis={
            "title": "Position [km]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
            "rangeslider": {"visible": True, "thickness": 0.06},
        },
        yaxis={
            "title": "Speed [km/h]",
            "range": [-10, 70],
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
            "zerolinecolor": "#cbd5e1",
        },
        yaxis2={
            "title": "Profile overlays",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
        },
        legend={
            "orientation": "h",
            "y": -0.24,
            "x": 0,
            "bgcolor": "rgba(255,255,255,0.82)",
        },
        margin={"l": 58, "r": 64, "t": 58, "b": 104},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#172033", "font": {"color": "#ffffff"}},
    )
    return fig


def build_speed_time_figure(*, result: SimulationResult) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.cumulative_time_s,
            y=_finite(result.speed_profile_mps * 3.6),
            name="Simulated speed [km/h]",
            fill="tozeroy",
            fillcolor=PLOT_COLORS["speed_fill"],
            line={"color": PLOT_COLORS["speed"], "width": 3.5},
            hovertemplate="Time %{x:.1f} s<br>Speed %{y:.1f} km/h<extra></extra>",
        )
    )
    for passage in result.timing_passages:
        fig.add_vline(
            x=passage.time_s,
            line={"color": PLOT_COLORS["signal"], "width": 1, "dash": "dot"},
        )
    if result.stall is not None:
        fig.add_vline(
            x=float(result.cumulative_time_s[result.stall.position_m]),
            line={"color": PLOT_COLORS["constraint"], "width": 2, "dash": "dash"},
            annotation_text=f"Stall {result.stall.position_m} m",
            annotation_position="top",
        )
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title="Speed Over Time",
        paper_bgcolor=PLOT_COLORS["paper"],
        plot_bgcolor=PLOT_COLORS["plot"],
        xaxis_title="Time [s]",
        yaxis_title="Speed [km/h]",
        xaxis={
            "title": "Time [s]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
            "rangeslider": {"visible": True, "thickness": 0.06},
        },
        yaxis={
            "title": "Speed [km/h]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
            "zerolinecolor": "#cbd5e1",
        },
        margin={"l": 58, "r": 36, "t": 58, "b": 84},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#172033", "font": {"color": "#ffffff"}},
    )
    return fig


def build_acceleration_figure(*, result: SimulationResult) -> go.Figure:
    delta_t = np.diff(result.cumulative_time_s)
    acceleration = np.divide(
        np.diff(result.speed_profile_mps),
        delta_t,
        out=np.zeros(result.speed_profile_mps.size - 1),
        where=delta_t != 0,
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.cumulative_time_s[:-1],
            y=acceleration,
            name="Acceleration [m/s^2]",
            fill="tozeroy",
            fillcolor="rgba(19, 138, 101, 0.10)",
            line={"color": PLOT_COLORS["gradient"], "width": 2.2},
            hovertemplate="Time %{x:.1f} s<br>Acceleration %{y:.3f} m/s^2<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title="Acceleration Over Time",
        paper_bgcolor=PLOT_COLORS["paper"],
        plot_bgcolor=PLOT_COLORS["plot"],
        xaxis_title="Time [s]",
        yaxis_title="Acceleration [m/s^2]",
        xaxis={
            "title": "Time [s]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
            "rangeslider": {"visible": True, "thickness": 0.06},
        },
        yaxis={
            "title": "Acceleration [m/s^2]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
            "zerolinecolor": "#94a3b8",
        },
        margin={"l": 58, "r": 36, "t": 58, "b": 84},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#172033", "font": {"color": "#ffffff"}},
    )
    return fig


def build_block_occupation_figure(
    *,
    result: SimulationResult,
    settings: SimulationSettings,
) -> go.Figure:
    x_km = display_positions_km(result=result, settings=settings)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.cumulative_time_s,
            y=x_km,
            name="Train trajectory",
            line={"color": PLOT_COLORS["speed"], "width": 2.4},
            hovertemplate="Time %{x:.1f} s<br>Position %{y:.3f} km<extra></extra>",
        )
    )
    for block in result.block_occupation.occupations:
        y = _display_position_for_m(
            position_m=block.signal_position_m,
            result=result,
            settings=settings,
        )
        fig.add_shape(
            type="rect",
            x0=block.booking_time_s,
            x1=block.release_time_s,
            y0=y - 0.02,
            y1=y + 0.02,
            fillcolor="rgba(185, 28, 28, 0.18)",
            line={"color": "rgba(185, 28, 28, 0.55)", "width": 1},
        )
        fig.add_annotation(
            x=block.arrival_time_s,
            y=y,
            text=block.name,
            showarrow=False,
            font={"size": 10},
        )
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title="Block Occupation",
        paper_bgcolor=PLOT_COLORS["paper"],
        plot_bgcolor=PLOT_COLORS["plot"],
        xaxis_title="Time [s]",
        yaxis_title="Position [km]",
        xaxis={
            "title": "Time [s]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
        },
        yaxis={
            "title": "Position [km]",
            "showgrid": True,
            "gridcolor": PLOT_COLORS["grid"],
        },
        margin={"l": 58, "r": 36, "t": 58, "b": 64},
        hovermode="closest",
        hoverlabel={"bgcolor": "#172033", "font": {"color": "#ffffff"}},
    )
    return fig


def _finite(values: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(values), values, np.nan)


def _raw_gradient_promille(result: SimulationResult) -> np.ndarray:
    values = np.zeros_like(result.route.x_positions_m, dtype=float)
    positions = result.route.vectors.gradient_positions_m.astype(int)
    slopes = result.route.vectors.gradient_slopes
    for slope, start, end in zip(slopes, positions[:-1], positions[1:], strict=True):
        values[start : end + 1] = slope * 1000.0
    return values


def _altitude_m(
    *,
    result: SimulationResult,
    settings: SimulationSettings,
) -> np.ndarray:
    altitude = np.empty_like(result.route.x_positions_m, dtype=float)
    altitude[0] = settings.altitude_at_start_m
    raw_gradient = _raw_gradient_promille(result) / 1000.0
    altitude[1:] = settings.altitude_at_start_m + np.cumsum(raw_gradient[:-1])
    return altitude


def _curve_radius_display(result: SimulationResult) -> np.ndarray:
    values = np.zeros_like(result.route.x_positions_m, dtype=float)
    positions = result.route.vectors.curve_positions_m.astype(int)
    radii = result.route.vectors.curve_radii_m
    for radius, start, end in zip(radii, positions[:-1], positions[1:], strict=True):
        if np.isfinite(radius):
            values[start : end + 1] = radius / 10.0
    return values


def _add_position_markers(
    fig: go.Figure,
    *,
    result: SimulationResult,
    settings: SimulationSettings,
) -> None:
    for passage in result.timing_passages:
        x = _display_position_for_m(
            position_m=passage.position_m,
            result=result,
            settings=settings,
        )
        y = result.speed_profile_mps[passage.position_m] * 3.6
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                name=f"Timing: {passage.name}",
                mode="markers",
                marker={"symbol": "diamond", "size": 9, "color": PLOT_COLORS["signal"]},
                showlegend=False,
            )
        )
    for position, name in zip(
        result.route.vectors.stop_positions_m.astype(int),
        result.route.vectors.stop_names,
        strict=True,
    ):
        x = _display_position_for_m(
            position_m=int(position),
            result=result,
            settings=settings,
        )
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[0],
                name=f"Stop: {name}",
                mode="markers",
                marker={"symbol": "x", "size": 10, "color": PLOT_COLORS["sth"]},
                showlegend=False,
            )
        )


def _add_tunnel_bars(
    fig: go.Figure,
    *,
    result: SimulationResult,
    settings: SimulationSettings,
) -> None:
    for start, end, factor in result.route.vectors.tunnel_rows_m:
        x0 = _display_position_for_m(
            position_m=int(start),
            result=result,
            settings=settings,
        )
        x1 = _display_position_for_m(
            position_m=int(end),
            result=result,
            settings=settings,
        )
        fig.add_shape(
            type="line",
            x0=min(x0, x1),
            x1=max(x0, x1),
            y0=-4,
            y1=-4,
            line={"color": PLOT_COLORS["sth"], "width": 5},
        )
        fig.add_annotation(
            x=(x0 + x1) / 2.0,
            y=-6,
            text=f"{factor:g}",
            showarrow=False,
            font={"size": 10, "color": PLOT_COLORS["sth"]},
        )


def _display_position_for_m(
    *,
    position_m: int,
    result: SimulationResult,
    settings: SimulationSettings,
) -> float:
    if settings.flip_profiles:
        position_m = position_m - result.route.vectors.max_position_m
    return position_m / 1000.0
