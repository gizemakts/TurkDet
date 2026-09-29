"""Document ingestion helpers for the TürkDet web interface.

This module only extracts text and lightweight document statistics. It does not
run detector inference, OCR, training, calibration, or any research pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re


class DocumentParseError(ValueError):
    """Raised when an uploaded document cannot be converted to usable text."""


@dataclass(frozen=True)
class DocumentStats:
    characters: int
    words: int
    paragraphs: int
    sentences_approx: int


def split_paragraphs(text: str) -> list[str]:
    """Split text into non-empty paragraphs while preserving paragraph content."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks = re.split(r"\n\s*\n+", normalized)
    paragraphs: list[str] = []
    for block in blocks:
        cleaned = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def get_document_stats(text: str) -> DocumentStats:
    """Return presentation-only document counts.

    Sentence count is intentionally marked approximate in the UI because this
    lightweight regex is not a linguistic sentence segmenter.
    """
    cleaned = text.strip()
    paragraphs = split_paragraphs(cleaned)
    words = re.findall(r"\S+", cleaned)
    sentence_marks = re.findall(r"[.!?…]+(?=\s|$)", cleaned)
    sentence_count = len(sentence_marks)
    if cleaned and sentence_count == 0:
        sentence_count = 1

    return DocumentStats(
        characters=len(cleaned),
        words=len(words),
        paragraphs=len(paragraphs),
        sentences_approx=sentence_count,
    )


def _decode_text_file(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise DocumentParseError("Metin dosyasının karakter kodlaması okunamadı.")


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from a supported uploaded file.

    Supported formats: .txt, .docx, .pdf. PDF extraction expects an existing
    text layer; scanned/image-only PDFs are deliberately not OCR'd here.
    """
    if not content:
        raise DocumentParseError("Yüklenen dosya boş.")

    suffix = Path(filename).suffix.lower()

    if suffix == ".txt":
        text = _decode_text_file(content)

    elif suffix == ".docx":
        try:
            from docx import Document

            document = Document(BytesIO(content))
            text = "\n\n".join(
                paragraph.text.strip()
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            )
        except Exception as exc:  # library errors differ by malformed input
            raise DocumentParseError("DOCX dosyası okunamadı.") from exc

    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
            text = "\n\n".join(page_text for page_text in page_texts if page_text)
        except Exception as exc:  # encrypted/corrupt PDFs surface varied errors
            raise DocumentParseError("PDF dosyası okunamadı.") from exc
        if not text.strip():
            raise DocumentParseError(
                "PDF içinde okunabilir bir metin katmanı bulunamadı. "
                "Taranmış PDF'ler için OCR desteği henüz etkin değil."
            )

    else:
        raise DocumentParseError("Desteklenmeyen dosya türü. TXT, DOCX veya PDF yükleyin.")

    cleaned = text.strip()
    if not cleaned:
        raise DocumentParseError("Belgeden analiz edilebilir metin çıkarılamadı.")
    return cleaned
