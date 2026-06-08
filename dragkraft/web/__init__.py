"""Dash-free entry points for the static (browser/Pyodide) frontend."""

from dragkraft.web.payload import (
    WebFormError,
    build_payload,
    default_form_values,
    run_simulation,
    run_simulation_json,
)

__all__ = [
    "WebFormError",
    "build_payload",
    "default_form_values",
    "run_simulation",
    "run_simulation_json",
]
