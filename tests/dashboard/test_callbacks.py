from __future__ import annotations

from types import SimpleNamespace

from dragkraft.dashboard.callbacks import _run_status, simulation_error_message
from dragkraft.dashboard.forms import DashboardFormError
from dragkraft.simulation.acceleration import StallPoint


def test_run_status_warns_and_keeps_results_for_a_stalled_train() -> None:
    result = SimpleNamespace(
        stall=StallPoint(position_m=2581, speed_mps=0.0957, acceleration_mps2=-0.0821)
    )
    summary = {"route_length_m": 4000, "total_time_s": 312.4}

    status = _run_status(result=result, summary=summary)

    assert status.className == "status-warn"
    text = "".join(str(child) for child in status.children)
    assert "Train stalled" in status.children[0].children
    assert "2581 m" in text


def test_run_status_reports_ready_when_not_stalled() -> None:
    result = SimpleNamespace(stall=None)
    summary = {"route_length_m": 4000, "total_time_s": 312.4}

    status = _run_status(result=result, summary=summary)

    assert status.className == "status-ok"


def test_simulation_error_message_suppresses_traceback_for_form_errors() -> None:
    message = simulation_error_message(DashboardFormError("Workbook does not exist"))

    assert "Workbook does not exist" in message
    assert "Traceback" not in message
