from __future__ import annotations

from app.document_parser import get_document_stats, split_paragraphs


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
