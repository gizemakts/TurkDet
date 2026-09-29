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


def _selected_document_name() -> str:
    return str(
        st.session_state.get("selected_document_name", "")
        or st.session_state.get("uploaded_name_buffer", "")
        or ""
    )


def _selected_document_size() -> int:
    return int(
        st.session_state.get("selected_document_size", 0)
        or st.session_state.get("uploaded_size_buffer", 0)
        or 0
    )


def _buffered_uploaded_document() -> _UploadedDocumentAdapter | None:
    """Return the last selected document when the uploader is remounted."""

    name = _selected_document_name()
    data = st.session_state.get("selected_document_data", b"")
    if not isinstance(data, (bytes, bytearray)) or not data:
        data = st.session_state.get("uploaded_data_buffer", b"")
    if not name or not isinstance(data, (bytes, bytearray)) or not data:
        return None
    return _UploadedDocumentAdapter(name, bytes(data))


def _clear_uploaded_document_state() -> None:
    """Clear document state only after an explicit remove action."""

    # Parsed-text state used by streamlit_app.py.
    st.session_state["uploaded_text_buffer"] = ""
    st.session_state["uploaded_name_buffer"] = ""
    st.session_state["uploaded_size_buffer"] = 0
    st.session_state["uploaded_data_buffer"] = b""
    st.session_state["uploaded_mime_buffer"] = ""

    # Selection state owned by the uploader itself. This is intentionally kept
    # separate from parsed-text state so parser errors cannot discard a file.
    st.session_state["selected_document_name"] = ""
    st.session_state["selected_document_size"] = 0
    st.session_state["selected_document_data"] = b""
    st.session_state["selected_document_mime"] = ""


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
            selected_name=_selected_document_name(),
            selected_size=_selected_document_size(),
            max_size_mb=10,
            key="turkdet_uploaded_document",
        )

        # Conditional Streamlit widgets are removed when the user switches to
        # the pasted-text tab. Restore the last document when this component is
        # mounted again instead of treating it as a brand-new empty uploader.
        if event is None:
            return _buffered_uploaded_document()

        if event.kind == "cleared":
            _clear_uploaded_document_state()
            return None

        if event.kind == "error":
            st.error(event.message)
            return _buffered_uploaded_document()

        # Persist the file selection independently from text extraction. A
        # parser failure (for example a scanned PDF without a text layer) may
        # clear uploaded_text_buffer, but must never clear this selection state.
        st.session_state["selected_document_name"] = event.name
        st.session_state["selected_document_size"] = event.size
        st.session_state["selected_document_data"] = event.data
        st.session_state["selected_document_mime"] = event.mime_type

        # Mirror metadata for the existing app flow. These keys may be changed
        # by parsing logic without affecting the durable selection above.
        st.session_state["uploaded_name_buffer"] = event.name
        st.session_state["uploaded_size_buffer"] = event.size
        st.session_state["uploaded_data_buffer"] = event.data
        st.session_state["uploaded_mime_buffer"] = event.mime_type
        st.session_state["uploaded_text_buffer"] = ""
        return _UploadedDocumentAdapter(event.name, event.data)

    # The second marker intentionally prevents app/__init__.py from installing
    # the old CSS-heavy native uploader wrapper after this override is active.
    _turkdet_file_uploader._turkdet_custom_document_uploader = True
    _turkdet_file_uploader._turkdet_premium_uploader = True
    st.file_uploader = _turkdet_file_uploader


_install_document_uploader_override()
