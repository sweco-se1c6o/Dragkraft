from __future__ import annotations

import math
from pathlib import Path

import pytest
from openpyxl import Workbook

from dragkraft.io.excel_reader import FormulaCacheError, read_track_profile


LEGACY_WORKBOOK = Path(__file__).resolve().parents[1] / "old" / "luleaHamn3.xlsx"


EXPECTED_COUNTS = {
    "DagensProfil": {
        "speed_limits": 4,
        "gradients": 18,
        "tunnels": 1,
        "timing_points": 2,
        "stops": 1,
        "curves": 26,
        "signals": 2,
    },
    "NyProfil": {
        "speed_limits": 4,
        "gradients": 18,
        "tunnels": 1,
        "timing_points": 2,
        "stops": 1,
        "curves": 26,
        "signals": 2,
    },
    "SpeedTest": {
        "speed_limits": 4,
        "gradients": 2,
        "tunnels": 1,
        "timing_points": 2,
        "stops": 0,
        "curves": 3,
        "signals": 2,
    },
}


def require_legacy_workbook() -> Path:
    if not LEGACY_WORKBOOK.exists():
        pytest.skip("legacy workbook is local-only because old/ is git-ignored")
    return LEGACY_WORKBOOK


@pytest.mark.parametrize("sheet_name, counts", EXPECTED_COUNTS.items())
def test_reads_legacy_workbook_fixed_blocks(sheet_name: str, counts: dict[str, int]) -> None:
    profile = read_track_profile(require_legacy_workbook(), sheet_name)

    assert len(profile.speed_limits) == counts["speed_limits"]
    assert len(profile.gradients) == counts["gradients"]
    assert len(profile.tunnels) == counts["tunnels"]
    assert len(profile.timing_points) == counts["timing_points"]
    assert len(profile.stops) == counts["stops"]
    assert len(profile.curves) == counts["curves"]
    assert len(profile.signals) == counts["signals"]


def test_speed_override_preserves_rows_and_replaces_speed_values() -> None:
    profile = read_track_profile(
        require_legacy_workbook(),
        "NyProfil",
        speed_override_kmh=40,
    )

    assert len(profile.speed_limits) == EXPECTED_COUNTS["NyProfil"]["speed_limits"]
    assert {segment.speed_kmh for segment in profile.speed_limits} == {40.0}


def test_curve_radius_sentinel_becomes_infinity() -> None:
    profile = read_track_profile(require_legacy_workbook(), "NyProfil")

    assert any(math.isinf(curve.radius_m) for curve in profile.curves)


def test_raises_when_formula_cell_has_no_cached_value(tmp_path: Path) -> None:
    workbook_path = tmp_path / "formula_without_cache.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "NyProfil"
    worksheet["B4"] = "from"
    worksheet["C4"] = "to"
    worksheet["D4"] = "speed"
    worksheet["B5"] = 0
    worksheet["C5"] = "=B5 + 1"
    worksheet["D5"] = 40
    workbook.save(workbook_path)

    with pytest.raises(FormulaCacheError, match="C5"):
        read_track_profile(workbook_path, "NyProfil")
