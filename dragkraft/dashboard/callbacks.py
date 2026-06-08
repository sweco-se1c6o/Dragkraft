from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any

from dash import Input, Output, State, callback_context, dash_table, html
from dash.exceptions import PreventUpdate

from dragkraft.dashboard.figures import (
    build_acceleration_figure,
    build_block_occupation_figure,
    build_route_profile_figure,
    build_speed_time_figure,
)
from dragkraft.dashboard.forms import DashboardFormError, parse_dashboard_form
from dragkraft.dashboard.results import build_result_summary
from dragkraft.dashboard.results import (
    build_comparison_rows,
    build_comparison_speed_position_figure,
    build_comparison_speed_time_figure,
    build_scenario_snapshot,
)
from dragkraft.dashboard.uploads import UploadError, save_uploaded_workbook
from dragkraft.io.outputs import write_simulation_outputs
from dragkraft.simulation.orchestrator import simulate_workbook


FORM_STATE_IDS = (
    "scenario_name",
    "workbook_path",
    "sheet_name",
    "train_name",
    "extra_wagon_count",
    "adhesion_coefficient",
    "speed_override_kmh",
    "flip_profiles",
    "altitude_at_start_m",
    "time_offset_s",
    "short_time_margin",
    "use_train_length_delay",
    "use_distance_before_signal",
    "use_tav_distance",
    "freight_signal_advance_s_per_mps",
    "freight_signal_advance2_s_per_mps",
    "freight_signal_advance2_m",
    "switch_speed_kmh",
    "use_min_time_to_hold_speed",
    "min_time_to_hold_speed_s",
    "speed_tolerance_kmh",
    "min_signal_deceleration_mps2",
    "reserve_before_arrival_s",
    "include_candidate_curves",
    "output_dir",
)


def register_callbacks(app) -> None:
    @app.callback(
        Output("workbook_path", "value"),
        Output("upload-status", "children"),
        Input("workbook-upload", "contents"),
        State("workbook-upload", "filename"),
        prevent_initial_call=True,
    )
    def save_uploaded_excel(contents: str | None, filename: str | None):
        if not contents:
            raise PreventUpdate
        try:
            path = save_uploaded_workbook(contents=contents, filename=filename)
        except UploadError as exc:
            return "", html.Span(str(exc), className="upload-error")
        return str(path), html.Span(f"Loaded {filename}", className="upload-ok")

    @app.callback(
        Output("status", "children"),
        Output("route-profile-graph", "figure"),
        Output("speed-time-graph", "figure"),
        Output("acceleration-graph", "figure"),
        Output("block-occupation-graph", "figure"),
        Output("result-cards", "children"),
        Output("summary-json", "children"),
        Output("timing-table", "data"),
        Output("block-table", "data"),
        Output("export-status", "children"),
        Output("current-scenario-store", "data"),
        Input("run-button", "n_clicks"),
        [State(field_id, "value") for field_id in FORM_STATE_IDS],
    )
    def run_simulation(n_clicks: int | None, *state_values: Any):
        del n_clicks
        values = dict(zip(FORM_STATE_IDS, state_values, strict=True))
        try:
            form = parse_dashboard_form(values)
            workbook = Path(form.workbook_path)
            if not workbook.exists():
                raise DashboardFormError(f"Workbook does not exist: {workbook}")
            result = simulate_workbook(
                workbook_path=workbook,
                train=form.train,
                settings=form.settings,
            )
            output_paths = write_simulation_outputs(
                result=result,
                output_dir=form.output_dir,
            )
        except Exception as exc:  # noqa: BLE001 - surfaced as local app status.
            return _error_payload(exc)

        summary = build_result_summary(
            result=result,
            train=form.train,
            settings=form.settings,
            workbook_path=workbook,
        )
        paths_text = "Exported: " + ", ".join(
            f"{name}={path}" for name, path in output_paths.items()
        )
        return (
            _run_status(result=result, summary=summary),
            build_route_profile_figure(
                result=result,
                settings=form.settings,
                include_candidate_curves=bool(values["include_candidate_curves"]),
            ),
            build_speed_time_figure(result=result),
            build_acceleration_figure(result=result),
            build_block_occupation_figure(result=result, settings=form.settings),
            _result_cards(summary),
            json.dumps(summary, indent=2),
            [
                {
                    "position_m": passage.position_m,
                    "name": passage.name,
                    "time_s": round(passage.time_s, 3),
                }
                for passage in result.timing_passages
            ],
            [
                {
                    "name": block.name,
                    "signal_position_m": block.signal_position_m,
                    "speed_difference_mps": round(block.speed_difference_mps, 6),
                    "intersection_position_m": block.intersection_position_m,
                    "booking_time_s": round(block.booking_time_s, 3),
                    "arrival_time_s": round(block.arrival_time_s, 3),
                    "release_time_s": round(block.release_time_s, 3),
                }
                for block in result.block_occupation.occupations
            ],
            paths_text,
            build_scenario_snapshot(
                label=form.scenario_name,
                result=result,
                train=form.train,
                settings=form.settings,
                workbook_path=workbook,
            ),
        )

    @app.callback(
        Output("saved-scenarios-store", "data"),
        Output("comparison-status", "children"),
        Output("comparison-position-graph", "figure"),
        Output("comparison-time-graph", "figure"),
        Output("comparison-table", "data"),
        Input("save-scenario-button", "n_clicks"),
        Input("clear-scenarios-button", "n_clicks"),
        State("current-scenario-store", "data"),
        State("saved-scenarios-store", "data"),
        prevent_initial_call=True,
    )
    def update_saved_scenarios(
        save_clicks: int | None,
        clear_clicks: int | None,
        current: dict[str, Any] | None,
        saved: list[dict[str, Any]] | None,
    ):
        del save_clicks, clear_clicks
        trigger = callback_context.triggered[0]["prop_id"].split(".")[0]
        snapshots = list(saved or [])
        if trigger == "clear-scenarios-button":
            snapshots = []
            status = "Saved scenarios cleared"
        elif current is None:
            status = "Run a simulation before saving a scenario"
        else:
            snapshots.append(current)
            status = f"Saved {len(snapshots)} scenario(s) in this browser session"
        return (
            snapshots,
            status,
            build_comparison_speed_position_figure(snapshots),
            build_comparison_speed_time_figure(snapshots),
            build_comparison_rows(snapshots),
        )


def _run_status(*, result: Any, summary: dict[str, Any]):
    if result.stall is not None:
        return html.Div(
            [
                html.Strong("Train stalled — partial result"),
                html.Span(
                    f" Reached {result.stall.position_m} m in "
                    f"{summary['total_time_s']:.1f} s before traction could no "
                    f"longer keep the consist moving "
                    f"(speed {result.stall.speed_mps:.3f} m/s, "
                    f"acceleration {result.stall.acceleration_mps2:.3f} m/s^2). "
                    "Reduce wagons or raise adhesion to complete the route.",
                ),
            ],
            className="status-warn",
        )
    return html.Div(
        [
            html.Strong("Simulation ready"),
            html.Span(
                f" {summary['route_length_m']} m, {summary['total_time_s']:.1f} s",
            ),
        ],
        className="status-ok",
    )


def _error_payload(exc: Exception):
    message = simulation_error_message(exc)
    empty = {}
    return (
        html.Pre(message, className="status-error"),
        empty,
        empty,
        empty,
        empty,
        [],
        "{}",
        [],
        [],
        "",
        None,
    )


def simulation_error_message(exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if isinstance(exc, DashboardFormError):
        return message
    return message + "\n" + traceback.format_exc(limit=2)


def _result_cards(summary: dict[str, Any]) -> list[html.Div]:
    cards = [
        ("Run time", f"{summary['total_time_s']:.1f} s", "Simulation duration"),
        ("Route", f"{summary['route_length_m']} m", summary["sheet"]),
        ("Max speed", f"{summary['simulated_max_speed_kmh']:.1f} km/h", "Simulated"),
        ("Vehicle", summary["vehicle_type"], summary["train_name"]),
        ("Consist", f"{summary['locomotives']} loco / {summary['wagons']} wagons", "Rolling stock"),
        ("Train mass", f"{summary['train_mass_t']:.1f} t", f"Dynamic {summary['dynamic_mass_t']:.1f} t"),
        ("Length", f"{summary['train_length_m']:.1f} m", f"Adhesion {summary['adhesion_mass_t']:.1f} t"),
        ("Models", f"T {summary['traction_model']} / R {summary['resistance_model']}", "Traction / resistance"),
        (
            "Braking",
            (
                f"{summary['brake_deceleration_min_mps2']:.3f}-"
                f"{summary['brake_deceleration_max_mps2']:.3f} m/s^2"
            ),
            "Deceleration table range",
        ),
        ("Infrastructure", f"{summary['timing_points']} timing / {summary['blocks']} blocks", "Workbook signals"),
    ]
    return [
        html.Div(
            [
                html.Div(label, className="metric-label"),
                html.Div(value, className="metric-value"),
                html.Div(detail, className="metric-detail"),
            ],
            className="metric-card",
        )
        for label, value, detail in cards
    ]


def timing_table() -> dash_table.DataTable:
    return dash_table.DataTable(
        id="timing-table",
        columns=[
            {"name": "Position [m]", "id": "position_m"},
            {"name": "Name", "id": "name"},
            {"name": "Time [s]", "id": "time_s"},
        ],
        data=[],
        page_size=12,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "Inter, Segoe UI, sans-serif",
            "fontSize": 13,
            "padding": "8px",
        },
        style_header={
            "backgroundColor": "#edf2f7",
            "fontWeight": "700",
        },
    )


def block_table() -> dash_table.DataTable:
    return dash_table.DataTable(
        id="block-table",
        columns=[
            {"name": "Name", "id": "name"},
            {"name": "Signal [m]", "id": "signal_position_m"},
            {"name": "Speed diff [m/s]", "id": "speed_difference_mps"},
            {"name": "Intersection [m]", "id": "intersection_position_m"},
            {"name": "Booking [s]", "id": "booking_time_s"},
            {"name": "Arrival [s]", "id": "arrival_time_s"},
            {"name": "Release [s]", "id": "release_time_s"},
        ],
        data=[],
        page_size=12,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "Inter, Segoe UI, sans-serif",
            "fontSize": 13,
            "padding": "8px",
        },
        style_header={
            "backgroundColor": "#edf2f7",
            "fontWeight": "700",
        },
    )


def comparison_table() -> dash_table.DataTable:
    return dash_table.DataTable(
        id="comparison-table",
        columns=[
            {"name": "#", "id": "index"},
            {"name": "Scenario", "id": "label"},
            {"name": "Total [s]", "id": "total_time_s"},
            {"name": "Delta [s]", "id": "delta_time_s"},
            {"name": "Route [m]", "id": "route_length_m"},
            {"name": "Wagons", "id": "wagons"},
            {"name": "Adhesion", "id": "adhesion_coefficient"},
            {"name": "Mass [t]", "id": "train_mass_t"},
            {"name": "Max [km/h]", "id": "max_speed_kmh"},
        ],
        data=[],
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "Inter, Segoe UI, sans-serif",
            "fontSize": 13,
            "padding": "8px",
        },
        style_header={
            "backgroundColor": "#edf2f7",
            "fontWeight": "700",
        },
    )
