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
    "Doğrulanmış üretim modeli henüz web uygulamasına bağlanmadı",
    "Model artifact mevcut",
)


def _install_streamlit_result_overrides() -> None:
    if getattr(st.markdown, "_turkdet_result_polish", False):
        return

    native_markdown = st.markdown
    native_caption = st.caption
    native_warning = st.warning
    native_info = st.info

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

                      /* Give the report action enough breathing room without loosening the whole panel. */
                      .stApp div[data-testid="stDownloadButton"] {{
                        margin-top:.78rem !important;
                        margin-bottom:.32rem !important;
                      }}

                      /* PDF report action: intentionally independent from model availability. */
                      .stApp div[data-testid="stDownloadButton"] button,
                      .stApp div[data-testid="stDownloadButton"] a,
                      .stApp div[data-testid="stDownloadButton"] [role="button"] {{
                        width:100% !important;
                        min-height:46px !important;
                        border-radius:12px !important;
                        border:1px solid transparent !important;
                        background:#6366F1 !important;
                        background-image:linear-gradient(135deg,#6366F1,#7377F5) !important;
                        color:#FFFFFF !important;
                        font-weight:780 !important;
                        opacity:1 !important;
                        box-shadow:0 10px 24px rgba(99,102,241,.22) !important;
                        transition:transform .12s ease,filter .12s ease,box-shadow .12s ease !important;
                      }}
                      .stApp div[data-testid="stDownloadButton"] button:hover,
                      .stApp div[data-testid="stDownloadButton"] a:hover,
                      .stApp div[data-testid="stDownloadButton"] [role="button"]:hover {{
                        filter:brightness(1.045) !important;
                        transform:translateY(-1px) !important;
                        box-shadow:0 13px 28px rgba(99,102,241,.26) !important;
                      }}
                      .stApp div[data-testid="stDownloadButton"] button *,
                      .stApp div[data-testid="stDownloadButton"] a *,
                      .stApp div[data-testid="stDownloadButton"] [role="button"] * {{
                        color:#FFFFFF !important;
                        fill:currentColor !important;
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
                      (() => {
                        const hostWindow = window.parent;
                        const doc = hostWindow.document;
                        const report = doc.getElementById("turkdet-analysis-report");

                        window.setTimeout(() => {
                          if (report) report.scrollIntoView({ behavior: "smooth", block: "start" });
                        }, 120);

                        let button = doc.getElementById("turkdet-back-to-top");
                        if (!button) {
                          button = doc.createElement("button");
                          button.id = "turkdet-back-to-top";
                          button.type = "button";
                          button.setAttribute("aria-label", "Yukarı dön");
                          button.setAttribute("title", "Yukarı dön");
                          button.innerHTML = `
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                              <path d="m6 15 6-6 6 6"></path>
                            </svg>`;

                          Object.assign(button.style, {
                            position: "fixed",
                            right: "24px",
                            bottom: "24px",
                            width: "42px",
                            height: "42px",
                            display: "grid",
                            placeItems: "center",
                            padding: "0",
                            borderRadius: "12px",
                            border: "1px solid rgba(99,102,241,.34)",
                            background: "rgba(99,102,241,.16)",
                            color: "#818CF8",
                            boxShadow: "0 10px 30px rgba(15,23,42,.18)",
                            backdropFilter: "blur(12px)",
                            WebkitBackdropFilter: "blur(12px)",
                            cursor: "pointer",
                            zIndex: "999999",
                            opacity: "0",
                            pointerEvents: "none",
                            transform: "translateY(8px)",
                            transition: "opacity .18s ease, transform .18s ease, background .16s ease, border-color .16s ease"
                          });

                          button.addEventListener("mouseenter", () => {
                            button.style.background = "rgba(99,102,241,.24)";
                            button.style.borderColor = "rgba(99,102,241,.58)";
                          });
                          button.addEventListener("mouseleave", () => {
                            button.style.background = "rgba(99,102,241,.16)";
                            button.style.borderColor = "rgba(99,102,241,.34)";
                          });
                          button.addEventListener("click", () => {
                            hostWindow.scrollTo({ top: 0, behavior: "smooth" });
                            const scroller = doc.querySelector('[data-testid="stAppViewContainer"]');
                            if (scroller && typeof scroller.scrollTo === "function") {
                              scroller.scrollTo({ top: 0, behavior: "smooth" });
                            }
                          });
                          doc.body.appendChild(button);
                        }

                        const scroller = doc.querySelector('[data-testid="stAppViewContainer"]');
                        const currentOffset = () => Math.max(
                          hostWindow.scrollY || 0,
                          doc.documentElement ? doc.documentElement.scrollTop || 0 : 0,
                          doc.body ? doc.body.scrollTop || 0 : 0,
                          scroller ? scroller.scrollTop || 0 : 0
                        );
                        const syncButton = () => {
                          const visible = currentOffset() > 220;
                          button.style.opacity = visible ? "1" : "0";
                          button.style.pointerEvents = visible ? "auto" : "none";
                          button.style.transform = visible ? "translateY(0)" : "translateY(8px)";
                        };

                        hostWindow.addEventListener("scroll", syncButton, { passive: true });
                        if (scroller) scroller.addEventListener("scroll", syncButton, { passive: true });
                        window.setTimeout(syncButton, 260);
                      })();
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
                body = re.sub(
                    r'\s*<div class="td-center td-muted"[^>]*>Model bağlantısı bekleniyor</div>\s*',
                    "",
                    body,
                    flags=re.DOTALL,
                )

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
            if text.startswith("Rapor No:") and " · Girdi SHA-256:" in text:
                body = text.split(" · Girdi SHA-256:", 1)[0]
        return native_caption(body, *args, **kwargs)

    def polished_warning(body, *args, **kwargs):
        if isinstance(body, str) and any(marker in body for marker in _TECHNICAL_MODEL_MARKERS):
            return None
        return native_warning(body, *args, **kwargs)

    def polished_info(body, *args, **kwargs):
        if isinstance(body, str) and any(marker in body for marker in _TECHNICAL_MODEL_MARKERS):
            return None
        return native_info(body, *args, **kwargs)

    polished_markdown._turkdet_result_polish = True
    st.markdown = polished_markdown
    st.caption = polished_caption
    st.warning = polished_warning
    st.info = polished_info


def _install_pdf_copy_overrides() -> None:
    if getattr(report_pdf, "_turkdet_copy_polish", False):
        return

    native_paragraph = report_pdf.Paragraph
    native_table = report_pdf.Table
    native_builder = report_pdf.build_analysis_report
    suppress_next_table = {"value": False}

    class _HiddenBlock(report_pdf.Spacer):
        def __init__(self):
            super().__init__(1, 0)

        def setStyle(self, *_args, **_kwargs):
            return None

    def clean_paragraph(text, *args, **kwargs):
        if isinstance(text, str):
            if text.strip() == "Girdi doğrulama bilgisi":
                suppress_next_table["value"] = True
                return report_pdf.Spacer(1, 0)
            text = text.replace(
                " SHA-256 değeri analiz edilen girdiyi tanımlar; bu PDF henüz kriptografik olarak dijital imzalanmış değildir.",
                "",
            )
            text = text.replace(
                "Aşağıdaki içerik analiz sırasında kullanılan metnin rapor görünümüdür. Segment düzeyi skorları ayrıca doğrulanmadan gösterilmez.",
                "Analiz sırasında kullanılan metin aşağıda yer alır.",
            )
        return native_paragraph(text, *args, **kwargs)

    def clean_table(*args, **kwargs):
        if suppress_next_table["value"]:
            suppress_next_table["value"] = False
            return _HiddenBlock()
        return native_table(*args, **kwargs)

    def clean_builder(*args, **kwargs):
        if kwargs.get("model_available") is False:
            kwargs["status_note"] = None
            kwargs["result_message"] = "Analiz sonucu üretilemedi"
        return native_builder(*args, **kwargs)

    report_pdf.Paragraph = clean_paragraph
    report_pdf.Table = clean_table
    report_pdf.build_analysis_report = clean_builder
    report_pdf._turkdet_copy_polish = True


_install_streamlit_result_overrides()
_install_pdf_copy_overrides()
