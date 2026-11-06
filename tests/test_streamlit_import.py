"""Smoke: streamlit_app defines main without executing Streamlit on import."""

from __future__ import annotations

import streamlit_app


def test_streamlit_app_has_main() -> None:
    assert callable(getattr(streamlit_app, "main", None))
