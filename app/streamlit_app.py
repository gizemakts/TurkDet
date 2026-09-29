"""TürkDet Streamlit research/demo interface."""

from __future__ import annotations

import math
from typing import Any

import streamlit as st

from app.document_parser import DocumentParseError, extract_text, get_document_stats, split_paragraphs
from app.inference import InferenceUnavailableError, predict_text
from app.metrics_loader import load_benchmark, load_final_metrics
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
      .block-container {max-width: 1180px; padding-top: 1.5rem;}
      .turkdet-hero {padding: 1.2rem 0 .8rem 0;}
      .turkdet-title {font-size: 2.8rem; font-weight: 760; margin-bottom: .15rem;}
      .turkdet-subtitle {font-size: 1.14rem; opacity: .72;}
      .research-note {opacity: .72; font-size: .92rem;}
      .report-card {border: 1px solid rgba(128,128,128,.25); border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: .85rem;}
      .score-placeholder {font-size: 2.4rem; font-weight: 760; line-height: 1.1;}
      .muted {opacity: .68;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="turkdet-hero">
      <div class="turkdet-title">TürkDet</div>
      <div class="turkdet-subtitle">Türkçe Yapay Zekâ Metin Analizi</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Araştırma arayüzü · Sonuçlar olasılıksaldır ve tek başına kesin yazarlık kanıtı değildir.")


def _metric_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _format_metric(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return "—"
        return f"{value:.4f}"
    return str(value)


def _render_document_summary(text: str) -> None:
    stats = get_document_stats(text)
    st.markdown("#### Belge özeti")
    cols = st.columns(4)
    cols[0].metric("Kelime", f"{stats.words:,}".replace(",", "."))
    cols[1].metric("Paragraf", stats.paragraphs)
    cols[2].metric("Yaklaşık cümle", stats.sentences_approx)
    cols[3].metric("Karakter", f"{stats.characters:,}".replace(",", "."))


def _render_segment_preview(text: str) -> None:
    paragraphs = split_paragraphs(text)
    st.markdown("#### Belge içi analiz")
    st.caption(
        "Paragraf bazlı AI skorları, model bu metin uzunluklarında ayrıca doğrulandığında etkinleştirilecektir."
    )
    if not paragraphs:
        st.info("Paragraf bulunamadı.")
        return

    for index, paragraph in enumerate(paragraphs[:25], start=1):
        with st.container(border=True):
            left, right = st.columns([5, 1])
            left.markdown(f"**Paragraf {index}**")
            left.write(paragraph)
            right.metric("AI skoru", "—")
            right.caption("Doğrulama bekliyor")

    if len(paragraphs) > 25:
        st.caption(f"Önizlemede ilk 25 paragraf gösteriliyor. Toplam: {len(paragraphs)}")


def render_detector() -> None:
    st.subheader("Belge Analizi")
    st.write(
        "Türkçe metni doğrudan yapıştırın veya TXT, DOCX ya da metin katmanına sahip PDF yükleyin."
    )

    input_tab, upload_tab = st.tabs(["Metin yapıştır", "Belge yükle"])

    pasted_text = ""
    uploaded_text = ""

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
            try:
                uploaded_text = extract_text(uploaded.name, uploaded.getvalue())
            except DocumentParseError as exc:
                st.error(str(exc))
            else:
                st.success(f"{uploaded.name} belgesinden metin çıkarıldı.")
                with st.expander("Çıkarılan metni önizle"):
                    st.write(uploaded_text[:8000])

    text = pasted_text.strip() or uploaded_text.strip()

    status = get_model_status()
    if status.available:
        st.info(status.message)
    else:
        st.warning(status.message)

    if text:
        _render_document_summary(text)

    analyze = st.button(
        "Analizi Başlat",
        type="primary",
        use_container_width=True,
        disabled=not bool(text),
    )

    if analyze:
        st.markdown("---")
        st.markdown("### TürkDet Analiz Raporu")

        try:
            result = predict_text(text)
        except ValueError as exc:
            st.error(str(exc))
        except InferenceUnavailableError as exc:
            st.markdown(
                """
                <div class="report-card">
                  <div class="score-placeholder">—</div>
                  <div><strong>Genel AI skoru</strong></div>
                  <div class="muted">Üretim modeli henüz bu web arayüzüne bağlanmadı.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.warning(str(exc))
            st.caption(
                "Bu nedenle TürkDet herhangi bir tahmin, yüzde veya paragraf skoru uydurmaz."
            )
            _render_segment_preview(text)
        else:
            left, middle, right = st.columns(3)
            left.metric("Karar", result.label)
            middle.metric("Genel AI skoru", f"%{result.ai_probability * 100:.2f}")
            right.metric("Karar eşiği", f"{result.threshold:.4f}")
            st.progress(min(max(result.ai_probability, 0.0), 1.0))
            st.caption(
                "Gösterilen skor model çıktısıdır; tek başına kesin yazarlık veya ihlal kanıtı olarak kullanılmamalıdır."
            )
            _render_segment_preview(text)


def render_performance() -> None:
    st.subheader("Model Performansı")
    result = load_final_metrics()
    if not result.available:
        st.info("Final evaluation pending")
        st.caption(f"Beklenen artifact: `{result.path}`")
        return

    data = result.data
    metrics = [
        ("AUC", _metric_value(data, "auc", "AUC")),
        ("F1", _metric_value(data, "f1", "f1_score", "F1")),
        ("Accuracy", _metric_value(data, "accuracy", "Accuracy")),
        ("Precision", _metric_value(data, "precision", "Precision")),
        ("Recall / TPR", _metric_value(data, "recall", "tpr", "TPR")),
        ("FPR", _metric_value(data, "fpr", "FPR")),
        ("Brier", _metric_value(data, "brier", "brier_score")),
        ("Log-loss", _metric_value(data, "log_loss", "logloss")),
        ("ECE", _metric_value(data, "ece", "ECE")),
    ]

    for start in range(0, len(metrics), 3):
        cols = st.columns(3)
        for col, (label, value) in zip(cols, metrics[start : start + 3]):
            col.metric(label, _format_metric(value))

    confusion = _metric_value(data, "confusion_matrix")
    if confusion is not None:
        st.markdown("#### Confusion matrix")
        st.dataframe(confusion, use_container_width=True)

    with st.expander("Ham final metrics artifact"):
        st.json(data)


def render_benchmark() -> None:
    st.subheader("Çalışma Karşılaştırması")
    result = load_benchmark()
    if not result.available:
        st.info("Karşılaştırma sonuçları henüz yayınlanmadı.")
        st.caption(f"Beklenen artifact: `{result.path}`")
        st.write(
            "Bu bölüm TürkDet ile 2026 referans çalışmasının aynı metrik tanımları "
            "ve karşılaştırılabilir değerlendirme koşulları altındaki sonuçlarını gösterecek."
        )
        return

    data = result.data
    rows = data.get("rows")
    if isinstance(rows, list) and rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.warning("Benchmark artifact mevcut ancak `rows` listesi bulunamadı.")
        st.json(data)

    st.caption("Eksik değerler sıfır olarak yorumlanmaz; mevcut değil olarak gösterilir.")


def render_methodology() -> None:
    st.subheader("Yöntem")
    st.markdown(
        """
        **Amaç**  
        TürkDet, Türkçe metinlerde yapay zekâ üretimiyle ilişkili örüntüleri araştırma temelli
        bir dedektörle belge düzeyinde incelemeyi hedefler.

        **Veri kapsamı**  
        Türkçe akademik/makale metinleri ile gazete metinlerinin birleşik değerlendirme
        çerçevesi için hazırlanmış araştırma hattı.

        **Belge işleme**  
        Web katmanı TXT, DOCX ve metin katmanına sahip PDF belgelerinden metin çıkarabilir.
        OCR, eğitim, kalibrasyon veya bilimsel metrik üretimi web katmanında yapılmaz.

        **Model ve çıkarım**  
        Web uygulaması eğitim çalıştırmaz. Yalnızca doğrulanmış final/frozen model artifact'ı
        ile side-effect-free bir inference adaptörü bağlandığında tahmin üretir.

        **Kalibrasyon ve karar eşiği**  
        Olasılık kalibrasyonu ve karar eşiği araştırma pipeline'ında üretilen artifact'lardan
        okunacaktır; arayüz içinde yeniden hesaplanmaz veya değiştirilmez.

        **Paragraf/cümle analizi**  
        Granüler skorlar ancak model bu uzunluk ve segment türlerinde ayrıca değerlendirildiğinde
        etkinleştirilecektir. Belge düzeyinde doğrulanan bir modelin skorunu keyfi biçimde
        cümle düzeyine taşımayız.

        **Tekrarlanabilirlik**  
        Arayüz katmanı eğitim/değerlendirme kodundan ayrıdır. Böylece UI değişiklikleri
        bilimsel sonuçları veya deney protokolünü değiştirmez.
        """
    )
    st.markdown(
        '<p class="research-note">Not: Bu metin nihai makale metodolojisinin yerine geçmez; '
        'araştırma artifact’ları tamamlandıkça güncellenecektir.</p>',
        unsafe_allow_html=True,
    )


tab_detector, tab_perf, tab_benchmark, tab_method = st.tabs(
    ["Belge Analizi", "Performans", "Karşılaştırma", "Yöntem"]
)
with tab_detector:
    render_detector()
with tab_perf:
    render_performance()
with tab_benchmark:
    render_benchmark()
with tab_method:
    render_methodology()
