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
    assert "green-cargo" in keys and "iore" in keys and "td" in keys
    assert keys[-1] == "custom"


def test_parse_form_builds_selected_library_train() -> None:
    train, _settings, _name, _sheet = parse_form({"train_name": "iore", "extra_wagon_count": 12})
    assert train.name == "iore"
    assert train.locomotive_count == 2


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
