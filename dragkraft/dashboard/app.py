from __future__ import annotations

import argparse
from collections.abc import Sequence

from dash import Dash, dcc, html

from dragkraft.dashboard.callbacks import (
    block_table,
    comparison_table,
    register_callbacks,
    timing_table,
)
from dragkraft.dashboard.forms import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WORKBOOK_PATH,
    TRAIN_PRESETS,
)
from dragkraft.vehicles.scenarios import default_scenario


def create_app() -> Dash:
    app = Dash(__name__, title="Dragkraft Dashboard")
    app.layout = _layout()
    register_callbacks(app)
    return app


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dragkraft dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def _layout() -> html.Div:
    settings = default_scenario()
    return html.Div(
        [
            dcc.Store(id="current-scenario-store", storage_type="memory"),
            dcc.Store(id="saved-scenarios-store", storage_type="memory", data=[]),
            html.A("Skip to plots", href="#plots", className="skip-link"),
            html.Aside(
                [
                    html.Header(
                        [
                            html.Div("Dragkraft", className="brand"),
                            html.Div("Simulation", className="subtitle"),
                        ],
                        className="sidebar-header",
                    ),
                    html.Section(
                        [
                            html.H2("Workbook"),
                            dcc.Upload(
                                id="workbook-upload",
                                children=html.Div("Upload Excel workbook"),
                                className="upload-zone",
                                multiple=False,
                            ),
                            html.Div(id="upload-status", className="upload-status"),
                            _text_input("Workbook path", "workbook_path", DEFAULT_WORKBOOK_PATH),
                            _text_input("Sheet", "sheet_name", settings.sheet_name),
                            _text_input("Scenario name", "scenario_name", "Scenario"),
                        ],
                        className="control-section",
                    ),
                    html.Section(
                        [
                            html.H2("Train"),
                            html.Label(
                                [
                                    html.Span("Preset"),
                                    dcc.Dropdown(
                                        id="train_name",
                                        options=[
                                            {"label": preset, "value": preset}
                                            for preset in TRAIN_PRESETS
                                        ],
                                        value=settings.train_name,
                                        clearable=False,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    _number_input(
                                        "Extra wagons",
                                        "extra_wagon_count",
                                        settings.extra_wagon_count,
                                        step=1,
                                    ),
                                    _number_input(
                                        "Adhesion coeff.",
                                        "adhesion_coefficient",
                                        0.6,
                                        step=0.01,
                                    ),
                                    _number_input(
                                        "Max speed [km/h]",
                                        "speed_override_kmh",
                                        settings.speed_override_kmh,
                                    ),
                                ],
                                className="field-grid",
                            ),
                        ],
                        className="control-section",
                    ),
                    html.Section(
                        [
                            html.H2("Display"),
                            _checklist(
                                "Direction",
                                "flip_profiles",
                                "Flip profile",
                                settings.flip_profiles,
                            ),
                            _checklist(
                                "Curves",
                                "include_candidate_curves",
                                "Show constraint candidates",
                                True,
                            ),
                        ],
                        className="control-section compact",
                    ),
                    html.Details(
                        [
                            html.Summary("Route and timing"),
                            _number_input(
                                "Altitude start [m]",
                                "altitude_at_start_m",
                                settings.altitude_at_start_m,
                            ),
                            _number_input(
                                "Time offset [s]",
                                "time_offset_s",
                                settings.time_offset_s,
                            ),
                            _number_input(
                                "Short time margin",
                                "short_time_margin",
                                settings.short_time_margin,
                            ),
                            _checklist(
                                "Train delay",
                                "use_train_length_delay",
                                "Use train length delay",
                                settings.use_train_length_delay,
                            ),
                            _checklist(
                                "Signal distance",
                                "use_distance_before_signal",
                                "Use distance before signal",
                                settings.use_distance_before_signal,
                            ),
                            _checklist(
                                "TAV distance",
                                "use_tav_distance",
                                "Use TAV distance",
                                settings.use_tav_distance,
                            ),
                        ],
                        open=True,
                        className="control-section",
                    ),
                    html.Details(
                        [
                            html.Summary("Signals and braking"),
                            _number_input(
                                "Advance [s/(m/s)]",
                                "freight_signal_advance_s_per_mps",
                                settings.freight_signal_advance_s_per_mps,
                            ),
                            _number_input(
                                "Advance 2 [s/(m/s)]",
                                "freight_signal_advance2_s_per_mps",
                                settings.freight_signal_advance2_s_per_mps,
                            ),
                            _number_input(
                                "Advance 2 [m]",
                                "freight_signal_advance2_m",
                                settings.freight_signal_advance2_m,
                            ),
                            _number_input(
                                "Switch speed [km/h]",
                                "switch_speed_kmh",
                                settings.switch_speed_mps * 3.6,
                            ),
                            _checklist(
                                "Hold speed",
                                "use_min_time_to_hold_speed",
                                "Use min hold time",
                                settings.use_min_time_to_hold_speed,
                            ),
                            _number_input(
                                "Min hold time [s]",
                                "min_time_to_hold_speed_s",
                                settings.min_time_to_hold_speed_s,
                            ),
                            _number_input(
                                "Speed tolerance [km/h]",
                                "speed_tolerance_kmh",
                                settings.speed_tolerance_mps * 3.6,
                            ),
                            _number_input(
                                "Min signal decel [m/s2]",
                                "min_signal_deceleration_mps2",
                                settings.min_signal_deceleration_mps2,
                            ),
                            _number_input(
                                "Reserve before arrival [s]",
                                "reserve_before_arrival_s",
                                settings.reserve_before_arrival_s,
                            ),
                        ],
                        open=False,
                        className="control-section",
                    ),
                    html.Section(
                        [
                            html.H2("Outputs"),
                            _text_input("Output directory", "output_dir", DEFAULT_OUTPUT_DIR),
                        ],
                        className="control-section",
                    ),
                    html.Button("Run simulation", id="run-button", n_clicks=0),
                    html.Div(
                        [
                            html.Button(
                                "Save scenario",
                                id="save-scenario-button",
                                n_clicks=0,
                                className="secondary-button",
                            ),
                            html.Button(
                                "Clear saved",
                                id="clear-scenarios-button",
                                n_clicks=0,
                                className="ghost-button",
                            ),
                        ],
                        className="scenario-actions",
                    ),
                    html.Div(id="comparison-status", className="comparison-status"),
                    html.Div(id="status", className="status"),
                    html.Div(id="export-status", className="export-status"),
                ],
                className="sidebar",
            ),
            html.Main(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.H1("Simulation Workspace"),
                                    html.Div(
                                        "Train traction simulation with interactive Plotly views",
                                        className="workspace-subtitle",
                                    ),
                                ]
                            ),
                        ],
                        className="workspace-header",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div("Run a simulation", className="metric-label"),
                                    html.Div("No results yet", className="metric-value"),
                                    html.Div("Use the controls on the left", className="metric-detail"),
                                ],
                                className="metric-card placeholder",
                            )
                        ],
                        id="result-cards",
                        className="result-cards",
                    ),
                    dcc.Tabs(
                        id="plots",
                        value="route",
                        className="plot-tabs",
                        children=[
                            dcc.Tab(
                                label="Route Profile",
                                value="route",
                                className="plot-tab",
                                selected_className="plot-tab selected",
                                children=[
                                    dcc.Graph(
                                        id="route-profile-graph",
                                        className="graph-panel",
                                        style={"height": "calc(100vh - 190px)"},
                                        config={"displaylogo": False},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Speed-Time",
                                value="speed",
                                className="plot-tab",
                                selected_className="plot-tab selected",
                                children=[
                                    dcc.Graph(
                                        id="speed-time-graph",
                                        className="graph-panel",
                                        style={"height": "calc(100vh - 190px)"},
                                        config={"displaylogo": False},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Acceleration",
                                value="acceleration",
                                className="plot-tab",
                                selected_className="plot-tab selected",
                                children=[
                                    dcc.Graph(
                                        id="acceleration-graph",
                                        className="graph-panel",
                                        style={"height": "calc(100vh - 190px)"},
                                        config={"displaylogo": False},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Block Occupation",
                                value="blocks",
                                className="plot-tab",
                                selected_className="plot-tab selected",
                                children=[
                                    dcc.Graph(
                                        id="block-occupation-graph",
                                        className="graph-panel",
                                        style={"height": "calc(100vh - 190px)"},
                                        config={"displaylogo": False},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Compare Scenarios",
                                value="compare",
                                className="plot-tab",
                                selected_className="plot-tab selected",
                                children=[
                                    html.Section(
                                        [
                                            dcc.Graph(
                                                id="comparison-position-graph",
                                                className="comparison-graph",
                                                style={"height": "40vh"},
                                                config={"displaylogo": False},
                                            ),
                                            dcc.Graph(
                                                id="comparison-time-graph",
                                                className="comparison-graph",
                                                style={"height": "40vh"},
                                                config={"displaylogo": False},
                                            ),
                                            html.H2("Saved Scenario Summary"),
                                            comparison_table(),
                                        ],
                                        className="tables comparison-panel",
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Tables / Export",
                                value="tables",
                                className="plot-tab",
                                selected_className="plot-tab selected",
                                children=[
                                    html.Section(
                                        [
                                            html.H2("Summary"),
                                            html.Pre(id="summary-json"),
                                            html.H2("Timing Points"),
                                            timing_table(),
                                            html.H2("Block Occupation"),
                                            block_table(),
                                        ],
                                        className="tables",
                                    )
                                ],
                            ),
                        ],
                    )
                ],
                className="main",
            ),
        ],
        className="app-shell",
    )


def _text_input(label: str, element_id: str, value: str):
    return html.Label(
        [
            html.Span(label),
            dcc.Input(id=element_id, type="text", value=value, debounce=True),
        ]
    )


def _number_input(label: str, element_id: str, value: float, *, step: float = 0.1):
    return html.Label(
        [
            html.Span(label),
            dcc.Input(id=element_id, type="number", value=value, step=step),
        ]
    )


def _checklist(label: str, element_id: str, text: str, checked: bool):
    return html.Label(
        [
            html.Span(label),
            dcc.Checklist(
                id=element_id,
                options=[{"label": text, "value": element_id}],
                value=[element_id] if checked else [],
            ),
        ]
    )
