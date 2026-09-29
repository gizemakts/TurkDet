"""TürkDet web application package."""

from __future__ import annotations

import streamlit as st

from app.live_textarea_component import live_textarea


# Keep small presentation-only adjustments close to the wrapped Streamlit
# widgets. Suppress obsolete helper copy and inject spacing CSS separately so
# it can never be rendered as visible text inside the summary markup.
if not getattr(st.markdown, "_turkdet_markdown", False):
    _streamlit_markdown = st.markdown

    def _turkdet_markdown(body, *args, **kwargs):
        if isinstance(body, str) and "Belge özeti yazdıkça güncellenir." in body:
            return None

        if isinstance(body, str) and "Belgenizi buraya bırakın veya bilgisayarınızdan seçin." in body:
            return None

        if isinstance(body, str) and body.strip() == "#### Belge özeti":
            return None

        if isinstance(body, str) and 'class="td-summary-grid"' in body:
            _streamlit_markdown(
                """
                <style>
                  div[data-testid="stElementContainer"]:has(.td-summary-grid) {
                    margin-top:-.8rem !important;
                  }

                  .td-summary-grid {
                    margin-top:0 !important;
                    margin-bottom:.55rem !important;
                  }

                  div[data-testid="stButton"] > button[kind="primary"] {
                    margin-top:.85rem !important;
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )

        return _streamlit_markdown(body, *args, **kwargs)

    _turkdet_markdown._turkdet_markdown = True
    st.markdown = _turkdet_markdown


# Remove the native hover tooltip from TürkDet's icon-only theme switch.
if not getattr(st.button, "_turkdet_button", False):
    _streamlit_button = st.button

    def _turkdet_button(label, *args, **kwargs):
        if kwargs.get("key") == "theme_toggle":
            kwargs["help"] = None
        return _streamlit_button(label, *args, **kwargs)

    _turkdet_button._turkdet_button = True
    st.button = _turkdet_button


# TürkDet's main pasted-text field must update while the user types. Streamlit's
# native multiline text_area only commits on blur/Ctrl+Enter, so route this one
# widget through a small bidirectional component. Other text areas stay native.
if not getattr(st.text_area, "_turkdet_live_text_area", False):
    _streamlit_text_area = st.text_area

    def _turkdet_text_area(label, *args, **kwargs):
        key = kwargs.get("key")
        if key != "pasted_text_widget":
            return _streamlit_text_area(label, *args, **kwargs)

        is_dark = st.session_state.get("theme_mode", "dark") == "dark"
        if is_dark:
            field_color = "#101826"
            text_color = "#F4F7FB"
            muted_color = "#97A3B6"
            border_color = "rgba(255,255,255,.16)"
            shadow = "0 8px 24px rgba(0,0,0,.14)"
        else:
            field_color = "#FFFFFF"
            text_color = "#111827"
            muted_color = "#667085"
            border_color = "rgba(15,23,42,.15)"
            shadow = "0 8px 22px rgba(15,23,42,.055)"

        current_value = st.session_state.get(
            key,
            st.session_state.get("pasted_text_buffer", ""),
        )
        return live_textarea(
            value=str(current_value or ""),
            placeholder=str(kwargs.get("placeholder") or ""),
            height=int(kwargs.get("height") or 300),
            debounce_ms=180,
            field_color=field_color,
            text_color=text_color,
            muted_color=muted_color,
            border_color=border_color,
            shadow=shadow,
            key=key,
        )

    _turkdet_text_area._turkdet_live_text_area = True
    st.text_area = _turkdet_text_area


# Streamlit's segmented-control internals inherit colors from the configured
# base theme. TürkDet changes theme at runtime, so style the source selector
# through its stable widget key instead of Streamlit's internal test IDs.
if hasattr(st, "segmented_control") and not getattr(st.segmented_control, "_turkdet_themed", False):
    _streamlit_segmented_control = st.segmented_control

    def _turkdet_segmented_control(*args, **kwargs):
        selected = _streamlit_segmented_control(*args, **kwargs)

        if kwargs.get("key") != "input_mode":
            return selected

        is_dark = st.session_state.get("theme_mode", "dark") == "dark"
        first_selected = selected != "Belge yükle"

        if is_dark:
            track = "#0F1622"
            inactive_bg = "#0F1622"
            inactive_text = "#97A3B6"
            hover_bg = "#151D2A"
            selected_bg = "#171B4A"
            selected_text = "#F4F7FB"
            border = "rgba(255,255,255,.12)"
            selected_border = "rgba(99,102,241,.78)"
        else:
            track = "#EEF1F7"
            inactive_bg = "#EEF1F7"
            inactive_text = "#667085"
            hover_bg = "#E7EAF2"
            selected_bg = "#FFFFFF"
            selected_text = "#111827"
            border = "rgba(15,23,42,.12)"
            selected_border = "rgba(99,102,241,.72)"

        first_bg = selected_bg if first_selected else inactive_bg
        first_text = selected_text if first_selected else inactive_text
        first_border = selected_border if first_selected else "transparent"
        first_hover_bg = first_bg if first_selected else hover_bg
        first_hover_text = first_text if first_selected else selected_text

        second_bg = inactive_bg if first_selected else selected_bg
        second_text = inactive_text if first_selected else selected_text
        second_border = "transparent" if first_selected else selected_border
        second_hover_bg = hover_bg if first_selected else second_bg
        second_hover_text = selected_text if first_selected else second_text

        st.markdown(
            f"""
            <style>
              div[class*="st-key-input_mode"] div[role="group"] {{
                background:{track} !important;
                background-color:{track} !important;
                border:1px solid {border} !important;
                border-radius:12px !important;
                overflow:hidden !important;
              }}

              div[class*="st-key-input_mode"] button {{
                background-image:none !important;
                box-shadow:none !important;
                outline:none !important;
                transition:background-color .15s ease,color .15s ease,border-color .15s ease !important;
              }}

              div[class*="st-key-input_mode"] button:first-of-type,
              div[class*="st-key-input_mode"] button:first-of-type:focus,
              div[class*="st-key-input_mode"] button:first-of-type:active {{
                background:{first_bg} !important;
                background-color:{first_bg} !important;
                color:{first_text} !important;
                -webkit-text-fill-color:{first_text} !important;
                border:1px solid {first_border} !important;
              }}

              div[class*="st-key-input_mode"] button:last-of-type,
              div[class*="st-key-input_mode"] button:last-of-type:focus,
              div[class*="st-key-input_mode"] button:last-of-type:active {{
                background:{second_bg} !important;
                background-color:{second_bg} !important;
                color:{second_text} !important;
                -webkit-text-fill-color:{second_text} !important;
                border:1px solid {second_border} !important;
              }}

              div[class*="st-key-input_mode"] button:first-of-type:hover {{
                background:{first_hover_bg} !important;
                background-color:{first_hover_bg} !important;
                color:{first_hover_text} !important;
                -webkit-text-fill-color:{first_hover_text} !important;
              }}

              div[class*="st-key-input_mode"] button:last-of-type:hover {{
                background:{second_hover_bg} !important;
                background-color:{second_hover_bg} !important;
                color:{second_hover_text} !important;
                -webkit-text-fill-color:{second_hover_text} !important;
              }}

              div[class*="st-key-input_mode"] button > div,
              div[class*="st-key-input_mode"] button div,
              div[class*="st-key-input_mode"] button p,
              div[class*="st-key-input_mode"] button span {{
                background:transparent !important;
                background-color:transparent !important;
                color:inherit !important;
                -webkit-text-fill-color:inherit !important;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        return selected

    _turkdet_segmented_control._turkdet_themed = True
    st.segmented_control = _turkdet_segmented_control


# Refine TürkDet's native Streamlit uploader into a compact, premium dropzone.
# The visual hierarchy follows the standard product pattern: icon, instruction,
# file constraints, then a clear browse action. The native upload behavior stays
# intact; only this keyed uploader receives the presentation layer below.
if not getattr(st.file_uploader, "_turkdet_premium_uploader", False):
    _streamlit_file_uploader = st.file_uploader

    def _turkdet_file_uploader(label, *args, **kwargs):
        uploaded = _streamlit_file_uploader(label, *args, **kwargs)

        if kwargs.get("key") == "uploaded_document":
            is_dark = st.session_state.get("theme_mode", "dark") == "dark"
            if is_dark:
                drop_bg = "#111824"
                drop_hover = "#141C2A"
                drop_border = "rgba(99,102,241,.40)"
                drop_border_hover = "rgba(99,102,241,.68)"
                icon_bg = "rgba(99,102,241,.12)"
                icon_border = "rgba(99,102,241,.30)"
                title_color = "#F4F7FB"
                meta_color = "#97A3B6"
                button_bg = "rgba(99,102,241,.12)"
                button_hover = "rgba(99,102,241,.18)"
            else:
                drop_bg = "#FFFFFF"
                drop_hover = "#FAFBFF"
                drop_border = "rgba(99,102,241,.30)"
                drop_border_hover = "rgba(99,102,241,.58)"
                icon_bg = "rgba(99,102,241,.07)"
                icon_border = "rgba(99,102,241,.20)"
                title_color = "#111827"
                meta_color = "#667085"
                button_bg = "rgba(99,102,241,.07)"
                button_hover = "rgba(99,102,241,.12)"

            st.markdown(
                f"""
                <style>
                  div[class*="st-key-uploaded_document"] [data-testid="stFileUploaderDropzone"],
                  div[class*="st-key-uploaded_document"] section {{
                    min-height:156px !important;
                    position:relative !important;
                    display:flex !important;
                    flex-direction:column !important;
                    align-items:center !important;
                    justify-content:center !important;
                    gap:.48rem !important;
                    padding:1.05rem 1.25rem !important;
                    text-align:center !important;
                    background:{drop_bg} !important;
                    border:1px dashed {drop_border} !important;
                    border-radius:16px !important;
                    box-shadow:0 10px 28px rgba(15,23,42,.055) !important;
                    transition:background .16s ease,border-color .16s ease,box-shadow .16s ease !important;
                  }}

                  div[class*="st-key-uploaded_document"] [data-testid="stFileUploaderDropzone"]:hover,
                  div[class*="st-key-uploaded_document"] section:hover {{
                    background:{drop_hover} !important;
                    border-color:{drop_border_hover} !important;
                    box-shadow:0 12px 30px rgba(99,102,241,.075) !important;
                  }}

                  div[class*="st-key-uploaded_document"] section > * {{
                    order:4;
                  }}

                  div[class*="st-key-uploaded_document"] section::before {{
                    content:"";
                    order:1;
                    width:40px;
                    height:40px;
                    flex:0 0 40px;
                    border-radius:12px;
                    border:1px solid {icon_border};
                    background-color:{icon_bg};
                    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='21' height='21' viewBox='0 0 24 24' fill='none' stroke='%236366F1' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V4'/%3E%3Cpath d='m7 9 5-5 5 5'/%3E%3Cpath d='M20 15v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4'/%3E%3C/svg%3E");
                    background-repeat:no-repeat;
                    background-position:center;
                    box-shadow:0 6px 16px rgba(99,102,241,.08);
                  }}

                  div[class*="st-key-uploaded_document"] div[data-testid="stFileUploaderDropzoneInstructions"] {{
                    order:2 !important;
                    width:100% !important;
                    display:flex !important;
                    flex-direction:column !important;
                    align-items:center !important;
                    justify-content:center !important;
                    gap:.2rem !important;
                    margin:0 !important;
                    padding:0 !important;
                    text-align:center !important;
                  }}

                  div[class*="st-key-uploaded_document"] div[data-testid="stFileUploaderDropzoneInstructions"] > div,
                  div[class*="st-key-uploaded_document"] div[data-testid="stFileUploaderDropzoneInstructions"] > svg {{
                    display:none !important;
                  }}

                  div[class*="st-key-uploaded_document"] div[data-testid="stFileUploaderDropzoneInstructions"]::before {{
                    content:"Belgenizi buraya sürükleyin" !important;
                    display:block !important;
                    width:100% !important;
                    color:{title_color} !important;
                    font-size:.88rem !important;
                    font-weight:720 !important;
                    line-height:1.3 !important;
                    text-align:center !important;
                  }}

                  div[class*="st-key-uploaded_document"] div[data-testid="stFileUploaderDropzoneInstructions"]::after {{
                    content:"TXT, DOCX veya PDF • En fazla 10 MB" !important;
                    display:block !important;
                    width:100% !important;
                    color:{meta_color} !important;
                    font-size:.73rem !important;
                    font-weight:450 !important;
                    line-height:1.35 !important;
                    text-align:center !important;
                  }}

                  div[class*="st-key-uploaded_document"] section > button,
                  div[class*="st-key-uploaded_document"] section > div:has(> button),
                  div[class*="st-key-uploaded_document"] section > div:has(button[kind="secondary"]) {{
                    order:3 !important;
                    margin:.18rem auto 0 !important;
                  }}

                  div[class*="st-key-uploaded_document"] section button {{
                    position:relative !important;
                    width:118px !important;
                    min-width:118px !important;
                    min-height:38px !important;
                    padding:0 !important;
                    border-radius:10px !important;
                    border:1px solid rgba(99,102,241,.46) !important;
                    background:{button_bg} !important;
                    color:transparent !important;
                    box-shadow:none !important;
                    transition:background .15s ease,border-color .15s ease,transform .15s ease !important;
                  }}

                  div[class*="st-key-uploaded_document"] section button > * {{
                    opacity:0 !important;
                  }}

                  div[class*="st-key-uploaded_document"] section button::after {{
                    content:"Belge seç" !important;
                    position:absolute !important;
                    inset:0 !important;
                    display:flex !important;
                    align-items:center !important;
                    justify-content:center !important;
                    color:#6366F1 !important;
                    font-size:.81rem !important;
                    font-weight:760 !important;
                  }}

                  div[class*="st-key-uploaded_document"] section button:hover {{
                    background:{button_hover} !important;
                    border-color:#6366F1 !important;
                    transform:translateY(-1px) !important;
                  }}
                </style>
                """,
                unsafe_allow_html=True,
            )

        return uploaded

    _turkdet_file_uploader._turkdet_premium_uploader = True
    st.file_uploader = _turkdet_file_uploader
