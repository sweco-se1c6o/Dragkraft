"""Build a JSON-serialisable result payload for the browser frontend.

This module deliberately avoids any Dash/Plotly imports so it can run inside
Pyodide with only numpy + openpyxl. The browser writes the uploaded workbook
into the virtual filesystem, calls :func:`run_simulation` with a plain dict of
form values, and renders the returned payload with Plotly.js.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from dragkraft.domain.result import SimulationResult
from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.train import TrainConfig
from dragkraft.simulation.orchestrator import simulate_workbook
from dragkraft.vehicles.scenarios import (
    TRAIN_LIBRARY,
    build_train,
    custom_train,
    default_scenario,
)

MAX_CHART_POINTS = 4000


def _train_label(name: str) -> str:
    if name in TRAIN_LIBRARY:
        return TRAIN_LIBRARY[name].label
    if name == "custom":
        return "Custom train"
    return name


class WebFormError(ValueError):
    """Raised when frontend form values cannot be converted to domain objects."""


# --------------------------------------------------------------------------- #
# Form parsing (mirrors the dashboard form, without the Dash dependency).
# --------------------------------------------------------------------------- #
def parse_form(values: dict[str, Any]) -> tuple[TrainConfig, SimulationSettings, str, str]:
    defaults = default_scenario()
    train_name = _text(values, "train_name", defaults.train_name)
    if train_name != "custom" and train_name not in TRAIN_LIBRARY:
        raise WebFormError(f"Unsupported train: {train_name}")

    extra_wagons = _integer(values, "extra_wagon_count", defaults.extra_wagon_count)
    adhesion = _positive(values, "adhesion_coefficient", 0.6)
    settings = replace(
        defaults,
        sheet_name=_text(values, "sheet_name", defaults.sheet_name),
        train_name=train_name,
        extra_wagon_count=extra_wagons,
        speed_override_kmh=_number(values, "speed_override_kmh", defaults.speed_override_kmh),
        flip_profiles=_boolean(values, "flip_profiles", defaults.flip_profiles),
        altitude_at_start_m=_number(values, "altitude_at_start_m", defaults.altitude_at_start_m),
        time_offset_s=_number(values, "time_offset_s", defaults.time_offset_s),
        short_time_margin=_number(values, "short_time_margin", defaults.short_time_margin),
        use_train_length_delay=_boolean(
            values, "use_train_length_delay", defaults.use_train_length_delay
        ),
        use_distance_before_signal=_boolean(
            values, "use_distance_before_signal", defaults.use_distance_before_signal
        ),
        use_tav_distance=_boolean(values, "use_tav_distance", defaults.use_tav_distance),
        freight_signal_advance_s_per_mps=_number(
            values, "freight_signal_advance_s_per_mps", defaults.freight_signal_advance_s_per_mps
        ),
        freight_signal_advance2_s_per_mps=_number(
            values, "freight_signal_advance2_s_per_mps", defaults.freight_signal_advance2_s_per_mps
        ),
        freight_signal_advance2_m=_number(
            values, "freight_signal_advance2_m", defaults.freight_signal_advance2_m
        ),
        switch_speed_mps=_number(values, "switch_speed_kmh", defaults.switch_speed_mps * 3.6) / 3.6,
        use_min_time_to_hold_speed=_boolean(
            values, "use_min_time_to_hold_speed", defaults.use_min_time_to_hold_speed
        ),
        min_time_to_hold_speed_s=_number(
            values, "min_time_to_hold_speed_s", defaults.min_time_to_hold_speed_s
        ),
        speed_tolerance_mps=_number(
            values, "speed_tolerance_kmh", defaults.speed_tolerance_mps * 3.6
        )
        / 3.6,
        min_signal_deceleration_mps2=_number(
            values, "min_signal_deceleration_mps2", defaults.min_signal_deceleration_mps2
        ),
        reserve_before_arrival_s=_number(
            values, "reserve_before_arrival_s", defaults.reserve_before_arrival_s
        ),
    )
    if train_name == "custom":
        train = custom_train(
            extra_wagons=extra_wagons, adhesion_coefficient=adhesion, params=values
        )
    else:
        train = build_train(
            train_name, extra_wagons=extra_wagons, adhesion_coefficient=adhesion
        )
    scenario_name = _text(values, "scenario_name", "Scenario")
    return train, settings, scenario_name, settings.sheet_name


def default_form_values() -> dict[str, Any]:
    """Default value for every form key, so the frontend can prefill controls."""
    d = default_scenario()
    return {
        "scenario_name": "Scenario",
        "sheet_name": d.sheet_name,
        "train_name": d.train_name,
        "extra_wagon_count": d.extra_wagon_count,
        "adhesion_coefficient": 0.6,
        "speed_override_kmh": d.speed_override_kmh,
        "flip_profiles": d.flip_profiles,
        "altitude_at_start_m": d.altitude_at_start_m,
        "time_offset_s": d.time_offset_s,
        "short_time_margin": d.short_time_margin,
        "use_train_length_delay": d.use_train_length_delay,
        "use_distance_before_signal": d.use_distance_before_signal,
        "use_tav_distance": d.use_tav_distance,
        "freight_signal_advance_s_per_mps": d.freight_signal_advance_s_per_mps,
        "freight_signal_advance2_s_per_mps": d.freight_signal_advance2_s_per_mps,
        "freight_signal_advance2_m": d.freight_signal_advance2_m,
        "switch_speed_kmh": round(d.switch_speed_mps * 3.6, 3),
        "use_min_time_to_hold_speed": d.use_min_time_to_hold_speed,
        "min_time_to_hold_speed_s": d.min_time_to_hold_speed_s,
        "speed_tolerance_kmh": round(d.speed_tolerance_mps * 3.6, 3),
        "min_signal_deceleration_mps2": d.min_signal_deceleration_mps2,
        "reserve_before_arrival_s": d.reserve_before_arrival_s,
        # Custom-train builder defaults (type-1 traction model).
        "custom_locomotive_count": 1,
        "custom_locomotive_mass_t": 76.0,
        "custom_locomotive_length_m": 15.4,
        "custom_wagon_mass_t": 84.0,
        "custom_wagon_length_m": 11.0,
        "custom_max_force_kn": 600.0,
        "custom_start_force_kn": 600.0,
        "custom_start_speed_kmh": 5.0,
        "custom_power_kw": 5000.0,
        "custom_vehicle_max_speed_kmh": 100.0,
        "custom_max_acceleration_mps2": 1.0,
        "custom_max_deceleration_mps2": 0.7,
    }


def default_form_values_json() -> str:
    return json.dumps(default_form_values())


def train_library() -> list[dict[str, Any]]:
    """Selectable trains with their fixed (per-consist) features for the UI."""
    presets = [
        {
            "key": spec.key,
            "label": spec.label,
            "description": spec.description,
            "custom": False,
            "locomotives": spec.locomotive_count,
            "locomotive_mass_t": round(spec.locomotive_mass_kg / 1000.0, 1),
            "wagon_mass_t": round(spec.wagon_mass_kg / 1000.0, 1),
            "vehicle_max_speed_kmh": spec.vehicle_max_speed_kmh,
            "traction_model": "Type 2 — piecewise",
            "max_tractive_force_kn": round(max(spec.traction_force_points_n) / 1000.0),
            "default_wagons": spec.default_wagons,
        }
        for spec in TRAIN_LIBRARY.values()
    ]
    presets.append(
        {
            "key": "custom",
            "label": "Custom train…",
            "description": "Define your own consist with a force + power traction model.",
            "custom": True,
        }
    )
    return presets


def train_library_json() -> str:
    return json.dumps(train_library())


# --------------------------------------------------------------------------- #
# Public entry points.
# --------------------------------------------------------------------------- #
def run_simulation(workbook_path: str, values: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse form values, run the simulation, and return a JSON-ready payload."""
    train, settings, scenario_name, _ = parse_form(values or {})
    result = simulate_workbook(workbook_path=Path(workbook_path), train=train, settings=settings)
    payload = build_payload(
        result=result,
        train=train,
        settings=settings,
        workbook_name=Path(workbook_path).name,
    )
    payload["scenario_name"] = scenario_name
    return _json_safe(payload)


def _json_safe(obj: Any) -> Any:
    """Recursively replace non-finite floats with None so the payload is valid
    JSON (browsers reject the NaN/Infinity tokens that json.dumps emits)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def run_simulation_json(workbook_path: str, values_json: str = "{}") -> str:
    """Browser-friendly wrapper: takes/returns JSON strings.

    On a form/parse error it returns ``{"error": ...}`` instead of raising so the
    JS side can render a clean message without crossing the Python/JS boundary.
    """
    try:
        values = json.loads(values_json) if values_json else {}
        payload = run_simulation(workbook_path, values)
        return json.dumps(payload)
    except (WebFormError, ValueError) as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


# --------------------------------------------------------------------------- #
# Payload assembly.
# --------------------------------------------------------------------------- #
def build_payload(
    *,
    result: SimulationResult,
    train: TrainConfig,
    settings: SimulationSettings,
    workbook_name: str,
) -> dict[str, Any]:
    idx = _sample_indices(result.cumulative_time_s.size)
    position_km = _display_positions_km(result, settings)
    speed_kmh = result.speed_profile_mps * 3.6
    cumulative_time = result.cumulative_time_s

    payload: dict[str, Any] = {
        "summary": _summary(result=result, train=train, settings=settings, workbook_name=workbook_name),
        "stall": _stall(result, settings),
        "route": {
            "position_km": _clean(position_km[idx], 5),
            "sth_kmh": _clean(result.initial_envelope.candidate_profiles_mps[0][idx] * 3.6, 3),
            "simulated_speed_kmh": _clean(speed_kmh[idx], 3),
            "eq_gradient_promille": _clean(result.route.equivalent_gradient[idx] * 1000.0, 3),
            "raw_gradient_promille": _clean(_raw_gradient_promille(result)[idx], 3),
            "altitude_m": _clean(_altitude_m(result, settings)[idx], 3),
            "curve_radius_disp": _clean(_curve_radius_display(result)[idx], 2),
            "timing_markers": _timing_markers(result, settings),
            "stop_markers": _stop_markers(result, settings),
            "tunnels": _tunnels(result, settings),
        },
        "speed_time": {
            "time_s": _clean(cumulative_time[idx], 3),
            "speed_kmh": _clean(speed_kmh[idx], 3),
            "timing_lines": [
                {"time_s": round(float(p.time_s), 3), "name": p.name}
                for p in result.timing_passages
            ],
        },
        "acceleration": _acceleration(result),
        "blocks_chart": _blocks_chart(result, settings, idx),
        "tables": {
            "timing": [
                {"position_m": p.position_m, "name": p.name, "time_s": round(p.time_s, 3)}
                for p in result.timing_passages
            ],
            "blocks": [
                {
                    "name": b.name,
                    "signal_position_m": b.signal_position_m,
                    "speed_difference_mps": _round_or_none(b.speed_difference_mps, 6),
                    "intersection_position_m": b.intersection_position_m,
                    "booking_time_s": round(b.booking_time_s, 3),
                    "arrival_time_s": round(b.arrival_time_s, 3),
                    "release_time_s": round(b.release_time_s, 3),
                }
                for b in result.block_occupation.occupations
            ],
        },
    }
    return payload


def _summary(
    *,
    result: SimulationResult,
    train: TrainConfig,
    settings: SimulationSettings,
    workbook_name: str,
) -> dict[str, Any]:
    finite = result.speed_profile_mps[np.isfinite(result.speed_profile_mps)]
    max_speed_kmh = float(np.max(finite) * 3.6) if finite.size else 0.0
    return {
        "workbook": workbook_name,
        "sheet": settings.sheet_name,
        "vehicle_type": _train_label(train.name),
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


def _stall(result: SimulationResult, settings: SimulationSettings) -> dict[str, Any] | None:
    if result.stall is None:
        return None
    pos = result.stall.position_m
    return {
        "position_m": pos,
        "speed_mps": round(result.stall.speed_mps, 4),
        "acceleration_mps2": round(result.stall.acceleration_mps2, 4),
        "position_km": round(float(_display_position_for_m(pos, result, settings)), 5),
        "time_s": round(float(result.cumulative_time_s[pos]), 1),
        "message": result.stall.describe(),
    }


def _acceleration(result: SimulationResult) -> dict[str, Any]:
    delta_t = np.diff(result.cumulative_time_s)
    accel = np.divide(
        np.diff(result.speed_profile_mps),
        delta_t,
        out=np.zeros(result.speed_profile_mps.size - 1),
        where=delta_t != 0,
    )
    time = result.cumulative_time_s[:-1]
    idx = _sample_indices(time.size)
    return {"time_s": _clean(time[idx], 3), "accel_mps2": _clean(accel[idx], 4)}


def _blocks_chart(
    result: SimulationResult, settings: SimulationSettings, idx: np.ndarray
) -> dict[str, Any]:
    return {
        "trajectory_time_s": _clean(result.cumulative_time_s[idx], 3),
        "trajectory_pos_km": _clean(_display_positions_km(result, settings)[idx], 5),
        "rects": [
            {
                "name": b.name,
                "booking_time_s": round(b.booking_time_s, 3),
                "arrival_time_s": round(b.arrival_time_s, 3),
                "release_time_s": round(b.release_time_s, 3),
                "position_km": round(
                    float(_display_position_for_m(b.signal_position_m, result, settings)), 5
                ),
            }
            for b in result.block_occupation.occupations
        ],
    }


# --------------------------------------------------------------------------- #
# Display helpers (pure numpy, ported from the figure builders).
# --------------------------------------------------------------------------- #
def _display_positions_km(result: SimulationResult, settings: SimulationSettings) -> np.ndarray:
    positions_m = result.route.x_positions_m.astype(float)
    if settings.flip_profiles:
        positions_m = positions_m - result.route.vectors.max_position_m
    return positions_m / 1000.0


def _display_position_for_m(
    position_m: int, result: SimulationResult, settings: SimulationSettings
) -> float:
    if settings.flip_profiles:
        position_m = position_m - result.route.vectors.max_position_m
    return position_m / 1000.0


def _raw_gradient_promille(result: SimulationResult) -> np.ndarray:
    values = np.zeros_like(result.route.x_positions_m, dtype=float)
    positions = result.route.vectors.gradient_positions_m.astype(int)
    slopes = result.route.vectors.gradient_slopes
    for slope, start, end in zip(slopes, positions[:-1], positions[1:], strict=True):
        values[start : end + 1] = slope * 1000.0
    return values


def _altitude_m(result: SimulationResult, settings: SimulationSettings) -> np.ndarray:
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


def _timing_markers(result: SimulationResult, settings: SimulationSettings) -> list[dict[str, Any]]:
    return [
        {
            "position_km": round(float(_display_position_for_m(p.position_m, result, settings)), 5),
            "name": p.name,
            "speed_kmh": round(float(result.speed_profile_mps[p.position_m] * 3.6), 3),
        }
        for p in result.timing_passages
    ]


def _stop_markers(result: SimulationResult, settings: SimulationSettings) -> list[dict[str, Any]]:
    markers = []
    for position, name in zip(
        result.route.vectors.stop_positions_m.astype(int),
        result.route.vectors.stop_names,
        strict=True,
    ):
        markers.append(
            {
                "position_km": round(
                    float(_display_position_for_m(int(position), result, settings)), 5
                ),
                "name": name,
            }
        )
    return markers


def _tunnels(result: SimulationResult, settings: SimulationSettings) -> list[dict[str, Any]]:
    tunnels = []
    for start, end, factor in result.route.vectors.tunnel_rows_m:
        x0 = _display_position_for_m(int(start), result, settings)
        x1 = _display_position_for_m(int(end), result, settings)
        tunnels.append(
            {"x0_km": round(float(min(x0, x1)), 5), "x1_km": round(float(max(x0, x1)), 5), "factor": float(factor)}
        )
    return tunnels


# --------------------------------------------------------------------------- #
# Small numeric utilities.
# --------------------------------------------------------------------------- #
def _sample_indices(size: int, *, max_points: int = MAX_CHART_POINTS) -> np.ndarray:
    if size <= max_points:
        return np.arange(size)
    return np.unique(np.linspace(0, size - 1, max_points, dtype=int))


def _clean(values: np.ndarray, digits: int) -> list[float | None]:
    out: list[float | None] = []
    for value in np.asarray(values, dtype=float):
        if not np.isfinite(value):
            out.append(None)
        else:
            out.append(round(float(value), digits))
    return out


def _round_or_none(value: float, digits: int) -> float | None:
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), digits)


# --------------------------------------------------------------------------- #
# Form value coercion.
# --------------------------------------------------------------------------- #
def _text(values: dict[str, Any], key: str, default: str) -> str:
    value = values.get(key, default)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip()


def _number(values: dict[str, Any], key: str, default: float) -> float:
    value = values.get(key, default)
    if value is None or value == "":
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise WebFormError(f"{key} must be numeric") from exc


def _integer(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    if value is None or value == "":
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise WebFormError(f"{key} must be an integer") from exc


def _positive(values: dict[str, Any], key: str, default: float) -> float:
    value = _number(values, key, default)
    if value <= 0:
        raise WebFormError(f"{key} must be greater than zero")
    return value


def _boolean(values: dict[str, Any], key: str, default: bool) -> bool:
    value = values.get(key, default)
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return bool(default)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
