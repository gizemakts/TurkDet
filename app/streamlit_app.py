"""TürkDet single-page Turkish AI text analysis interface."""

from __future__ import annotations

import streamlit as st

from app.document_parser import DocumentParseError, extract_text, get_document_stats, split_paragraphs
from app.inference import InferenceUnavailableError, predict_text
from app.model_loader import get_model_status


st.set_page_config(
    page_title="TürkDet",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 1.3rem; padding-bottom: 3rem;}
      .td-header {display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; padding:.7rem 0 1.3rem; border-bottom:1px solid rgba(128,128,128,.18);}
      .td-brand {font-size:2.45rem; font-weight:780; letter-spacing:-.04em; line-height:1;}
      .td-subtitle {opacity:.68; margin-top:.35rem; font-size:1rem;}
      .td-badge {border:1px solid rgba(128,128,128,.25); border-radius:999px; padding:.4rem .75rem; opacity:.78; font-size:.85rem;}
      .td-card {border:1px solid rgba(128,128,128,.22); border-radius:16px; padding:1rem 1.15rem; background:rgba(128,128,128,.025);}
      .td-score {font-size:3.25rem; font-weight:800; line-height:1; letter-spacing:-.05em;}
      .td-muted {opacity:.66;}
      .td-section {margin-top:1.6rem;}
      .td-paragraph {border-left:4px solid rgba(128,128,128,.30); padding:.8rem 1rem; margin:.65rem 0; border-radius:0 10px 10px 0; background:rgba(128,128,128,.035);}
      .td-small {font-size:.88rem; opacity:.68;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="td-header">
      <div>
        <div class="td-brand">TürkDet</div>
        <div class="td-subtitle">Türkçe Yapay Zekâ Metin Analizi</div>
      </div>
      <div class="td-badge">Belge analizi</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Belgenizi analiz edin")
st.write("Türkçe metni yapıştırın veya TXT, DOCX ya da metin katmanına sahip PDF yükleyin.")

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
    st.markdown('<div class="td-section"></div>', unsafe_allow_html=True)
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

    status = get_model_status()

    try:
        result = predict_text(text)
    except ValueError as exc:
        st.error(str(exc))
    except InferenceUnavailableError as exc:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(
                """
                <div class="td-card">
                  <div class="td-score">—</div>
                  <div style="font-weight:700; margin-top:.5rem;">Genel AI skoru</div>
                  <div class="td-muted" style="margin-top:.4rem;">Model bağlantısı bekleniyor</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            st.markdown("#### Sonuç")
            st.warning(str(exc))
            st.write(
                "Gerçek TürkDet modeli web arayüzüne bağlanana kadar uygulama herhangi bir "
                "yüzde, karar veya risk seviyesi üretmez."
            )
    else:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(
                f"""
                <div class="td-card">
                  <div class="td-score">%{result.ai_probability * 100:.1f}</div>
                  <div style="font-weight:700; margin-top:.5rem;">Genel AI skoru</div>
                  <div class="td-muted" style="margin-top:.4rem;">TürkDet model çıktısı</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            st.markdown("#### Sonuç")
            st.metric("Model kararı", result.label)
            st.progress(min(max(result.ai_probability, 0.0), 1.0))
            st.caption(
                "Bu skor olasılıksal bir model çıktısıdır; tek başına kesin yazarlık veya ihlal kanıtı değildir."
            )

    st.markdown("### Belge içi görünüm")
    st.caption(
        "Paragraf bazlı AI skorları, TürkDet bu uzunluklarda ayrıca doğrulandığında burada gösterilecektir."
    )

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        st.info("Belgede gösterilecek paragraf bulunamadı.")
    else:
        for index, paragraph in enumerate(paragraphs[:30], start=1):
            st.markdown(
                f"""
                <div class="td-paragraph">
                  <div class="td-small">Paragraf {index} · AI skoru: —</div>
                  <div style="margin-top:.35rem;">{paragraph}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if len(paragraphs) > 30:
            st.caption(f"İlk 30 paragraf gösteriliyor. Toplam paragraf: {len(paragraphs)}")

st.markdown("---")
st.caption(
    "TürkDet, Türkçe metinlerde yapay zekâ üretimiyle ilişkili örüntüleri analiz etmek için geliştirilen bir araştırma uygulamasıdır."
)
