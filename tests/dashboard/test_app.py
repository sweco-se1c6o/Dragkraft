from __future__ import annotations

from dash import Dash

from dragkraft.dashboard.app import create_app


def test_create_app_returns_dash_instance_with_layout() -> None:
    app = create_app()

    assert isinstance(app, Dash)
    assert app.layout is not None
