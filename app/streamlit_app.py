"""TürkDet single-page Turkish AI text analysis interface."""

from __future__ import annotations

from html import escape

import streamlit as st

from app.document_parser import DocumentParseError, extract_text, get_document_stats, split_paragraphs
from app.inference import InferenceUnavailableError, predict_text


st.set_page_config(
    page_title="TürkDet",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      [data-testid="stHeader"] {background: transparent;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}

      .block-container {
        max-width: 1180px;
        padding-top: 1.1rem;
        padding-bottom: 3rem;
      }

      .td-header {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:1rem;
        padding:.55rem 0 1.25rem;
        margin-bottom:1.35rem;
        border-bottom:1px solid rgba(128,128,128,.16);
      }
      .td-brand-wrap {display:flex; align-items:center; gap:.8rem;}
      .td-mark {
        width:42px;
        height:42px;
        border-radius:11px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight:800;
        font-size:1.05rem;
        letter-spacing:-.04em;
        border:1px solid rgba(255,255,255,.14);
        background:rgba(255,255,255,.06);
      }
      .td-brand {
        font-size:1.72rem;
        font-weight:800;
        letter-spacing:-.045em;
        line-height:1;
      }
      .td-subtitle {opacity:.58; margin-top:.27rem; font-size:.88rem;}

      .td-kicker {
        font-size:.78rem;
        font-weight:700;
        letter-spacing:.08em;
        text-transform:uppercase;
        opacity:.52;
        margin-bottom:.4rem;
      }
      .td-lead {opacity:.72; max-width:760px; margin-bottom:1.2rem;}

      .td-score-card {
        border:1px solid rgba(128,128,128,.22);
        border-radius:18px;
        padding:1.4rem 1.25rem;
        background:rgba(128,128,128,.035);
      }
      .td-ring {
        --score: 0;
        width:176px;
        height:176px;
        margin:0 auto 1.15rem;
        border-radius:50%;
        display:grid;
        place-items:center;
        background:conic-gradient(#ff4b4b calc(var(--score) * 1%), rgba(128,128,128,.18) 0);
        position:relative;
      }
      .td-ring::after {
        content:"";
        width:138px;
        height:138px;
        border-radius:50%;
        background:var(--background-color, #0e1117);
        position:absolute;
      }
      .td-ring-value {
        position:relative;
        z-index:1;
        font-size:2.35rem;
        font-weight:800;
        letter-spacing:-.05em;
      }
      .td-ring-label {
        text-align:center;
        font-weight:750;
        font-size:1rem;
      }
      .td-muted {opacity:.62;}
      .td-center {text-align:center;}
      .td-small {font-size:.84rem; opacity:.62;}

      .td-doc {
        border:1px solid rgba(128,128,128,.20);
        border-radius:16px;
        background:rgba(128,128,128,.025);
        padding:1.05rem 1.15rem;
      }
      .td-paragraph {
        padding:.85rem .95rem;
        margin:.6rem 0;
        border-radius:10px;
        background:rgba(128,128,128,.045);
        border-left:3px solid rgba(128,128,128,.28);
      }
      .td-paragraph-head {
        font-size:.76rem;
        font-weight:700;
        opacity:.52;
        margin-bottom:.35rem;
      }

      div[data-testid="stTextArea"] textarea {
        border-radius:14px;
        min-height:280px;
      }
      div[data-testid="stFileUploader"] section {
        border-radius:14px;
      }
      div[data-testid="stButton"] > button[kind="primary"] {
        min-height:48px;
        border-radius:11px;
        font-weight:750;
      }

      @media (max-width: 700px) {
        .td-subtitle {display:none;}
        .td-mark {width:38px; height:38px;}
        .td-brand {font-size:1.55rem;}
      }
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

input_tab, upload_tab = st.tabs(["Metin yapıştır", "Belge yükle"])

pasted_text = ""
uploaded_text = ""
uploaded_name = ""

with input_tab:
    pasted_text = st.text_area(
        "Türkçe metin",
        height=300,
        placeholder="Analiz etmek istediğiniz Türkçe metni buraya yapıştırın…",
        label_visibility="collapsed",
    )

with upload_tab:
    uploaded = st.file_uploader(
        "Belge seçin",
        type=["txt", "docx", "pdf"],
        help="Taranmış/görüntü tabanlı PDF'lerde OCR henüz etkin değildir.",
    )
    if uploaded is not None:
        uploaded_name = uploaded.name
        try:
            uploaded_text = extract_text(uploaded.name, uploaded.getvalue())
        except DocumentParseError as exc:
            st.error(str(exc))
        else:
            st.success(f"{uploaded.name} belgesinden metin çıkarıldı.")
            with st.expander("Çıkarılan metni önizle"):
                st.write(uploaded_text[:8000])

text = pasted_text.strip() or uploaded_text.strip()

if text:
    stats = get_document_stats(text)
    st.markdown("#### Belge özeti")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kelime", f"{stats.words:,}".replace(",", "."))
    c2.metric("Paragraf", stats.paragraphs)
    c3.metric("Yaklaşık cümle", stats.sentences_approx)
    c4.metric("Karakter", f"{stats.characters:,}".replace(",", "."))

analyze = st.button(
    "Analizi Başlat",
    type="primary",
    use_container_width=True,
    disabled=not bool(text),
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
            st.metric("Model kararı", result.label)
            st.caption(
                "Bu skor olasılıksal bir model çıktısıdır; tek başına kesin yazarlık veya ihlal kanıtı değildir."
            )

    if len(paragraphs) > 30:
        st.caption(f"İlk 30 paragraf gösteriliyor. Toplam paragraf: {len(paragraphs)}")

st.markdown("---")
st.caption("TürkDet · Türkçe yapay zekâ metin analizi")
