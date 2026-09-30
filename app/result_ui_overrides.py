"""Small result-screen refinements for the TürkDet Streamlit UI."""

from __future__ import annotations

from html import escape
import re

import streamlit as st
import streamlit.components.v1 as components

from app import report_pdf


_TECHNICAL_MODEL_MARKERS = (
    "TURKDET_MODEL_PATH",
    "Üretim modeli henüz web uygulamasına bağlanmadı",
    "Model artifact mevcut",
)


def _install_streamlit_result_overrides() -> None:
    if getattr(st.markdown, "_turkdet_result_polish", False):
        return

    native_markdown = st.markdown
    native_caption = st.caption
    native_warning = st.warning

    def polished_markdown(body, *args, **kwargs):
        if isinstance(body, str):
            stripped = body.strip()

            if stripped == "## TürkDet Analiz Raporu":
                file_name = str(st.session_state.get("uploaded_name_buffer", "") or "")
                file_chip = ""
                if file_name:
                    file_chip = f"""
                    <div class="td-report-file-chip" title="{escape(file_name)}">
                      <span class="td-report-file-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                          <path d="M14 2v6h6"></path>
                          <path d="M8 13h8"></path>
                          <path d="M8 17h5"></path>
                        </svg>
                      </span>
                      <span class="td-report-file-name">{escape(file_name)}</span>
                    </div>
                    """

                result = native_markdown(
                    f"""
                    <style>
                      .td-report-head {{
                        margin:.15rem 0 1.25rem;
                      }}
                      .td-report-kicker {{
                        display:inline-flex;
                        align-items:center;
                        gap:.42rem;
                        margin-bottom:.42rem;
                        color:#6366F1;
                        font-size:.68rem;
                        font-weight:800;
                        letter-spacing:.12em;
                        text-transform:uppercase;
                      }}
                      .td-report-kicker::before {{
                        content:"";
                        width:6px;
                        height:6px;
                        border-radius:999px;
                        background:#6366F1;
                        box-shadow:0 0 0 4px rgba(99,102,241,.10);
                      }}
                      .td-report-title {{
                        margin:0 0 .78rem;
                        font-size:2rem;
                        line-height:1.12;
                        font-weight:820;
                        letter-spacing:-.04em;
                      }}
                      .td-report-file-chip {{
                        width:fit-content;
                        max-width:min(100%,520px);
                        display:flex;
                        align-items:center;
                        gap:.62rem;
                        min-height:42px;
                        padding:.45rem .7rem;
                        border:1px solid rgba(99,102,241,.22);
                        border-radius:11px;
                        background:rgba(99,102,241,.055);
                      }}
                      .td-report-file-icon {{
                        width:28px;
                        height:28px;
                        flex:0 0 28px;
                        display:grid;
                        place-items:center;
                        border-radius:8px;
                        background:rgba(99,102,241,.10);
                        color:#6366F1;
                      }}
                      .td-report-file-icon svg {{ width:15px; height:15px; }}
                      .td-report-file-name {{
                        min-width:0;
                        overflow:hidden;
                        text-overflow:ellipsis;
                        white-space:nowrap;
                        font-size:.82rem;
                        font-weight:700;
                      }}
                    </style>
                    <div id="turkdet-analysis-report" class="td-report-head">
                      <div class="td-report-kicker">Analiz sonucu</div>
                      <div class="td-report-title">TürkDet Analiz Raporu</div>
                      {file_chip}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                components.html(
                    """
                    <script>
                      window.setTimeout(() => {
                        const node = window.parent.document.getElementById("turkdet-analysis-report");
                        if (node) node.scrollIntoView({ behavior: "smooth", block: "start" });
                      }, 120);
                    </script>
                    """,
                    height=0,
                )
                return result

            if stripped in {'<div class="td-doc">', "</div>"}:
                return None

            if "td-paragraph-head" in body and "AI SKORU" in body:
                body = re.sub(
                    r'\s*<div class="td-paragraph-head">.*?</div>\s*',
                    "",
                    body,
                    flags=re.DOTALL,
                )

            if "Model bağlantısı bekleniyor" in body:
                body = body.replace("Model bağlantısı bekleniyor", "Analiz sonucu kullanılamıyor")

        return native_markdown(body, *args, **kwargs)

    def polished_caption(body, *args, **kwargs):
        if isinstance(body, str):
            text = body.strip()
            if text.startswith("Belge:"):
                return None
            if "Paragraf skorları, segment düzeyindeki doğrulama tamamlandığında" in text:
                return None
            if "TürkDet, gerçek model bağlı değilken yüzde veya karar üretmez" in text:
                return None
        return native_caption(body, *args, **kwargs)

    def polished_warning(body, *args, **kwargs):
        if isinstance(body, str) and any(marker in body for marker in _TECHNICAL_MODEL_MARKERS):
            return None
        return native_warning(body, *args, **kwargs)

    polished_markdown._turkdet_result_polish = True
    st.markdown = polished_markdown
    st.caption = polished_caption
    st.warning = polished_warning


def _install_pdf_copy_overrides() -> None:
    if getattr(report_pdf, "_turkdet_copy_polish", False):
        return

    native_paragraph = report_pdf.Paragraph
    native_builder = report_pdf.build_analysis_report

    def clean_paragraph(text, *args, **kwargs):
        if isinstance(text, str):
            text = text.replace(
                " SHA-256 değeri analiz edilen girdiyi tanımlar; bu PDF henüz kriptografik olarak dijital imzalanmış değildir.",
                "",
            )
            text = text.replace(
                "Aşağıdaki içerik analiz sırasında kullanılan metnin rapor görünümüdür. Segment düzeyi skorları ayrıca doğrulanmadan gösterilmez.",
                "Analiz sırasında kullanılan metin aşağıda yer alır.",
            )
        return native_paragraph(text, *args, **kwargs)

    def clean_builder(*args, **kwargs):
        if kwargs.get("model_available") is False:
            kwargs["status_note"] = None
            kwargs["result_message"] = "Analiz sonucu üretilemedi"
        return native_builder(*args, **kwargs)

    report_pdf.Paragraph = clean_paragraph
    report_pdf.build_analysis_report = clean_builder
    report_pdf._turkdet_copy_polish = True


_install_streamlit_result_overrides()
_install_pdf_copy_overrides()
