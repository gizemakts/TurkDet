"""TürkDet web application package."""

from __future__ import annotations

import streamlit as st


# Remove the native hover tooltip from TürkDet's icon-only theme switch.
if not getattr(st.button, "_turkdet_button", False):
    _streamlit_button = st.button

    def _turkdet_button(label, *args, **kwargs):
        if kwargs.get("key") == "theme_toggle":
            kwargs["help"] = None
        return _streamlit_button(label, *args, **kwargs)

    _turkdet_button._turkdet_button = True
    st.button = _turkdet_button


# Hide Streamlit's native Ctrl+Enter instruction and resize affordance from
# TürkDet's main text input. Streamlit 1.64 can execute trusted JavaScript via
# st.html directly in the app DOM, so the lightweight document counters can be
# updated on each browser input event without rerunning detector inference.
if not getattr(st.text_area, "_turkdet_text_area", False):
    _streamlit_text_area = st.text_area

    def _turkdet_text_area(*args, **kwargs):
        value = _streamlit_text_area(*args, **kwargs)

        if kwargs.get("key") == "pasted_text_widget":
            st.markdown(
                """
                <style>
                  div[data-testid="stTextArea"] [data-testid="InputInstructions"],
                  div[data-testid="stTextArea"] small {
                    display:none !important;
                    visibility:hidden !important;
                  }

                  div[data-testid="stTextArea"] textarea {
                    resize:none !important;
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )

            st.html(
                """
                <script>
                (() => {
                  let attachedTextarea = null;

                  const setStat = (id, value) => {
                    const node = document.getElementById(id);
                    if (node) node.textContent = Number(value).toLocaleString('tr-TR');
                  };

                  const computeStats = (rawValue) => {
                    const cleaned = (rawValue || '').trim();
                    if (!cleaned) {
                      return { words: 0, paragraphs: 0, sentences: 0, characters: 0 };
                    }

                    const words = (cleaned.match(/\S+/gu) || []).length;
                    const normalized = cleaned.replace(/\r\n?/g, '\n');
                    const paragraphs = normalized
                      .split(/\n\s*\n+/u)
                      .map((block) => block
                        .split('\n')
                        .map((line) => line.trim())
                        .filter(Boolean)
                        .join(' '))
                      .filter(Boolean).length;

                    const sentenceMarks = cleaned.match(/[.!?…]+(?=\s|$)/gu) || [];
                    const sentences = sentenceMarks.length || 1;
                    const characters = [...cleaned].length;

                    return { words, paragraphs, sentences, characters };
                  };

                  const updateSummary = () => {
                    const textarea = document.querySelector(
                      'div[class*="st-key-pasted_text_widget"] textarea, div[data-testid="stTextArea"] textarea'
                    );
                    if (!textarea) return;

                    const stats = computeStats(textarea.value);
                    setStat('td-stat-words', stats.words);
                    setStat('td-stat-paragraphs', stats.paragraphs);
                    setStat('td-stat-sentences', stats.sentences);
                    setStat('td-stat-characters', stats.characters);
                  };

                  const attach = () => {
                    const textarea = document.querySelector(
                      'div[class*="st-key-pasted_text_widget"] textarea, div[data-testid="stTextArea"] textarea'
                    );
                    if (!textarea) return;

                    if (textarea !== attachedTextarea) {
                      if (attachedTextarea) {
                        attachedTextarea.removeEventListener('input', updateSummary);
                      }
                      attachedTextarea = textarea;
                      textarea.addEventListener('input', updateSummary, { passive: true });
                    }
                    updateSummary();
                  };

                  attach();
                  const observer = new MutationObserver(attach);
                  observer.observe(document.body, { childList: true, subtree: true });
                })();
                </script>
                """,
                unsafe_allow_javascript=True,
            )

        return value

    _turkdet_text_area._turkdet_text_area = True
    st.text_area = _turkdet_text_area


# Streamlit's segmented-control internals inherit colors from the configured
# base theme. TürkDet changes theme at runtime, so style the source selector
# through its stable widget key instead of Streamlit's internal test IDs.
if hasattr(st, "segmented_control") and not getattr(st.segmented_control, "_turkdet_themed", False):
    _streamlit_segmented_control = st.segmented_control

    def _turkdet_segmented_control(*args, **kwargs):
        selected = _streamlit_segmented_control(*args, **kwargs)

        key = kwargs.get("key")
        if key != "input_mode":
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
