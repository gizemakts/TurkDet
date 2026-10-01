"""Stable interaction fixes for TürkDet input/result widgets."""

from __future__ import annotations

import streamlit as st


def install_input_behavior_fixes() -> None:
    """Keep input mode sticky and normalize the public score label."""

    if hasattr(st, "segmented_control") and not getattr(
        st.segmented_control, "_turkdet_sticky_input_mode", False
    ):
        native_segmented_control = st.segmented_control

        def sticky_segmented_control(*args, **kwargs):
            key = kwargs.get("key")

            if key == "input_mode":
                last_valid = st.session_state.get(
                    "_turkdet_last_input_mode",
                    kwargs.get("default") or "Metin yapıştır",
                )

                # Streamlit's single-select segmented control can temporarily
                # become None when the already-selected item is clicked again.
                # Restore the last valid value before the widget is instantiated
                # on this rerun so both behavior and styling stay consistent.
                if (
                    key in st.session_state
                    and st.session_state.get(key) is None
                    and last_valid
                ):
                    st.session_state[key] = last_valid

            selected = native_segmented_control(*args, **kwargs)

            if key == "input_mode":
                valid_modes = {"Metin yapıştır", "Belge yükle"}
                if selected in valid_modes:
                    st.session_state["_turkdet_last_input_mode"] = selected
                else:
                    selected = st.session_state.get(
                        "_turkdet_last_input_mode", "Metin yapıştır"
                    )

            return selected

        sticky_segmented_control._turkdet_sticky_input_mode = True
        st.segmented_control = sticky_segmented_control

    if not getattr(st.markdown, "_turkdet_ai_score_label", False):
        native_markdown = st.markdown

        def score_label_markdown(body, *args, **kwargs):
            if isinstance(body, str) and "AI yazım skoru" in body:
                body = body.replace("AI yazım skoru", "AI Score")
            return native_markdown(body, *args, **kwargs)

        score_label_markdown._turkdet_ai_score_label = True
        st.markdown = score_label_markdown
