from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook

from dragkraft.cli import main


def test_cli_run_writes_outputs_for_fixed_contract_workbook(tmp_path: Path) -> None:
    workbook_path = tmp_path / "fixed_contract.xlsx"
    output_dir = tmp_path / "out"
    _write_workbook(workbook_path)

    exit_code = main(
        [
            "run",
            str(workbook_path),
            "--sheet",
            "NyProfil",
            "--train",
            "freight",
            "--extra-wagons",
            "0",
            "--max-speed-kmh",
            "7.2",
            "--no-flip",
            "--out",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "timing_points.csv").exists()
    assert (output_dir / "block_occupation.csv").exists()
    assert (output_dir / "speed_profile.csv").exists()
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["route_length_m"] == 100
    assert summary["timing_point_count"] == 1
    assert summary["block_count"] == 1


def _write_workbook(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "NyProfil"

    worksheet["B5"] = 10.0
    worksheet["C5"] = 10.1
    worksheet["D5"] = 99.0

    worksheet["G5"] = 10.0
    worksheet["H5"] = 10.1
    worksheet["I5"] = 0.0

    worksheet["L5"] = 10.0
    worksheet["M5"] = 10.1
    worksheet["N5"] = 0.0

    worksheet["Q5"] = 10.04
    worksheet["R5"] = "TP"

    worksheet["Y5"] = 10.0
    worksheet["Z5"] = 10.1
    worksheet["AA5"] = 99999

    worksheet["AD5"] = 10.05
    worksheet["AE5"] = "MB1"
    worksheet["AF5"] = 5.0
    worksheet["AG5"] = 0.0
    worksheet["AH5"] = 3.0
    worksheet["AI5"] = 4.0

    workbook.save(path)
