"""TürkDet web application package."""

from __future__ import annotations

import streamlit as st


# Streamlit's segmented-control internals inherit parts of the configured base
# theme. TürkDet switches themes at runtime, so we restyle the two source
# segments from the widget's actual selected value instead of relying on
# Streamlit's native light/dark state selectors.
if hasattr(st, "segmented_control") and not getattr(st.segmented_control, "_turkdet_themed", False):
    _streamlit_segmented_control = st.segmented_control

    def _turkdet_segmented_control(*args, **kwargs):
        selected = _streamlit_segmented_control(*args, **kwargs)

        is_dark = st.session_state.get("theme_mode", "dark") == "dark"
        first_selected = selected != "Belge yükle"

        if is_dark:
            track = "#0F1622"
            inactive_bg = "transparent"
            inactive_text = "#97A3B6"
            hover_bg = "rgba(255,255,255,.055)"
            selected_bg = "rgba(99,102,241,.18)"
            selected_text = "#F4F7FB"
            border = "rgba(255,255,255,.105)"
            selected_border = "rgba(99,102,241,.52)"
        else:
            track = "#EEF1F7"
            inactive_bg = "transparent"
            inactive_text = "#667085"
            hover_bg = "rgba(15,23,42,.045)"
            selected_bg = "#FFFFFF"
            selected_text = "#111827"
            border = "rgba(15,23,42,.105)"
            selected_border = "rgba(99,102,241,.48)"

        first_bg = selected_bg if first_selected else inactive_bg
        first_text = selected_text if first_selected else inactive_text
        first_border = selected_border if first_selected else "transparent"
        second_bg = inactive_bg if first_selected else selected_bg
        second_text = inactive_text if first_selected else selected_text
        second_border = "transparent" if first_selected else selected_border

        st.markdown(
            f"""
            <style>
              div[data-testid="stSegmentedControl"] div[role="group"] {{
                background:{track} !important;
                border:1px solid {border} !important;
              }}

              div[data-testid="stSegmentedControl"] button,
              div[data-testid="stSegmentedControl"] button:hover,
              div[data-testid="stSegmentedControl"] button:focus,
              div[data-testid="stSegmentedControl"] button:active {{
                box-shadow:none !important;
                outline:none !important;
              }}

              div[data-testid="stSegmentedControl"] button:first-of-type {{
                background:{first_bg} !important;
                color:{first_text} !important;
                border:1px solid {first_border} !important;
              }}
              div[data-testid="stSegmentedControl"] button:last-of-type {{
                background:{second_bg} !important;
                color:{second_text} !important;
                border:1px solid {second_border} !important;
              }}

              div[data-testid="stSegmentedControl"] button:first-of-type *,
              div[data-testid="stSegmentedControl"] button:last-of-type * {{
                background:transparent !important;
                color:inherit !important;
              }}

              div[data-testid="stSegmentedControl"] button:first-of-type:hover {{
                background:{first_bg if first_selected else hover_bg} !important;
                color:{selected_text if not first_selected else first_text} !important;
              }}
              div[data-testid="stSegmentedControl"] button:last-of-type:hover {{
                background:{hover_bg if first_selected else second_bg} !important;
                color:{selected_text if first_selected else second_text} !important;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        return selected

    _turkdet_segmented_control._turkdet_themed = True
    st.segmented_control = _turkdet_segmented_control
