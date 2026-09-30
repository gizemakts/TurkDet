"""Small, stable spacing refinements for the TürkDet result view."""

from __future__ import annotations

import streamlit as st


def install_result_layout_spacing() -> None:
    """Tighten the report rhythm without depending on fragile internal markup."""

    if not getattr(st.columns, "_turkdet_result_layout", False):
        native_columns = st.columns

        def polished_columns(spec, *args, **kwargs):
            adjusted = spec
            if isinstance(spec, (list, tuple)) and len(spec) == 2:
                try:
                    left = float(spec[0])
                    right = float(spec[1])
                except (TypeError, ValueError):
                    pass
                else:
                    if abs(left - 2.15) < 0.001 and abs(right - 1.0) < 0.001:
                        adjusted = [2.0, 1.08]
            return native_columns(adjusted, *args, **kwargs)

        polished_columns._turkdet_result_layout = True
        st.columns = polished_columns

    if getattr(st.markdown, "_turkdet_result_spacing", False):
        return

    native_markdown = st.markdown

    def polished_markdown(body, *args, **kwargs):
        result = native_markdown(body, *args, **kwargs)

        if isinstance(body, str) and body.strip() == "## TürkDet Analiz Raporu":
            native_markdown(
                """
                <style>
                  /* Bring the report header and two-column content into one visual group. */
                  .td-report-head {
                    margin-bottom:.48rem !important;
                  }

                  div[data-testid="stElementContainer"]:has(#turkdet-analysis-report) {
                    margin-bottom:-.18rem !important;
                  }

                  /* Column headings should belong to the surfaces directly below them. */
                  div[data-testid="stHorizontalBlock"] h3 {
                    margin-top:.05rem !important;
                    margin-bottom:.62rem !important;
                    line-height:1.18 !important;
                  }

                  /* Keep the preview/result pair comfortably separated, not disconnected. */
                  div[data-testid="stHorizontalBlock"]:has(.td-document-paper) {
                    column-gap:2.15rem !important;
                  }

                  /* A slightly calmer result stack: card -> action -> report metadata. */
                  .td-score-card {
                    margin-bottom:0 !important;
                  }

                  .stApp div[data-testid="stDownloadButton"] {
                    margin-top:.74rem !important;
                    margin-bottom:.38rem !important;
                  }

                  div[data-testid="stElementContainer"]:has(.td-report-id) {
                    margin-top:-.08rem !important;
                  }

                  .td-report-id {
                    min-height:36px !important;
                    padding:.42rem .58rem !important;
                  }

                  @media (max-width:700px) {
                    div[data-testid="stHorizontalBlock"]:has(.td-document-paper) {
                      column-gap:1rem !important;
                    }
                    .td-report-head {
                      margin-bottom:.65rem !important;
                    }
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )

        return result

    polished_markdown._turkdet_result_spacing = True
    st.markdown = polished_markdown
