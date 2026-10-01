"""Small, stable spacing refinements for the TürkDet result view."""

from __future__ import annotations

import streamlit as st


def install_result_layout_spacing() -> None:
    """Tighten the report rhythm without changing analysis behavior."""

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

    if not getattr(st.caption, "_turkdet_result_spacing", False):
        native_caption = st.caption
        native_markdown_for_caption = st.markdown

        def polished_caption(body, *args, **kwargs):
            if isinstance(body, str) and body.strip().startswith("İlk 30 paragraf gösteriliyor."):
                text = body.strip()
                return native_markdown_for_caption(
                    f'<div class="td-preview-meta">{text}</div>',
                    unsafe_allow_html=True,
                )
            return native_caption(body, *args, **kwargs)

        polished_caption._turkdet_result_spacing = True
        st.caption = polished_caption

    if getattr(st.markdown, "_turkdet_result_spacing", False):
        return

    native_markdown = st.markdown

    def polished_markdown(body, *args, **kwargs):
        # The report already has a strong visual header. The native markdown
        # divider created a large empty band between the analyze action and the
        # report, so omit only this standalone divider.
        if isinstance(body, str) and body.strip() == "---":
            return None

        result = native_markdown(body, *args, **kwargs)

        if isinstance(body, str) and body.strip() == "## TürkDet Analiz Raporu":
            native_markdown(
                """
                <style>
                  /* Keep the report title, file chip and columns as one compact block. */
                  .td-report-head {
                    margin-top:.05rem !important;
                    margin-bottom:.18rem !important;
                  }

                  div[data-testid="stElementContainer"]:has(#turkdet-analysis-report) {
                    margin-top:0 !important;
                    margin-bottom:-.62rem !important;
                  }

                  /* Column headings should visually belong to the cards below. */
                  div[data-testid="stHorizontalBlock"]:has(.td-document-paper) {
                    column-gap:2rem !important;
                    align-items:flex-start !important;
                    margin-top:0 !important;
                  }

                  div[data-testid="stHorizontalBlock"]:has(.td-document-paper) h3 {
                    margin-top:0 !important;
                    margin-bottom:.38rem !important;
                    line-height:1.16 !important;
                  }

                  div[data-testid="stElementContainer"]:has(.td-document-paper),
                  div[data-testid="stElementContainer"]:has(.td-score-card) {
                    margin-top:0 !important;
                  }

                  .td-document-paper,
                  .td-score-card {
                    margin-top:0 !important;
                  }

                  /* Right-side stack: result card -> report action -> report number. */
                  .td-score-card {
                    margin-bottom:0 !important;
                  }

                  .stApp div[data-testid="stDownloadButton"] {
                    margin-top:.62rem !important;
                    margin-bottom:.34rem !important;
                  }

                  div[data-testid="stElementContainer"]:has(.td-report-id) {
                    margin-top:-.12rem !important;
                  }

                  .td-report-id {
                    min-height:36px !important;
                    padding:.4rem .58rem !important;
                  }

                  /* The preview-limit note should read as a footer, not a new section. */
                  .td-preview-meta {
                    margin:.34rem 0 0 !important;
                    color:#8F99AA;
                    font-size:.72rem;
                    line-height:1.35;
                    font-weight:560;
                  }

                  div[data-testid="stElementContainer"]:has(.td-preview-meta) {
                    margin-top:-.18rem !important;
                  }

                  @media (max-width:700px) {
                    div[data-testid="stHorizontalBlock"]:has(.td-document-paper) {
                      column-gap:1rem !important;
                    }
                    .td-report-head {
                      margin-bottom:.4rem !important;
                    }
                    div[data-testid="stElementContainer"]:has(#turkdet-analysis-report) {
                      margin-bottom:-.25rem !important;
                    }
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )

        return result

    polished_markdown._turkdet_result_spacing = True
    st.markdown = polished_markdown
