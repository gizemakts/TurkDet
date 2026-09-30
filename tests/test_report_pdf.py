from datetime import datetime, timezone
from io import BytesIO

from pypdf import PdfReader

from app.report_pdf import build_analysis_report


def _sample_report(*, ai_probability=0.42, model_available=True, result_message='Yapay zekâ üretimiyle uyumlu sinyal saptandı'):
    return build_analysis_report(
        text='Türkçe karakter testi: ç ğ ı İ ö ş ü.\n\nİkinci paragraf.',
        source_name='ornek.pdf',
        words=9,
        paragraphs=2,
        sentences_approx=2,
        characters=55,
        result_message=result_message,
        ai_probability=ai_probability,
        model_available=model_available,
        source_bytes=b'original document bytes',
        generated_at=datetime(2026, 9, 30, 20, 30, tzinfo=timezone.utc),
    )


def test_report_is_pdf_and_contains_core_fields():
    report = _sample_report()
    assert report.pdf_bytes.startswith(b'%PDF')
    assert report.report_id.startswith('TD-20260930-203000-')
    assert len(report.input_sha256) == 64
    reader = PdfReader(BytesIO(report.pdf_bytes))
    extracted = '\n'.join(page.extract_text() or '' for page in reader.pages)
    assert 'TürkDet Analiz Raporu' in extracted
    assert 'ornek.pdf' in extracted
    assert 'Belge özeti' in extracted
    assert 'SHA-256' in extracted
    assert 'Türkçe karakter testi' in extracted


def test_unavailable_model_never_invents_probability():
    report = _sample_report(
        ai_probability=None,
        model_available=False,
        result_message='Analiz sonucu üretilemedi',
    )
    reader = PdfReader(BytesIO(report.pdf_bytes))
    extracted = '\n'.join(page.extract_text() or '' for page in reader.pages)
    assert 'Analiz sonucu üretilemedi' in extracted
    assert 'Model sonucu üretilemedi' in extracted
    assert '%42' not in extracted
