"""Live input widget helpers used by the TürkDet interface."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.document_uploader_component import document_uploader


_COMPONENT = components.declare_component(
    "turkdet_live_textarea",
    path=str(Path(__file__).resolve().parent / "frontend"),
)


class _UploadedDocumentAdapter:
    """Minimal UploadedFile-compatible object consumed by streamlit_app.py."""

    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


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


def _install_document_uploader_override() -> None:
    """Route TürkDet's document field through the custom uploader component."""

    if getattr(st.file_uploader, "_turkdet_custom_document_uploader", False):
        return

    native_file_uploader = st.file_uploader

    def _turkdet_file_uploader(label, *args, **kwargs):
        if kwargs.get("key") != "uploaded_document":
            return native_file_uploader(label, *args, **kwargs)

        event = document_uploader(
            theme_mode=st.session_state.get("theme_mode", "dark"),
            selected_name=str(st.session_state.get("uploaded_name_buffer", "") or ""),
            selected_size=int(st.session_state.get("uploaded_size_buffer", 0) or 0),
            max_size_mb=10,
            key="turkdet_uploaded_document",
        )

        if event is None:
            return None

        if event.kind == "cleared":
            st.session_state["uploaded_text_buffer"] = ""
            st.session_state["uploaded_name_buffer"] = ""
            st.session_state["uploaded_size_buffer"] = 0
            return None

        if event.kind == "error":
            st.error(event.message)
            return None

        st.session_state["uploaded_size_buffer"] = event.size
        return _UploadedDocumentAdapter(event.name, event.data)

    # The second marker intentionally prevents app/__init__.py from installing
    # the old CSS-heavy native uploader wrapper after this override is active.
    _turkdet_file_uploader._turkdet_custom_document_uploader = True
    _turkdet_file_uploader._turkdet_premium_uploader = True
    st.file_uploader = _turkdet_file_uploader


_install_document_uploader_override()
