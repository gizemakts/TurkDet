# TürkDet

**Türkçe Yapay Zekâ Metin Tespiti** için araştırma ve demo web arayüzü.

Bu repository şu aşamada web uygulaması katmanını içerir. Eğitim, yeniden eğitim ve bilimsel değerlendirme web uygulamasının içinde çalıştırılmaz. Final/frozen model ve final metrikler doğrulanmış araştırma pipeline'ından artifact olarak bağlanır.

## Arayüz

Uygulama dört bölümden oluşur:

- **Dedektör:** doğrulanmış inference adaptörü bağlandığında Türkçe metin analizi.
- **Performans:** final machine-readable metrics artifact'ından değerlendirme ölçümleri.
- **Karşılaştırma:** TürkDet ile 2026 referans çalışma için artifact tabanlı benchmark.
- **Yöntem:** veri, model, kalibrasyon ve değerlendirme yaklaşımının kısa özeti.

Eksik model veya sonuç durumunda uygulama tahmin/metrik uydurmaz; bekleyen entegrasyonu açıkça gösterir.

## Lokal çalıştırma

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Artifact bağlantıları

Varsayılan sonuç yolları:

- `artifacts/final_metrics.json`
- `artifacts/benchmark.json`

İsteğe bağlı ortam değişkenleri:

```text
TURKDET_MODEL_PATH
TURKDET_METRICS_PATH
TURKDET_BENCHMARK_PATH
```

Model artifact'ının var olması tek başına inference'ı etkinleştirmez. Mevcut TürkDet araştırma repository'sindeki doğrulanmış preprocessing + model + calibration + threshold zinciri incelendikten sonra `app/inference.py` güvenli bir adaptöre bağlanacaktır.

## Streamlit Community Cloud

Entry point:

```text
app/streamlit_app.py
```

Deployment öncesinde model artifact boyutu ve erişim yöntemi ayrıca kontrol edilmelidir. Büyük model dosyaları veya özel veri setleri doğrudan repository'ye eklenmemelidir.

## Durum

UI scaffold hazırdır. Sonraki entegrasyon adımı, araştırma kodundaki doğrulanmış inference giriş noktasını ve final artifact şemalarını bağlamaktır.
