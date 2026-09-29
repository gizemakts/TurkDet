"""TürkDet Streamlit research/demo interface."""

from __future__ import annotations

import math
from typing import Any

import streamlit as st

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
      .block-container {max-width: 1120px; padding-top: 2rem;}
      .turkdet-hero {padding: 1.35rem 0 1rem 0;}
      .turkdet-title {font-size: 2.75rem; font-weight: 750; margin-bottom: .1rem;}
      .turkdet-subtitle {font-size: 1.12rem; opacity: .72;}
      .research-note {opacity: .72; font-size: .92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="turkdet-hero">
      <div class="turkdet-title">TürkDet</div>
      <div class="turkdet-subtitle">Türkçe Yapay Zekâ Metin Tespiti</div>
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


def render_detector() -> None:
    st.subheader("Metin Dedektörü")
    st.write("Analiz etmek istediğiniz Türkçe metni aşağıya yapıştırın.")
    text = st.text_area(
        "Metin",
        height=260,
        placeholder="Türkçe metni buraya yapıştırın…",
        label_visibility="collapsed",
    )

    status = get_model_status()
    if status.available:
        st.info(status.message)
    else:
        st.warning(status.message)

    if st.button("Analiz Et", type="primary", use_container_width=True):
        try:
            result = predict_text(text)
        except ValueError as exc:
            st.error(str(exc))
        except InferenceUnavailableError as exc:
            st.warning(str(exc))
        else:
            left, middle, right = st.columns(3)
            left.metric("Karar", result.label)
            middle.metric("AI olasılığı", f"%{result.ai_probability * 100:.2f}")
            right.metric("Karar eşiği", f"{result.threshold:.4f}")
            st.progress(min(max(result.ai_probability, 0.0), 1.0))


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
        **Veri kapsamı**  
        Türkçe akademik/makale metinleri ile gazete metinlerinin birleşik değerlendirme
        çerçevesi için hazırlanmış araştırma hattı.

        **Model ve çıkarım**  
        Web uygulaması eğitim çalıştırmaz. Yalnızca doğrulanmış final/frozen model artifact'ı
        ile side-effect-free bir inference adaptörü bağlandığında tahmin üretir.

        **Kalibrasyon ve karar eşiği**  
        Olasılık kalibrasyonu ve karar eşiği araştırma pipeline'ında üretilen artifact'lardan
        okunacaktır; arayüz içinde yeniden hesaplanmaz veya değiştirilmez.

        **Değerlendirme**  
        AUC, F1, Accuracy, Precision, Recall/TPR, FPR, Brier, Log-loss, ECE ve
        confusion matrix gibi ölçümler makine-okunur final sonuç dosyalarından yüklenir.

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
    ["Dedektör", "Performans", "Karşılaştırma", "Yöntem"]
)
with tab_detector:
    render_detector()
with tab_perf:
    render_performance()
with tab_benchmark:
    render_benchmark()
with tab_method:
    render_methodology()
