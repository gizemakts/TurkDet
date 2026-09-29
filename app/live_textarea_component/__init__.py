"""Live multiline text input used by the TürkDet interface."""

from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "turkdet_live_textarea",
    path=str(Path(__file__).resolve().parent / "frontend"),
)


def live_textarea(
    *,
    value: str,
    placeholder: str,
    height: int,
    debounce_ms: int,
    field_color: str,
    text_color: str,
    muted_color: str,
    border_color: str,
    shadow: str,
    key: str,
) -> str:
    """Render a multiline textarea that commits after a short typing pause."""

    result = _COMPONENT(
        value=value,
        placeholder=placeholder,
        height=height,
        debounce_ms=debounce_ms,
        field_color=field_color,
        text_color=text_color,
        muted_color=muted_color,
        border_color=border_color,
        shadow=shadow,
        default=value,
        key=key,
    )
    return value if result is None else str(result)
