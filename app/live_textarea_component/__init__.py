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


def _install_expander_theme_override() -> None:
    """Keep native Streamlit expanders stable during runtime theme changes."""

    if getattr(st.expander, "_turkdet_themed_expander", False):
        return

    native_expander = st.expander

    def _turkdet_expander(label, *args, **kwargs):
        is_dark = st.session_state.get("theme_mode", "dark") == "dark"
        if is_dark:
            surface = "rgba(255,255,255,.025)"
            content = "#0E131C"
            text = "#F4F7FB"
            muted = "#97A3B6"
            border = "rgba(255,255,255,.105)"
        else:
            surface = "rgba(99,102,241,.025)"
            content = "#FFFFFF"
            text = "#111827"
            muted = "#667085"
            border = "rgba(15,23,42,.105)"

        # Deliberately use the same translucent indigo header in both themes.
        # Streamlit toggles theme through a rerun, so a theme-specific dark/light
        # header creates a visible black-to-white flash while the new render is
        # replacing the old one. Keeping the header chroma stable removes that
        # perceptual jump while the surrounding page changes theme normally.
        header = "rgba(99,102,241,.085)"
        header_hover = "rgba(99,102,241,.125)"

        st.markdown(
            f"""
            <style>
              details[data-testid="stExpander"],
              [data-testid="stExpander"] {{
                background:{surface} !important;
                border:1px solid {border} !important;
                border-radius:12px !important;
                overflow:hidden !important;
                transition:background-color .18s ease,border-color .18s ease !important;
              }}

              details[data-testid="stExpander"] > summary,
              [data-testid="stExpander"] summary,
              [data-testid="stExpander"] summary:focus,
              [data-testid="stExpander"] summary:focus-visible,
              [data-testid="stExpander"][open] summary {{
                background:{header} !important;
                background-color:{header} !important;
                color:{text} !important;
                border:0 !important;
                outline:0 !important;
                box-shadow:none !important;
                transition:background-color .16s ease,color .16s ease !important;
              }}

              [data-testid="stExpander"] summary:hover {{
                background:{header_hover} !important;
                background-color:{header_hover} !important;
                color:{text} !important;
              }}

              [data-testid="stExpander"] summary > div,
              [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],
              [data-testid="stExpander"] summary p,
              [data-testid="stExpander"] summary span,
              [data-testid="stExpander"] summary svg {{
                background:transparent !important;
                background-color:transparent !important;
                color:{text} !important;
                fill:currentColor !important;
                transition:color .16s ease !important;
              }}

              [data-testid="stExpanderDetails"] {{
                background:{content} !important;
                background-color:{content} !important;
                color:{text} !important;
                border-top:1px solid {border} !important;
                transition:background-color .18s ease,color .18s ease,border-color .18s ease !important;
              }}

              [data-testid="stExpanderDetails"] p,
              [data-testid="stExpanderDetails"] span,
              [data-testid="stExpanderDetails"] div {{
                color:{text};
              }}

              [data-testid="stExpanderDetails"] [data-testid="stCaptionContainer"] {{
                color:{muted} !important;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        return native_expander(label, *args, **kwargs)

    _turkdet_expander._turkdet_themed_expander = True
    st.expander = _turkdet_expander


_install_document_uploader_override()
_install_expander_theme_override()
