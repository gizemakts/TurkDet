"""TürkDet single-page Turkish AI text analysis interface."""

from __future__ import annotations

from html import escape

import streamlit as st

from app.document_parser import DocumentParseError, extract_text, get_document_stats, split_paragraphs
from app.inference import InferenceUnavailableError, predict_text


SHORT_TEXT_NOTICE_WORDS = 30  # UI guidance only; not a scientific validity threshold.
ACCENT = "#6366F1"


st.set_page_config(
    page_title="TürkDet",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Persistent input state
# ---------------------------------------------------------------------------
st.session_state.setdefault("pasted_text_buffer", "")
st.session_state.setdefault("uploaded_text_buffer", "")
st.session_state.setdefault("uploaded_name_buffer", "")


def _sync_pasted_text() -> None:
    st.session_state["pasted_text_buffer"] = st.session_state.get("pasted_text_widget", "")


def _safe_result_message(label: str) -> str:
    """Translate a binary backend label into cautious user-facing language."""
    normalized = str(label).strip().upper().replace(" ", "_")
    if normalized in {"HUMAN", "İNSAN", "INSAN", "0"}:
        return "Belirgin yapay zekâ izi saptanmadı"
    if normalized in {"AI", "AI_GENERATED", "AI-GENERATED", "1"}:
        return "Yapay zekâ üretimiyle uyumlu sinyal saptandı"
    return "Model çıktısı hazır"


st.markdown(
    f"""
    <style>
      header[data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stDecoration"],
      #MainMenu,
      footer {{
        display: none !important;
        visibility: hidden !important;
      }}

      .block-container {{
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
      }}

      .td-header {{
        display:flex;
        align-items:center;
        gap:1rem;
        padding:.35rem 0 1.25rem;
        margin-bottom:1.5rem;
        border-bottom:1px solid rgba(128,128,128,.16);
      }}
      .td-brand-wrap {{display:flex; align-items:center; gap:.8rem;}}
      .td-mark {{
        width:42px;
        height:42px;
        border-radius:11px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight:800;
        font-size:1.02rem;
        letter-spacing:-.04em;
        border:1px solid rgba(255,255,255,.14);
        background:rgba(255,255,255,.06);
      }}
      .td-brand {{
        font-size:1.72rem;
        font-weight:800;
        letter-spacing:-.045em;
        line-height:1;
      }}
      .td-subtitle {{opacity:.58; margin-top:.27rem; font-size:.88rem;}}

      .td-kicker {{
        font-size:.76rem;
        font-weight:750;
        letter-spacing:.09em;
        text-transform:uppercase;
        opacity:.50;
        margin-bottom:.45rem;
      }}
      .td-lead {{
        opacity:.70;
        max-width:760px;
        margin-bottom:1.1rem;
        line-height:1.55;
      }}
      .td-upload-copy {{
        margin:.5rem 0 .75rem;
        font-size:.88rem;
        opacity:.67;
      }}
      .td-help {{
        margin:.35rem 0 1rem;
        font-size:.84rem;
        opacity:.58;
      }}
      .td-note {{
        border:1px solid rgba(99,102,241,.28);
        background:rgba(99,102,241,.07);
        border-radius:12px;
        padding:.8rem .95rem;
        margin:.85rem 0 1.15rem;
        font-size:.88rem;
        line-height:1.5;
      }}

      .td-score-card {{
        border:1px solid rgba(128,128,128,.22);
        border-radius:18px;
        padding:1.4rem 1.25rem;
        background:rgba(128,128,128,.035);
      }}
      .td-ring {{
        --score: 0;
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
        background:var(--background-color, #0e1117);
        position:absolute;
      }}
      .td-ring-value {{
        position:relative;
        z-index:1;
        font-size:2.35rem;
        font-weight:800;
        letter-spacing:-.05em;
      }}
      .td-ring-label {{text-align:center; font-weight:750; font-size:1rem;}}
      .td-muted {{opacity:.62;}}
      .td-center {{text-align:center;}}

      .td-doc {{
        border:1px solid rgba(128,128,128,.20);
        border-radius:16px;
        background:rgba(128,128,128,.025);
        padding:1.05rem 1.15rem;
      }}
      .td-paragraph {{
        padding:.85rem .95rem;
        margin:.6rem 0;
        border-radius:10px;
        background:rgba(128,128,128,.045);
        border-left:3px solid rgba(128,128,128,.28);
      }}
      .td-paragraph-head {{
        font-size:.76rem;
        font-weight:700;
        opacity:.52;
        margin-bottom:.35rem;
      }}

      div[data-testid="stTextArea"] textarea {{
        border-radius:14px;
        min-height:280px;
      }}
      div[data-testid="stTextArea"] textarea:focus {{
        border-color:{ACCENT} !important;
        box-shadow:0 0 0 1px {ACCENT} !important;
      }}

      div[data-testid="stFileUploader"] section {{
        border-radius:14px;
        padding-top:1rem;
        padding-bottom:1rem;
      }}

      div[data-testid="stFileUploader"] button {{
        position:relative;
        color:transparent !important;
        min-width:112px;
      }}
      div[data-testid="stFileUploader"] button > * {{display:none !important;}}
      div[data-testid="stFileUploader"] button::after {{
        content:"Belge seç";
        position:absolute;
        inset:0;
        display:flex;
        align-items:center;
        justify-content:center;
        color:var(--text-color, #fafafa);
        font-size:.9rem;
        font-weight:700;
      }}

      div[data-testid="stButton"] > button[kind="primary"] {{
        min-height:50px;
        border-radius:11px;
        font-weight:780;
        transition:transform .12s ease, filter .12s ease;
      }}
      div[data-testid="stButton"] > button[kind="primary"]:not(:disabled) {{
        background:{ACCENT};
        border-color:{ACCENT};
        color:#fff;
      }}
      div[data-testid="stButton"] > button[kind="primary"]:not(:disabled):hover {{
        filter:brightness(1.07);
        transform:translateY(-1px);
      }}
      div[data-testid="stButton"] > button[kind="primary"]:disabled {{opacity:.48;}}

      div[data-testid="stSegmentedControl"] {{margin-bottom:.35rem;}}
      div[data-testid="stSegmentedControl"] button {{font-weight:680;}}

      @media (max-width: 700px) {{
        .block-container {{padding-top:1.25rem;}}
        .td-subtitle {{display:none;}}
        .td-mark {{width:38px; height:38px;}}
        .td-brand {{font-size:1.55rem;}}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="td-header">
      <div class="td-brand-wrap">
        <div class="td-mark">TD</div>
        <div>
          <div class="td-brand">TürkDet</div>
          <div class="td-subtitle">Türkçe Yapay Zekâ Metin Analizi</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="td-kicker">Belge analizi</div>', unsafe_allow_html=True)
st.markdown("## Türkçe metninizi analiz edin")
st.markdown(
    '<div class="td-lead">Metni doğrudan yapıştırın veya TXT, DOCX ya da metin katmanına sahip PDF belgesi yükleyin.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="td-note"><strong>Kapsam notu:</strong> TürkDet’in desteklediği metin türleri ve güvenilir kullanım aralığı, akademik ve gazete metinleri üzerindeki doğrulama tamamlandıkça güncellenecektir. Sonuçlar olasılıksaldır ve tek başına yazarlık kanıtı değildir.</div>',
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
        '<div class="td-help">Belge özeti, girilen metin hakkında hızlı bilgi verir. TürkDet model analizi yalnızca <strong>Analizi Başlat</strong> düğmesine bastığınızda çalışır.</div>',
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

stats = None
if text:
    stats = get_document_stats(text)
    st.markdown("#### Belge özeti")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kelime", f"{stats.words:,}".replace(",", "."))
    c2.metric("Paragraf", stats.paragraphs)
    c3.metric("Yaklaşık cümle", stats.sentences_approx)
    c4.metric("Karakter", f"{stats.characters:,}".replace(",", "."))

    if stats.words < SHORT_TEXT_NOTICE_WORDS:
        st.warning(
            "Metin çok kısa görünüyor. Kısa metinlerde model sinyalleri kararsız olabilir; "
            "güvenilir minimum uzunluk nihai doğrulama tamamlandığında belirlenecektir."
        )

analyze = st.button(
    "Analizi Başlat",
    type="primary",
    use_container_width=True,
    disabled=not bool(text),
)

st.caption(
    "Yerel demo metni kalıcı bir dosyaya yazmak üzere tasarlanmamıştır. "
    "Bulut sürümü yayınlanmadan önce veri işleme ve gizlilik politikası ayrıca doğrulanacaktır."
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
    except InferenceUnavailableError as exc:
        left, right = st.columns([2.15, 1], gap="large")

        with left:
            st.markdown("### Belge görünümü")
            st.caption("Paragraf skorları, segment düzeyindeki doğrulama tamamlandığında burada gösterilecektir.")
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
            st.markdown('</div>', unsafe_allow_html=True)

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
            st.warning(str(exc))
            st.caption("TürkDet, gerçek model bağlı değilken yüzde veya karar üretmez.")

    else:
        score_percent = max(0.0, min(100.0, result.ai_probability * 100.0))
        left, right = st.columns([2.15, 1], gap="large")

        with left:
            st.markdown("### Belge görünümü")
            st.caption("Belge genel skorla birlikte incelenir. Paragraf skorları yalnızca ayrıca doğrulandığında açılır.")
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
            st.markdown('</div>', unsafe_allow_html=True)

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
            st.metric("Sonuç", _safe_result_message(result.label))
            st.caption(
                "Bu skor olasılıksal bir model çıktısıdır; tek başına kesin yazarlık veya ihlal kanıtı değildir."
            )

    if len(paragraphs) > 30:
        st.caption(f"İlk 30 paragraf gösteriliyor. Toplam paragraf: {len(paragraphs)}")
