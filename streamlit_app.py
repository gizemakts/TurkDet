"""Streamlit Community Cloud entry point for TürkDet."""

from __future__ import annotations

from pathlib import Path
import runpy


_APP_PATH = Path(__file__).resolve().parent / "app" / "streamlit_app.py"
runpy.run_path(str(_APP_PATH), run_name="__main__")
