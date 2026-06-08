from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from dragkraft.domain.scenario import SimulationSettings
from dragkraft.domain.train import TrainConfig
from dragkraft.vehicles.scenarios import default_scenario, freight_train


DEFAULT_WORKBOOK_PATH = "old/luleaHamn3.xlsx"
DEFAULT_OUTPUT_DIR = "runs/dashboard"
TRAIN_PRESETS = ("freight",)


class DashboardFormError(ValueError):
    """Raised when dashboard form values cannot be converted to domain objects."""


@dataclass(frozen=True)
class DashboardForm:
    scenario_name: str
    workbook_path: str
    output_dir: str
    settings: SimulationSettings
    train: TrainConfig


def parse_dashboard_form(values: dict[str, Any]) -> DashboardForm:
    defaults = default_scenario()
    train_name = _text(values, "train_name", defaults.train_name)
    if train_name not in TRAIN_PRESETS:
        raise DashboardFormError(f"Unsupported train preset: {train_name}")

    extra_wagons = _integer(values, "extra_wagon_count", defaults.extra_wagon_count)
    adhesion_coefficient = _positive_number(values, "adhesion_coefficient", 0.6)
    settings = replace(
        defaults,
        sheet_name=_text(values, "sheet_name", defaults.sheet_name),
        train_name=train_name,
        extra_wagon_count=extra_wagons,
        speed_override_kmh=_number(
            values,
            "speed_override_kmh",
            defaults.speed_override_kmh,
        ),
        flip_profiles=_boolean(values, "flip_profiles", defaults.flip_profiles),
        altitude_at_start_m=_number(
            values,
            "altitude_at_start_m",
            defaults.altitude_at_start_m,
        ),
        time_offset_s=_number(values, "time_offset_s", defaults.time_offset_s),
        short_time_margin=_number(
            values,
            "short_time_margin",
            defaults.short_time_margin,
        ),
        use_train_length_delay=_boolean(
            values,
            "use_train_length_delay",
            defaults.use_train_length_delay,
        ),
        use_distance_before_signal=_boolean(
            values,
            "use_distance_before_signal",
            defaults.use_distance_before_signal,
        ),
        use_tav_distance=_boolean(
            values,
            "use_tav_distance",
            defaults.use_tav_distance,
        ),
        freight_signal_advance_s_per_mps=_number(
            values,
            "freight_signal_advance_s_per_mps",
            defaults.freight_signal_advance_s_per_mps,
        ),
        freight_signal_advance2_s_per_mps=_number(
            values,
            "freight_signal_advance2_s_per_mps",
            defaults.freight_signal_advance2_s_per_mps,
        ),
        freight_signal_advance2_m=_number(
            values,
            "freight_signal_advance2_m",
            defaults.freight_signal_advance2_m,
        ),
        switch_speed_mps=_number(
            values,
            "switch_speed_kmh",
            defaults.switch_speed_mps * 3.6,
        )
        / 3.6,
        use_min_time_to_hold_speed=_boolean(
            values,
            "use_min_time_to_hold_speed",
            defaults.use_min_time_to_hold_speed,
        ),
        min_time_to_hold_speed_s=_number(
            values,
            "min_time_to_hold_speed_s",
            defaults.min_time_to_hold_speed_s,
        ),
        speed_tolerance_mps=_number(
            values,
            "speed_tolerance_kmh",
            defaults.speed_tolerance_mps * 3.6,
        )
        / 3.6,
        min_signal_deceleration_mps2=_number(
            values,
            "min_signal_deceleration_mps2",
            defaults.min_signal_deceleration_mps2,
        ),
        reserve_before_arrival_s=_number(
            values,
            "reserve_before_arrival_s",
            defaults.reserve_before_arrival_s,
        ),
    )
    return DashboardForm(
        scenario_name=_text(values, "scenario_name", "Scenario"),
        workbook_path=_text(values, "workbook_path", DEFAULT_WORKBOOK_PATH),
        output_dir=_text(values, "output_dir", DEFAULT_OUTPUT_DIR),
        settings=settings,
        train=replace(
            freight_train(extra_wagons=extra_wagons),
            adhesion_coefficient=adhesion_coefficient,
        ),
    )


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
        raise DashboardFormError(f"{key} must be numeric") from exc


def _integer(values: dict[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    if value is None or value == "":
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DashboardFormError(f"{key} must be an integer") from exc


def _positive_number(values: dict[str, Any], key: str, default: float) -> float:
    value = _number(values, key, default)
    if value <= 0:
        raise DashboardFormError(f"{key} must be greater than zero")
    return value


def _boolean(values: dict[str, Any], key: str, default: bool) -> bool:
    value = values.get(key, default)
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return bool(default)
    if isinstance(value, (list, tuple, set)):
        return key in value or True in value or "true" in value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
