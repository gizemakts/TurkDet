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


def _normalize_pdf_page_text(text: str) -> str:
    """Normalize PDF hard line breaks without pretending to perform OCR.

    PDFs often store visually continuous text as many independent drawing
    fragments. Layout extraction improves reading order, but list-heavy PDFs can
    still contain artificial blank lines between fragments. When a page clearly
    looks like a numbered list, reconstruct each numbered item as one paragraph.
    Otherwise preserve real blank-line paragraph boundaries and only join wrapped
    lines inside each block.
    """
    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u00a0", " ")
        .strip()
    )
    if not normalized:
        return ""

    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]
    nonempty = [line for line in lines if line]
    if not nonempty:
        return ""

    flattened = " ".join(nonempty)
    flattened = re.sub(r"\s+", " ", flattened).strip()

    # Typical bibliography/directory pages (1. ..., 2. ..., 3. ...) are often
    # fragmented into separate PDF text objects. Rebuild those items so words
    # such as "Gazi / Eğitim / Fakültesi / Dergisi" do not become fake paragraphs.
    numbered_markers = list(re.finditer(r"(?<!\w)\d{1,3}\.\s+(?=\S)", flattened))
    if len(numbered_markers) >= 2:
        chunks = [
            chunk.strip()
            for chunk in re.split(r"(?=(?<!\w)\d{1,3}\.\s+(?=\S))", flattened)
            if chunk.strip()
        ]
        if chunks:
            return "\n\n".join(chunks)

    blocks = re.split(r"\n\s*\n+", normalized)
    cleaned_blocks: list[str] = []
    for block in blocks:
        block_lines = [
            re.sub(r"[ \t]+", " ", line).strip()
            for line in block.splitlines()
            if line.strip()
        ]
        if not block_lines:
            continue

        joined = ""
        for line in block_lines:
            if not joined:
                joined = line
                continue
            # Rejoin ordinary line wrapping. If a PDF split a hyphenated word at
            # the line boundary, avoid inserting an additional space.
            if joined.endswith("-") and re.match(r"^[a-zçğıöşü]", line):
                joined = joined[:-1] + line
            else:
                joined += " " + line
        cleaned_blocks.append(joined.strip())

    return "\n\n".join(cleaned_blocks)


def _extract_pdf_page_text(page) -> str:
    """Prefer pypdf's layout-aware extraction, with a safe plain fallback."""
    try:
        text = page.extract_text(extraction_mode="layout") or ""
    except (TypeError, ValueError, NotImplementedError):
        text = page.extract_text() or ""
    return _normalize_pdf_page_text(text)


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
            page_texts = [_extract_pdf_page_text(page) for page in reader.pages]
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
