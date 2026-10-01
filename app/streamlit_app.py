"""TürkDet single-page Turkish AI text analysis interface."""

from __future__ import annotations

from html import escape

import streamlit as st

from app.document_parser import DocumentParseError, extract_text, get_document_stats, split_paragraphs
from app.inference import InferenceUnavailableError, predict_text
from app.report_pdf import build_analysis_report


MIN_WORDS = 30  # Temporary UI guard; not a validated scientific threshold.
ACCENT = "#6366F1"

st.set_page_config(
    page_title="TürkDet",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.session_state.setdefault("pasted_text_buffer", "")
st.session_state.setdefault("uploaded_text_buffer", "")
st.session_state.setdefault("uploaded_name_buffer", "")
st.session_state.setdefault("theme_mode", "dark")


def _sync_pasted_text() -> None:
    st.session_state["pasted_text_buffer"] = st.session_state.get("pasted_text_widget", "")


def _toggle_theme() -> None:
    st.session_state["theme_mode"] = "light" if st.session_state["theme_mode"] == "dark" else "dark"


def _safe_result_message(label: str) -> str:
    normalized = str(label).strip().upper().replace(" ", "_")
    if normalized in {"HUMAN", "İNSAN", "INSAN", "0"}:
        return "Belirgin yapay zekâ izi saptanmadı"
    if normalized in {"AI", "AI_GENERATED", "AI-GENERATED", "1"}:
        return "Yapay zekâ üretimiyle uyumlu sinyal saptandı"
    return "Model çıktısı hazır"


def _render_document(paragraphs: list[str], caption: str) -> None:
    st.markdown("### Belge görünümü")
    st.caption(caption)
    st.markdown('<div class="td-doc">', unsafe_allow_html=True)
    if paragraphs:
        for index, paragraph in enumerate(paragraphs[:30], start=1):
            safe_paragraph = escape(paragraph)
            st.markdown(
                f"""
                <div class="td-paragraph">
                  <div class="td-paragraph-head">PARAGRAF {index} · AI SKORU —</div>
                  <div>{safe_paragraph}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Belgede gösterilecek paragraf bulunamadı.")
    st.markdown("</div>", unsafe_allow_html=True)


def _report_source_bytes(uploaded_name: str) -> bytes | None:
    if not uploaded_name:
        return None
    for key in ("selected_document_data", "uploaded_data_buffer"):
        data = st.session_state.get(key, b"")
        if isinstance(data, (bytes, bytearray)) and data:
            return bytes(data)
    return None


def _render_report_download(
    *,
    text: str,
    uploaded_name: str,
    stats,
    result_message: str,
    ai_probability: float | None,
    model_available: bool,
    status_note: str | None = None,
) -> None:
    report = build_analysis_report(
        text=text,
        source_name=uploaded_name or "Yapıştırılan metin",
        source_bytes=_report_source_bytes(uploaded_name),
        words=stats.words,
        paragraphs=stats.paragraphs,
        sentences_approx=stats.sentences_approx,
        characters=stats.characters,
        result_message=result_message,
        ai_probability=ai_probability,
        model_available=model_available,
        status_note=status_note,
    )
    st.download_button(
        "PDF Raporunu İndir",
        data=report.pdf_bytes,
        file_name=report.file_name,
        mime="application/pdf",
        use_container_width=True,
        on_click="ignore",
        key=f"download_report_{report.report_id}",
    )
    st.caption(
        f"Rapor No: {report.report_id} · Girdi SHA-256: {report.input_sha256[:16]}…"
    )


is_dark = st.session_state["theme_mode"] == "dark"

if is_dark:
    BG = "#0B0F16"
    BG_SOFT = "#0E131C"
    SURFACE = "#121824"
    SURFACE_2 = "#151C29"
    FIELD = "#101826"
    TEXT = "#F4F7FB"
    MUTED = "#97A3B6"
    BORDER = "rgba(255,255,255,.105)"
    BORDER_STRONG = "rgba(255,255,255,.16)"
    SOFT = "rgba(255,255,255,.045)"
    SHADOW = "0 16px 42px rgba(0,0,0,.22)"
    SHADOW_SOFT = "0 8px 24px rgba(0,0,0,.14)"
    TOGGLE_TRACK = "linear-gradient(135deg,#18202E,#222C3E)"
    SEGMENT_TRACK = "#0F1622"
    SEGMENT_SELECTED = "rgba(99,102,241,.18)"
    SHORT_WARNING_BG = "rgba(245,158,11,.095)"
    SHORT_WARNING_BORDER = "rgba(245,158,11,.28)"
    SHORT_WARNING_TEXT = "#F6C85F"
    PAGE_GLOW = "radial-gradient(circle at 16% 0%, rgba(99,102,241,.075), transparent 28%)"
else:
    BG = "#F7F8FC"
    BG_SOFT = "#FBFCFE"
    SURFACE = "#FFFFFF"
    SURFACE_2 = "#F8FAFD"
    FIELD = "#FFFFFF"
    TEXT = "#111827"
    MUTED = "#667085"
    BORDER = "rgba(15,23,42,.105)"
    BORDER_STRONG = "rgba(15,23,42,.15)"
    SOFT = "rgba(15,23,42,.03)"
    SHADOW = "0 16px 42px rgba(15,23,42,.07)"
    SHADOW_SOFT = "0 8px 22px rgba(15,23,42,.055)"
    TOGGLE_TRACK = "linear-gradient(135deg,#E8EEFF,#F2F4FF)"
    SEGMENT_TRACK = "#EEF1F7"
    SEGMENT_SELECTED = "#FFFFFF"
    SHORT_WARNING_BG = "#FFFAEB"
    SHORT_WARNING_BORDER = "rgba(217,119,6,.24)"
    SHORT_WARNING_TEXT = "#92400E"
    PAGE_GLOW = "radial-gradient(circle at 16% 0%, rgba(99,102,241,.055), transparent 30%)"

SUN_ICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' "
    "viewBox='0 0 24 24' fill='none' stroke='%23F59E0B' stroke-width='2' stroke-linecap='round'%3E"
    "%3Ccircle cx='12' cy='12' r='4'/%3E%3Cpath d='M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41"
    "M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41'/%3E%3C/svg%3E"
)
MOON_ICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' "
    "viewBox='0 0 24 24' fill='none' stroke='%236366F1' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E"
    "%3Cpath d='M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z'/%3E%3C/svg%3E"
)

theme_thumb_offset = "32px" if is_dark else "0px"
theme_active_icon = MOON_ICON if is_dark else SUN_ICON
theme_passive_icon = SUN_ICON if is_dark else MOON_ICON
theme_passive_side = "left:9px;" if is_dark else "right:9px;"

st.markdown(
    f"""
    <style>
      header[data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stDecoration"],
      #MainMenu,
      footer {{
        display:none !important;
        visibility:hidden !important;
      }}

      html {{
        color-scheme:{'dark' if is_dark else 'light'};
      }}

      .stApp {{
        --background-color:{BG};
        --secondary-background-color:{SURFACE};
        --text-color:{TEXT};
        --primary-color:{ACCENT};
        background:{PAGE_GLOW}, linear-gradient(180deg,{BG_SOFT} 0%,{BG} 28%,{BG} 100%) !important;
        color:{TEXT} !important;
      }}
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"] {{
        background:transparent !important;
        color:{TEXT} !important;
      }}

      .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
      .stApp p, .stApp label,
      .stApp [data-testid="stMarkdownContainer"] {{
        color:{TEXT};
      }}
      .stApp [data-testid="stCaptionContainer"] {{
        color:{MUTED} !important;
      }}

      .block-container {{
        max-width:1120px;
        padding-top:1.55rem;
        padding-bottom:3.4rem;
      }}

      /* Header */
      .td-brand-wrap {{
        display:flex;
        align-items:center;
        gap:.82rem;
        padding:.2rem 0 .72rem;
      }}
      .td-mark {{
        width:44px;
        height:44px;
        border-radius:13px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight:850;
        font-size:1rem;
        letter-spacing:-.04em;
        border:1px solid {BORDER_STRONG};
        background:linear-gradient(145deg,rgba(99,102,241,.12),{SURFACE});
        box-shadow:{SHADOW_SOFT};
      }}
      .td-brand {{
        font-size:1.66rem;
        font-weight:840;
        letter-spacing:-.045em;
        line-height:1;
      }}
      .td-subtitle {{
        color:{MUTED};
        margin-top:.28rem;
        font-size:.82rem;
        letter-spacing:.005em;
      }}
      .td-header-rule {{
        height:1px;
        background:linear-gradient(90deg,{BORDER_STRONG},transparent 88%);
        margin:.22rem 0 1.7rem;
      }}

      /* Premium vector sun/moon theme switch */
      div[class*="st-key-theme_toggle"] {{
        display:flex;
        justify-content:flex-end;
        padding-top:.36rem;
      }}
      div[class*="st-key-theme_toggle"] button {{
        position:relative !important;
        width:64px !important;
        min-width:64px !important;
        height:32px !important;
        min-height:32px !important;
        padding:0 !important;
        overflow:hidden !important;
        border-radius:999px !important;
        border:1px solid {BORDER_STRONG} !important;
        background:{TOGGLE_TRACK} !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.06), 0 3px 12px rgba(0,0,0,.10) !important;
        transition:border-color .18s ease, box-shadow .18s ease, background .22s ease !important;
      }}
      div[class*="st-key-theme_toggle"] button:hover {{
        border-color:rgba(99,102,241,.58) !important;
        box-shadow:0 0 0 3px rgba(99,102,241,.09), 0 3px 12px rgba(0,0,0,.10) !important;
      }}
      div[class*="st-key-theme_toggle"] button::before {{
        content:"";
        position:absolute;
        top:50%;
        {theme_passive_side}
        width:14px;
        height:14px;
        transform:translateY(-50%);
        background-image:url("{theme_passive_icon}");
        background-size:14px 14px;
        background-repeat:no-repeat;
        background-position:center;
        opacity:.52;
        z-index:1;
      }}
      div[class*="st-key-theme_toggle"] button p {{
        position:absolute !important;
        top:2px !important;
        left:2px !important;
        z-index:2 !important;
        width:26px !important;
        height:26px !important;
        min-width:26px !important;
        margin:0 !important;
        padding:0 !important;
        border-radius:50% !important;
        display:block !important;
        overflow:hidden !important;
        color:transparent !important;
        font-size:0 !important;
        background:linear-gradient(180deg,#FFFFFF,#F8FAFC) !important;
        border:1px solid rgba(15,23,42,.07) !important;
        box-shadow:0 2px 7px rgba(0,0,0,.20), 0 1px 1px rgba(0,0,0,.08) !important;
        transform:translateX({theme_thumb_offset}) !important;
        transition:transform .24s cubic-bezier(.22,1,.36,1), box-shadow .18s ease !important;
      }}
      div[class*="st-key-theme_toggle"] button p::before {{
        content:"";
        position:absolute;
        inset:5px;
        background-image:url("{theme_active_icon}");
        background-size:16px 16px;
        background-repeat:no-repeat;
        background-position:center;
      }}

      /* Hero */
      .td-kicker {{
        display:inline-flex;
        align-items:center;
        gap:.45rem;
        font-size:.7rem;
        font-weight:800;
        letter-spacing:.12em;
        text-transform:uppercase;
        color:{ACCENT};
        margin-bottom:.5rem;
      }}
      .td-kicker::before {{
        content:"";
        width:6px;
        height:6px;
        border-radius:50%;
        background:{ACCENT};
        box-shadow:0 0 0 4px rgba(99,102,241,.10);
      }}
      .stApp h2 {{
        letter-spacing:-.034em;
        font-weight:820;
        margin-top:.16rem;
      }}
      .td-lead {{
        color:{MUTED};
        max-width:760px;
        margin:.1rem 0 1.35rem;
        line-height:1.65;
        font-size:.96rem;
      }}

      /* Input source selector */
      div[data-testid="stSegmentedControl"] {{
        margin-bottom:.72rem;
      }}
      div[data-testid="stSegmentedControl"] div[role="group"] {{
        width:fit-content !important;
        padding:3px !important;
        gap:2px !important;
        border:1px solid {BORDER} !important;
        border-radius:12px !important;
        background:{SEGMENT_TRACK} !important;
        box-shadow:inset 0 1px 1px rgba(0,0,0,.025) !important;
      }}
      div[data-testid="stSegmentedControl"] button {{
        min-height:34px !important;
        padding:.22rem .9rem !important;
        border:0 !important;
        border-radius:9px !important;
        background:transparent !important;
        color:{MUTED} !important;
        box-shadow:none !important;
        font-weight:700 !important;
        transition:background .16s ease,color .16s ease,box-shadow .16s ease !important;
      }}
      div[data-testid="stSegmentedControl"] button * {{
        background:transparent !important;
        color:inherit !important;
      }}
      div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {{
        background:{SEGMENT_SELECTED} !important;
        color:{TEXT} !important;
        box-shadow:0 1px 3px rgba(15,23,42,.10), inset 0 0 0 1px rgba(99,102,241,.34) !important;
      }}
      div[data-testid="stSegmentedControl"] button[aria-pressed="true"] * {{
        background:transparent !important;
        color:inherit !important;
      }}
      div[data-testid="stSegmentedControl"] button:hover:not([aria-pressed="true"]) {{
        color:{TEXT} !important;
        background:{SOFT} !important;
      }}

      /* Text area */
      div[data-testid="stTextArea"] {{
        margin-top:.15rem;
      }}
      div[data-testid="stTextArea"] > div,
      div[data-testid="stTextArea"] div[data-baseweb="base-input"],
      div[data-testid="stTextArea"] div[data-baseweb="textarea"] {{
        border:1px solid {BORDER_STRONG} !important;
        outline:0 !important;
        border-radius:16px !important;
        background:{FIELD} !important;
        box-shadow:{SHADOW_SOFT} !important;
        overflow:hidden !important;
        transition:border-color .17s ease,box-shadow .17s ease !important;
      }}
      div[data-testid="stTextArea"]:focus-within > div,
      div[data-testid="stTextArea"] div[data-baseweb="base-input"]:focus-within,
      div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {{
        border-color:rgba(99,102,241,.72) !important;
        box-shadow:0 0 0 3px rgba(99,102,241,.10),{SHADOW_SOFT} !important;
      }}
      div[data-testid="stTextArea"] textarea {{
        min-height:286px !important;
        padding:1rem 1.05rem !important;
        background:{FIELD} !important;
        color:{TEXT} !important;
        border:0 !important;
        outline:0 !important;
        box-shadow:none !important;
        -webkit-appearance:none !important;
        appearance:none !important;
        line-height:1.6 !important;
      }}
      div[data-testid="stTextArea"] textarea:focus {{
        border:0 !important;
        outline:0 !important;
        box-shadow:none !important;
      }}
      div[data-testid="stTextArea"] textarea::placeholder {{
        color:{MUTED} !important;
        opacity:.78;
      }}

      .td-help {{
        margin:.72rem 0 1.05rem;
        font-size:.8rem;
        color:{MUTED};
        line-height:1.55;
      }}

      /* Upload */
      .td-upload-copy {{
        margin:.08rem 0 .7rem;
        font-size:.83rem;
        color:{MUTED};
      }}
      div[data-testid="stFileUploader"] section {{
        min-height:90px;
        border-radius:16px !important;
        padding:1rem !important;
        background:{SURFACE} !important;
        border:1px dashed rgba(99,102,241,.34) !important;
        box-shadow:{SHADOW_SOFT} !important;
        transition:border-color .16s ease,background .16s ease !important;
      }}
      div[data-testid="stFileUploader"] section:hover {{
        border-color:rgba(99,102,241,.58) !important;
        background:{SURFACE_2} !important;
      }}
      div[data-testid="stFileUploaderDropzoneInstructions"] {{
        display:flex !important;
        flex-direction:column !important;
        justify-content:center !important;
        gap:.34rem !important;
        line-height:1.2 !important;
      }}
      div[data-testid="stFileUploaderDropzoneInstructions"] > div {{
        display:none !important;
      }}
      div[data-testid="stFileUploaderDropzoneInstructions"]::before {{
        content:"Dosyayı buraya sürükleyin";
        display:block;
        font-size:.88rem;
        font-weight:720;
        color:{TEXT};
      }}
      div[data-testid="stFileUploaderDropzoneInstructions"]::after {{
        content:"En fazla 10 MB • TXT, DOCX, PDF";
        display:block;
        font-size:.74rem;
        color:{MUTED};
      }}
      div[data-testid="stFileUploader"] section button {{
        position:relative !important;
        color:transparent !important;
        min-width:108px !important;
        min-height:40px !important;
        border-radius:10px !important;
        border:1px solid rgba(99,102,241,.46) !important;
        background:rgba(99,102,241,.095) !important;
        box-shadow:none !important;
      }}
      div[data-testid="stFileUploader"] section button > * {{
        display:none !important;
      }}
      div[data-testid="stFileUploader"] section button::after {{
        content:"Belge seç";
        position:absolute;
        inset:0;
        display:flex;
        align-items:center;
        justify-content:center;
        color:{ACCENT};
        font-size:.84rem;
        font-weight:760;
      }}
      div[data-testid="stFileUploader"] section button:hover {{
        background:rgba(99,102,241,.15) !important;
        border-color:{ACCENT} !important;
      }}

      /* Document summary */
      .stApp h4 {{
        margin-top:1.2rem;
        margin-bottom:.68rem;
        font-weight:790;
        letter-spacing:-.025em;
      }}
      .td-summary-grid {{
        display:grid;
        grid-template-columns:repeat(4,minmax(0,1fr));
        gap:.9rem;
        margin-bottom:.15rem;
      }}
      .td-summary-card {{
        position:relative;
        min-height:98px;
        background:linear-gradient(145deg,{SURFACE},{SURFACE_2});
        border:1px solid {BORDER};
        border-radius:15px;
        padding:.82rem .9rem .72rem;
        box-shadow:{SHADOW_SOFT};
        overflow:hidden;
      }}
      .td-summary-card::before {{
        content:"";
        position:absolute;
        left:0;
        right:0;
        top:0;
        height:2px;
        background:linear-gradient(90deg,rgba(99,102,241,.85),rgba(129,140,248,.18),transparent);
      }}
      .td-summary-label {{
        color:{MUTED};
        font-size:.75rem;
        font-weight:680;
        margin-bottom:.42rem;
      }}
      .td-summary-value {{
        color:{TEXT};
        font-size:1.9rem;
        font-weight:760;
        letter-spacing:-.04em;
        line-height:1.1;
      }}
      [data-testid="stMetric"] {{
        position:relative;
        min-height:98px;
        background:linear-gradient(145deg,{SURFACE},{SURFACE_2});
        border:1px solid {BORDER};
        border-radius:15px;
        padding:.82rem .9rem .72rem;
        box-shadow:{SHADOW_SOFT};
        overflow:hidden;
      }}
      [data-testid="stMetric"]::before {{
        content:"";
        position:absolute;
        left:0;
        right:0;
        top:0;
        height:2px;
        background:linear-gradient(90deg,rgba(99,102,241,.85),rgba(129,140,248,.18),transparent);
      }}
      [data-testid="stMetricLabel"] {{
        color:{MUTED} !important;
        font-size:.75rem !important;
        font-weight:680 !important;
      }}
      [data-testid="stMetricValue"] {{
        color:{TEXT} !important;
        font-size:1.9rem !important;
        font-weight:760 !important;
        letter-spacing:-.04em;
      }}

      .td-short-warning {{
        border:1px solid {SHORT_WARNING_BORDER};
        background:{SHORT_WARNING_BG};
        color:{SHORT_WARNING_TEXT} !important;
        border-radius:14px;
        padding:.92rem 1rem;
        margin:.9rem 0 1.05rem;
        font-size:.84rem;
        line-height:1.55;
        box-shadow:0 8px 24px rgba(245,158,11,.04);
      }}
      .td-short-warning strong {{
        color:inherit !important;
      }}

      /* Primary action */
      div[data-testid="stButton"] > button[kind="primary"] {{
        min-height:50px;
        border-radius:13px;
        font-weight:780;
        letter-spacing:-.01em;
        transition:transform .12s ease,filter .12s ease,box-shadow .12s ease;
      }}
      div[data-testid="stButton"] > button[kind="primary"]:not(:disabled) {{
        background:linear-gradient(135deg,#6366F1,#7377F5) !important;
        border-color:transparent !important;
        color:#fff !important;
        box-shadow:0 10px 24px rgba(99,102,241,.22) !important;
      }}
      div[data-testid="stButton"] > button[kind="primary"]:not(:disabled):hover {{
        filter:brightness(1.045);
        transform:translateY(-1px);
        box-shadow:0 13px 28px rgba(99,102,241,.26) !important;
      }}
      div[data-testid="stButton"] > button[kind="primary"]:disabled {{
        opacity:1 !important;
        background:{SURFACE_2} !important;
        border:1px solid {BORDER} !important;
        color:{MUTED} !important;
        cursor:not-allowed;
        box-shadow:none !important;
      }}

      /* Result screen */
      .td-score-card {{
        border:1px solid {BORDER};
        border-radius:18px;
        padding:1.4rem 1.25rem;
        background:linear-gradient(145deg,{SURFACE},{SURFACE_2});
        box-shadow:{SHADOW};
      }}
      .td-ring {{
        --score:0;
        width:176px;
        height:176px;
        margin:0 auto 1.15rem;
        border-radius:50%;
        display:grid;
        place-items:center;
        background:conic-gradient(#ef4444 calc(var(--score) * 1%), rgba(128,128,128,.18) 0);
        position:relative;
      }}
      .td-ring::after {{
        content:"";
        width:138px;
        height:138px;
        border-radius:50%;
        background:{BG};
        position:absolute;
      }}
      .td-ring-value {{
        position:relative;
        z-index:1;
        font-size:2.35rem;
        font-weight:800;
        letter-spacing:-.05em;
      }}
      .td-ring-label {{text-align:center;font-weight:750;font-size:1rem;}}
      .td-muted {{color:{MUTED};}}
      .td-center {{text-align:center;}}
      .td-doc {{
        border:1px solid {BORDER};
        border-radius:16px;
        background:{SURFACE};
        padding:1.05rem 1.15rem;
        box-shadow:{SHADOW_SOFT};
      }}
      .td-paragraph {{
        padding:.85rem .95rem;
        margin:.6rem 0;
        border-radius:10px;
        background:{SOFT};
        border-left:3px solid rgba(99,102,241,.42);
      }}
      .td-paragraph-head {{
        font-size:.76rem;
        font-weight:700;
        color:{MUTED};
        margin-bottom:.35rem;
      }}
      details[data-testid="stExpander"] {{
        background:{SURFACE};
        border-color:{BORDER} !important;
        border-radius:13px !important;
      }}

      @media (max-width:700px) {{
        .block-container {{padding-top:1.05rem;padding-left:1rem;padding-right:1rem;}}
        .td-subtitle {{display:none;}}
        .td-mark {{width:39px;height:39px;border-radius:11px;}}
        .td-brand {{font-size:1.5rem;}}
        .td-summary-grid {{grid-template-columns:repeat(2,minmax(0,1fr));}}
        .td-summary-card,[data-testid="stMetric"] {{min-height:88px;}}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

brand_col, theme_col = st.columns([12, 1])
with brand_col:
    st.markdown(
        """
        <div class="td-brand-wrap">
          <div class="td-mark">TD</div>
          <div>
            <div class="td-brand">TürkDet</div>
            <div class="td-subtitle">Türkçe Yapay Zekâ Metin Analizi</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with theme_col:
    st.button(
        "Tema",
        key="theme_toggle",
        on_click=_toggle_theme,
    )

st.markdown('<div class="td-header-rule"></div>', unsafe_allow_html=True)

st.markdown('<div class="td-kicker">Belge analizi</div>', unsafe_allow_html=True)
st.markdown("## Türkçe metninizi analiz edin")
st.markdown(
    '<div class="td-lead">Metni doğrudan yapıştırın veya TXT, DOCX ya da metin katmanına sahip PDF belgesi yükleyin.</div>',
    unsafe_allow_html=True,
)

input_mode = st.segmented_control(
    "Giriş yöntemi",
    options=["Metin yapıştır", "Belge yükle"],
    default="Metin yapıştır",
    selection_mode="single",
    label_visibility="collapsed",
    key="input_mode",
)

text = ""
uploaded_name = ""

if input_mode == "Metin yapıştır":
    if "pasted_text_widget" not in st.session_state:
        st.session_state["pasted_text_widget"] = st.session_state["pasted_text_buffer"]

    pasted_text = st.text_area(
        "Türkçe metin",
        height=300,
        placeholder="Analiz etmek istediğiniz Türkçe metni buraya yapıştırın…",
        label_visibility="collapsed",
        key="pasted_text_widget",
        on_change=_sync_pasted_text,
    )
    st.session_state["pasted_text_buffer"] = pasted_text
    text = pasted_text.strip()
    st.markdown(
        '<div class="td-help">Belge özeti yazdıkça güncellenir. TürkDet model analizi yalnızca <strong>Analizi Başlat</strong> düğmesine bastığınızda çalışır.</div>',
        unsafe_allow_html=True,
    )

elif input_mode == "Belge yükle":
    st.markdown(
        '<div class="td-upload-copy">Belgenizi buraya bırakın veya bilgisayarınızdan seçin.</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Belge seçin",
        type=["txt", "docx", "pdf"],
        help="Taranmış/görüntü tabanlı PDF'lerde OCR henüz etkin değildir.",
        label_visibility="collapsed",
        key="uploaded_document",
    )

    if uploaded is not None:
        uploaded_name = uploaded.name
        try:
            extracted_text = extract_text(uploaded.name, uploaded.getvalue()).strip()
        except DocumentParseError as exc:
            st.session_state["uploaded_text_buffer"] = ""
            st.session_state["uploaded_name_buffer"] = ""
            st.error(str(exc))
        else:
            st.session_state["uploaded_text_buffer"] = extracted_text
            st.session_state["uploaded_name_buffer"] = uploaded.name
            text = extracted_text
            st.success(f"{uploaded.name} belgesinden metin çıkarıldı.")
            with st.expander("Çıkarılan metni önizle"):
                st.write(text[:8000])
    elif st.session_state["uploaded_text_buffer"]:
        text = st.session_state["uploaded_text_buffer"]
        uploaded_name = st.session_state["uploaded_name_buffer"]
        st.info(f"Son yüklenen belge korunuyor: {uploaded_name}")
        with st.expander("Çıkarılan metni önizle"):
            st.write(text[:8000])

stats = get_document_stats(text) if text else None
summary_words = stats.words if stats is not None else 0
summary_paragraphs = stats.paragraphs if stats is not None else 0
summary_sentences = stats.sentences_approx if stats is not None else 0
summary_characters = stats.characters if stats is not None else 0

st.markdown("#### Belge özeti")
st.markdown(
    f"""
    <div class="td-summary-grid">
      <div class="td-summary-card">
        <div class="td-summary-label">Kelime</div>
        <div class="td-summary-value" id="td-stat-words">{summary_words:,}</div>
      </div>
      <div class="td-summary-card">
        <div class="td-summary-label">Paragraf</div>
        <div class="td-summary-value" id="td-stat-paragraphs">{summary_paragraphs:,}</div>
      </div>
      <div class="td-summary-card">
        <div class="td-summary-label">Yaklaşık cümle</div>
        <div class="td-summary-value" id="td-stat-sentences">{summary_sentences:,}</div>
      </div>
      <div class="td-summary-card">
        <div class="td-summary-label">Karakter</div>
        <div class="td-summary-value" id="td-stat-characters">{summary_characters:,}</div>
      </div>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)

if text and stats is not None and stats.words < MIN_WORDS:
    st.markdown(
        f'<div class="td-short-warning"><strong>Metin çok kısa.</strong> '
        f'Analiz için en az {MIN_WORDS} kelimelik bir metin gerekli. '
        'Bu sınır geliştirme aşamasındaki geçici bir arayüz korumasıdır; '
        'bilimsel geçerlilik eşiği değildir ve nihai doğrulama sonrasında güncellenecektir.</div>',
        unsafe_allow_html=True,
    )

can_analyze = bool(text) and stats is not None and stats.words >= MIN_WORDS

analyze = st.button(
    "Analizi Başlat",
    type="primary",
    use_container_width=True,
    disabled=not can_analyze,
)

if analyze:
    st.markdown("---")
    st.markdown("## TürkDet Analiz Raporu")
    if uploaded_name:
        st.caption(f"Belge: {uploaded_name}")

    paragraphs = split_paragraphs(text)

    try:
        result = predict_text(text)
    except ValueError as exc:
        st.error(str(exc))
    except InferenceUnavailableError:
        left, right = st.columns([2.15, 1], gap="large")

        with left:
            _render_document(
                paragraphs,
                "Paragraf skorları, segment düzeyindeki doğrulama tamamlandığında burada gösterilecektir.",
            )

        with right:
            st.markdown("### Genel sonuç")
            st.markdown(
                """
                <div class="td-score-card">
                  <div class="td-ring" style="--score:0;">
                    <div class="td-ring-value">—</div>
                  </div>
                  <div class="td-ring-label">AI yazım skoru</div>
                  <div class="td-center td-muted" style="margin-top:.35rem;">Model bağlantısı bekleniyor</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info("Doğrulanmış üretim modeli henüz web uygulamasına bağlanmadı.")
            st.caption("TürkDet, gerçek model bağlı değilken yüzde veya karar üretmez.")
            _render_report_download(
                text=text,
                uploaded_name=uploaded_name,
                stats=stats,
                result_message="Analiz sonucu üretilemedi",
                ai_probability=None,
                model_available=False,
                status_note=(
                    "Doğrulanmış üretim modeli henüz uygulamaya bağlanmadığı için "
                    "bu raporda yüzde veya karar yer almaz."
                ),
            )

    else:
        score_percent = max(0.0, min(100.0, result.ai_probability * 100.0))
        result_message = _safe_result_message(result.label)
        left, right = st.columns([2.15, 1], gap="large")

        with left:
            _render_document(
                paragraphs,
                "Belge genel skorla birlikte incelenir. Paragraf skorları yalnızca ayrıca doğrulandığında açılır.",
            )

        with right:
            st.markdown("### Genel sonuç")
            st.markdown(
                f"""
                <div class="td-score-card">
                  <div class="td-ring" style="--score:{score_percent:.1f};">
                    <div class="td-ring-value">%{score_percent:.1f}</div>
                  </div>
                  <div class="td-ring-label">AI yazım skoru</div>
                  <div class="td-center td-muted" style="margin-top:.35rem;">TürkDet model çıktısı</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.metric("Sonuç", result_message)
            st.caption(
                "Bu skor olasılıksal bir model çıktısıdır; tek başına kesin yazarlık veya ihlal kanıtı değildir."
            )
            _render_report_download(
                text=text,
                uploaded_name=uploaded_name,
                stats=stats,
                result_message=result_message,
                ai_probability=result.ai_probability,
                model_available=True,
            )

    if len(paragraphs) > 30:
        st.caption(f"İlk 30 paragraf gösteriliyor. Toplam paragraf: {len(paragraphs)}")