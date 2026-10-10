from __future__ import annotations

from app.document_parser import _normalize_pdf_page_text, get_document_stats, split_paragraphs


def test_split_paragraphs_normalizes_lines() -> None:
    text = "Birinci satır\nikinci satır.\n\nİkinci paragraf."
    assert split_paragraphs(text) == [
        "Birinci satır ikinci satır.",
        "İkinci paragraf.",
    ]


def test_document_stats_counts_basic_structure() -> None:
    text = "Merhaba dünya.\n\nBu ikinci paragraf mı? Evet!"
    stats = get_document_stats(text)
    assert stats.words == 7
    assert stats.paragraphs == 2
    assert stats.sentences_approx == 3
    assert stats.characters == len(text.strip())


def test_pdf_numbered_list_fragments_are_reconstructed() -> None:
    raw = (
        "1. Fen Bilimleri Dergisi (1995)\n"
        "https://dergipark.org.tr/tr/pub/fen\n\n"
        "2. Sağlık Bilimleri Ege Tıp Dergisi (1962)\n\n"
        "3. Eğitim Bilimleri (1)\n"
        "Gazi\n\n"
        "Eğitim\n\n"
        "Fakültesi\n\n"
        "Dergisi\n\n"
        "(1985)\n\n"
        "4. Teknik/Mühendislik Dergisi (2008)"
    )
    normalized = _normalize_pdf_page_text(raw)
    paragraphs = split_paragraphs(normalized)

    assert len(paragraphs) == 4
    assert paragraphs[2] == "3. Eğitim Bilimleri (1) Gazi Eğitim Fakültesi Dergisi (1985)"
    assert paragraphs[3].startswith("4. Teknik/Mühendislik")


def test_pdf_regular_paragraph_boundaries_are_preserved() -> None:
    raw = "Birinci satır\nikinci satır.\n\nİkinci paragraf\ndevam ediyor."
    assert _normalize_pdf_page_text(raw) == (
        "Birinci satır ikinci satır.\n\nİkinci paragraf devam ediyor."
    )
