from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import math

import numpy as np
import pytest
from openpyxl import Workbook

from dragkraft.domain.track import (
    CurveSegment,
    GradientSegment,
    SignalBlock,
    SpeedLimitSegment,
    Stop,
    TimingPoint,
    TrackProfile,
    TunnelSegment,
)
from dragkraft.domain.train import TrainConfig
from dragkraft.simulation.orchestrator import simulate_profile, simulate_workbook
from dragkraft.vehicles.scenarios import default_scenario


def test_simulate_profile_wires_envelope_acceleration_time_and_timing_points() -> None:
    settings = replace(
        default_scenario(),
        flip_profiles=False,
        short_time_margin=1.0,
        use_distance_before_signal=False,
        use_train_length_delay=False,
        time_offset_s=10.0,
    )

    result = simulate_profile(
        profile=_sample_profile(),
        train=_sample_train(),
        settings=settings,
    )

    assert result.route.vectors.max_position_m == 5
    assert result.initial_envelope.candidate_profiles_mps[0, 1:6].tolist() == [2.0] * 5
    assert result.initial_envelope.speed_envelope_mps[4] < 2.0
    assert result.acceleration_profile_mps[1] == pytest.approx(
        result.initial_envelope.speed_envelope_mps[1]
    )
    assert result.speed_profile_mps[1] == pytest.approx(result.acceleration_profile_mps[1])
    assert result.speed_profile_mps[4] == 0.0
    assert result.running_speed_profile_mps[4] > 0.0
    assert result.time_s_per_m[4] == pytest.approx(
        1.0 / result.running_speed_profile_mps[4] + 30.0
    )
    assert result.cumulative_time_s[0] == pytest.approx(10.0)
    assert result.timing_passages[0].name == "TP"
    assert result.timing_passages[0].position_m == 3
    assert result.timing_passages[0].time_s == pytest.approx(result.cumulative_time_s[3])
    assert result.block_occupation.occupations[0].name == "MB1"
    assert result.block_occupation.occupations[0].signal_position_m == 4
    assert result.block_occupation.occupations[0].arrival_time_s == pytest.approx(
        result.cumulative_time_s[4]
    )
    assert result.block_occupation.occupations[0].release_time_s == pytest.approx(
        result.cumulative_time_s[5] + 3.0
    )


def test_simulate_workbook_reads_excel_contract_and_applies_scenario_settings(
    tmp_path: Path,
) -> None:
    workbook_path = tmp_path / "fixed_contract.xlsx"
    _write_fixed_contract_workbook(workbook_path)
    settings = replace(
        default_scenario(),
        sheet_name="NyProfil",
        speed_override_kmh=7.2,
        flip_profiles=False,
        short_time_margin=1.0,
        use_distance_before_signal=False,
        use_train_length_delay=False,
        time_offset_s=0.0,
    )

    result = simulate_workbook(
        workbook_path=workbook_path,
        train=_sample_train(),
        settings=settings,
    )

    assert result.route.vectors.origin_km == 10.0
    assert result.route.vectors.max_position_m == 5
    assert result.initial_envelope.candidate_profiles_mps[0, 1:6].tolist() == [2.0] * 5
    assert result.timing_passages[0].name == "TP"
    assert result.timing_passages[0].position_m == 3


def _sample_profile() -> TrackProfile:
    return TrackProfile(
        sheet_name="Example",
        speed_limits=(SpeedLimitSegment(10.0, 10.005, 7.2),),
        gradients=(GradientSegment(10.0, 10.005, 0.0),),
        tunnels=(TunnelSegment(10.0, 10.005, 0.0),),
        timing_points=(TimingPoint(10.003, "TP"),),
        stops=(Stop(10.004, "Stop", 30.0),),
        curves=(CurveSegment(10.0, 10.005, math.inf),),
        signals=(SignalBlock(10.004, "MB1", 5.0, 0.0, 3.0, 4.0),),
    )


def _sample_train() -> TrainConfig:
    return TrainConfig(
        name="sample",
        locomotive_count=1,
        locomotive_mass_kg=20.0,
        extra_wagon_count=1,
        wagon_mass_kg=80.0,
        train_mass_kg=100.0,
        dynamic_mass_kg=100.0,
        adhesion_mass_kg=20.0,
        adhesion_coefficient=100.0,
        train_length_m=1.0,
        resistance_type=1,
        davis_a_n=0.0,
        davis_b_n_per_mps=0.0,
        davis_c_n_per_mps2=0.0,
        resistance_factor=0.0,
        traction_model_type=2,
        max_force_n=100.0,
        start_force_n=100.0,
        start_force_max_speed_mps=2.0,
        continuous_power_w=1000.0,
        traction_speed_intervals_mps=np.array([[0.0, 10.0]]),
        traction_force_intervals_n=np.array([[100.0, 100.0]]),
        traction_intercepts_n=np.array([100.0]),
        traction_slopes_n_per_mps=np.array([0.0]),
        min_deceleration_mps2=0.1,
        max_deceleration_mps2=1.0,
        max_acceleration_mps2=1.0,
        vehicle_max_speed_mps=2.0,
        braking_speed_intervals_mps=np.array([[0.0, 10.0]]),
        braking_decelerations_mps2=np.array([0.5]),
    )


def _write_fixed_contract_workbook(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "NyProfil"

    worksheet["B5"] = 10.0
    worksheet["C5"] = 10.005
    worksheet["D5"] = 99.0

    worksheet["G5"] = 10.0
    worksheet["H5"] = 10.005
    worksheet["I5"] = 0.0

    worksheet["L5"] = 10.0
    worksheet["M5"] = 10.005
    worksheet["N5"] = 0.0

    worksheet["Q5"] = 10.003
    worksheet["R5"] = "TP"

    worksheet["T5"] = 10.004
    worksheet["U5"] = "Stop"
    worksheet["V5"] = 30.0

    worksheet["Y5"] = 10.0
    worksheet["Z5"] = 10.005
    worksheet["AA5"] = 99999

    worksheet["AD5"] = 10.004
    worksheet["AE5"] = "MB1"
    worksheet["AF5"] = 5.0
    worksheet["AG5"] = 0.0
    worksheet["AH5"] = 3.0
    worksheet["AI5"] = 4.0

    workbook.save(path)
