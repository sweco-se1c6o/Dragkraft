from __future__ import annotations

from dataclasses import replace

import pytest

from dragkraft.dashboard.forms import DashboardFormError, parse_dashboard_form
from dragkraft.vehicles.scenarios import default_scenario


def test_parse_dashboard_form_uses_defaults_for_empty_values() -> None:
    form = parse_dashboard_form({})

    assert form.workbook_path == "old/luleaHamn3.xlsx"
    assert form.output_dir == "runs/dashboard"
    assert form.scenario_name == "Scenario"
    assert form.settings == default_scenario()
    assert form.train.name == "freight"
    assert form.train.adhesion_coefficient == 0.6


def test_parse_dashboard_form_maps_full_editor_values_to_domain_objects() -> None:
    form = parse_dashboard_form(
        {
            "workbook_path": "old/luleaHamn3.xlsx",
            "scenario_name": "Heavy wet rail",
            "sheet_name": "DagensProfil",
            "train_name": "freight",
            "extra_wagon_count": "25",
            "adhesion_coefficient": "0.42",
            "speed_override_kmh": "55",
            "flip_profiles": False,
            "altitude_at_start_m": "12.5",
            "time_offset_s": "3",
            "short_time_margin": "1.2",
            "use_train_length_delay": False,
            "use_distance_before_signal": True,
            "use_tav_distance": False,
            "freight_signal_advance_s_per_mps": "38.5",
            "freight_signal_advance2_s_per_mps": "27.5",
            "freight_signal_advance2_m": "360.25",
            "switch_speed_kmh": "95",
            "use_min_time_to_hold_speed": True,
            "min_time_to_hold_speed_s": "45",
            "speed_tolerance_kmh": "1.5",
            "min_signal_deceleration_mps2": "0.18",
            "reserve_before_arrival_s": "25",
            "output_dir": "runs/custom",
        }
    )

    expected = replace(
        default_scenario(),
        sheet_name="DagensProfil",
        train_name="freight",
        extra_wagon_count=25,
        speed_override_kmh=55.0,
        flip_profiles=False,
        altitude_at_start_m=12.5,
        time_offset_s=3.0,
        short_time_margin=1.2,
        use_train_length_delay=False,
        use_distance_before_signal=True,
        use_tav_distance=False,
        freight_signal_advance_s_per_mps=38.5,
        freight_signal_advance2_s_per_mps=27.5,
        freight_signal_advance2_m=360.25,
        switch_speed_mps=95.0 / 3.6,
        use_min_time_to_hold_speed=True,
        min_time_to_hold_speed_s=45.0,
        speed_tolerance_mps=1.5 / 3.6,
        min_signal_deceleration_mps2=0.18,
        reserve_before_arrival_s=25.0,
    )
    assert form.settings == expected
    assert form.scenario_name == "Heavy wet rail"
    assert form.train.extra_wagon_count == 25
    assert form.train.adhesion_coefficient == 0.42
    assert form.output_dir == "runs/custom"


def test_parse_dashboard_form_rejects_invalid_numeric_values() -> None:
    with pytest.raises(DashboardFormError, match="speed_override_kmh"):
        parse_dashboard_form({"speed_override_kmh": "fast"})


def test_parse_dashboard_form_rejects_invalid_adhesion_values() -> None:
    with pytest.raises(DashboardFormError, match="adhesion_coefficient"):
        parse_dashboard_form({"adhesion_coefficient": "0"})


def test_parse_dashboard_form_rejects_unknown_train_preset() -> None:
    with pytest.raises(DashboardFormError, match="Unsupported train preset"):
        parse_dashboard_form({"train_name": "regional"})
