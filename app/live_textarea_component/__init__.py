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


def _selected_document_data() -> bytes:
    data = st.session_state.get("selected_document_data", b"")
    if not isinstance(data, (bytes, bytearray)) or not data:
        data = st.session_state.get("uploaded_data_buffer", b"")
    return bytes(data) if isinstance(data, (bytes, bytearray)) else b""


def _buffered_uploaded_document() -> _UploadedDocumentAdapter | None:
    """Return the last selected document when the uploader is remounted."""

    name = _selected_document_name()
    data = _selected_document_data()
    if not name or not data:
        return None
    return _UploadedDocumentAdapter(name, data)


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


def _selection_matches_event(name: str, data: bytes) -> bool:
    """Return True when browser and Python already point to the same file."""

    return _selected_document_name() == name and _selected_document_data() == data


def _persist_selected_document(*, name: str, data: bytes, size: int, mime_type: str) -> None:
    """Atomically replace all document metadata for a newly selected file."""

    st.session_state["selected_document_name"] = name
    st.session_state["selected_document_size"] = size
    st.session_state["selected_document_data"] = data
    st.session_state["selected_document_mime"] = mime_type

    # Mirror metadata for the existing application flow. Reset parsed text so
    # no success message or analysis from the previous document can survive the
    # document replacement render.
    st.session_state["uploaded_name_buffer"] = name
    st.session_state["uploaded_size_buffer"] = size
    st.session_state["uploaded_data_buffer"] = data
    st.session_state["uploaded_mime_buffer"] = mime_type
    st.session_state["uploaded_text_buffer"] = ""


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
            had_selection = bool(_selected_document_name() or _selected_document_data())
            _clear_uploaded_document_state()
            if had_selection:
                st.rerun()
            return None

        if event.kind == "error":
            st.error(event.message)
            return _buffered_uploaded_document()

        # The component renders before Python can persist the newly returned
        # event. Without one synchronization rerun, the browser can briefly be
        # given the previous file metadata while streamlit_app.py still parses
        # the previous adapter. Persist first, rerun once, then parse only when
        # both sides point to the same document.
        event_data = bytes(event.data)
        if not _selection_matches_event(event.name, event_data):
            _persist_selected_document(
                name=event.name,
                data=event_data,
                size=event.size,
                mime_type=event.mime_type,
            )
            st.rerun()

        return _UploadedDocumentAdapter(event.name, event_data)

    # The second marker intentionally prevents app/__init__.py from installing
    # the old CSS-heavy native uploader wrapper after this override is active.
    _turkdet_file_uploader._turkdet_custom_document_uploader = True
    _turkdet_file_uploader._turkdet_premium_uploader = True
    st.file_uploader = _turkdet_file_uploader


_install_document_uploader_override()
