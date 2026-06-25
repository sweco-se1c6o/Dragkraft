from __future__ import annotations

import json
from pathlib import Path

import pytest

from dragkraft.web.payload import (
    WebFormError,
    parse_form,
    run_simulation,
    run_simulation_json,
    train_library,
)

LOCAL_WORKBOOK = Path(__file__).resolve().parents[1] / "old" / "luleaHamn3.xlsx"


def _skip_without_workbook() -> None:
    if not LOCAL_WORKBOOK.exists():
        pytest.skip("reference workbook is local-only because old/ is git-ignored")


def test_parse_form_rejects_unknown_train_preset() -> None:
    with pytest.raises(WebFormError):
        parse_form({"train_name": "bullet-train"})


def test_train_library_exposes_presets_and_custom() -> None:
    keys = [t["key"] for t in train_library()]
    assert keys[:1] == ["freight"]
    assert "rc4" in keys and "vectron" in keys
    assert "green-cargo" in keys and "iore" in keys and "td" in keys
    assert keys[-1] == "custom"


def test_parse_form_builds_vectron_with_datasheet_specs() -> None:
    train, _s, _n, _sh = parse_form({"train_name": "vectron", "extra_wagon_count": 26})
    assert train.name == "vectron"
    assert train.locomotive_count == 1
    assert train.adhesion_mass_kg == pytest.approx(90_000.0)
    assert train.continuous_power_w == pytest.approx(6.4e6)
    assert train.max_force_n == pytest.approx(300_000.0)


def test_parse_form_builds_selected_library_train() -> None:
    train, _settings, _name, _sheet = parse_form({"train_name": "iore", "extra_wagon_count": 12})
    assert train.name == "iore"
    assert train.locomotive_count == 2


def test_parse_form_overrides_library_consist_mass_and_length() -> None:
    train, _s, _n, _sh = parse_form(
        {
            "train_name": "freight",
            "extra_wagon_count": 26,
            "loco_mass_t": 76,
            "loco_length_m": 15.4,
            "wagon_mass_t": 61.6,
            "wagon_length_m": 19.64,
        }
    )
    assert train.name == "freight"  # still the preset's traction model
    assert train.train_mass_kg == pytest.approx((76 + 26 * 61.6) * 1000.0)
    assert train.train_length_m == pytest.approx(15.4 + 26 * 19.64)
    assert train.adhesion_mass_kg == pytest.approx(76_000.0)


def test_train_library_exposes_lengths_for_prefill() -> None:
    freight = train_library()[0]
    assert {"locomotive_mass_t", "locomotive_length_m", "wagon_mass_t", "wagon_length_m"} <= freight.keys()


def test_parse_form_builds_custom_train_from_params() -> None:
    train, _s, _n, _sh = parse_form(
        {"train_name": "custom", "extra_wagon_count": 8, "custom_max_force_kn": 720}
    )
    assert train.name == "custom"
    assert train.traction_model_type == 1
    assert train.max_force_n == pytest.approx(720_000.0)


def test_run_simulation_json_returns_error_dict_for_bad_form() -> None:
    result = json.loads(run_simulation_json("missing.xlsx", json.dumps({"adhesion_coefficient": -1})))
    assert "error" in result


def test_run_simulation_payload_is_json_serialisable_and_complete() -> None:
    _skip_without_workbook()
    payload = run_simulation(str(LOCAL_WORKBOOK), {})

    # Must round-trip through json with no nan/inf leaking through.
    encoded = json.dumps(payload, allow_nan=False)
    assert isinstance(encoded, str)

    assert payload["stall"] is None
    for key in ("summary", "route", "speed_time", "acceleration", "blocks_chart", "tables"):
        assert key in payload
    assert payload["summary"]["route_length_m"] > 0
    assert len(payload["route"]["position_km"]) == len(payload["route"]["simulated_speed_kmh"])
    assert payload["tables"]["timing"]
    assert payload["tables"]["blocks"]


def test_run_simulation_reports_partial_payload_when_train_stalls() -> None:
    _skip_without_workbook()
    payload = run_simulation(str(LOCAL_WORKBOOK), {"extra_wagon_count": 30})

    json.dumps(payload, allow_nan=False)
    assert payload["stall"] is not None
    assert payload["stall"]["position_m"] == 2581
    assert "Train stalled" in payload["stall"]["message"]
    # Only infrastructure actually reached is reported.
    assert all(p["position_m"] <= 2581 for p in payload["tables"]["timing"])
