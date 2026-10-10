"""PDF report generation for TürkDet analysis results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ACCENT = colors.HexColor("#6366F1")
INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#667085")
BORDER = colors.HexColor("#E4E7EC")
SOFT = colors.HexColor("#F8FAFC")
ACCENT_SOFT = colors.HexColor("#EEF2FF")
WARNING_SOFT = colors.HexColor("#FFFAEB")
WARNING_INK = colors.HexColor("#92400E")


@dataclass(frozen=True)
class AnalysisReport:
    pdf_bytes: bytes
    report_id: str
    input_sha256: str
    file_name: str
    generated_at: datetime


def _first_existing(candidates: list[str]) -> str | None:
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return None


def _register_fonts() -> tuple[str, str]:
    regular = _first_existing(
        [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    )
    bold = _first_existing(
        [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]
    )
    if regular:
        if "TurkDetSans" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("TurkDetSans", regular))
        if bold and "TurkDetSansBold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("TurkDetSansBold", bold))
        return "TurkDetSans", "TurkDetSansBold" if bold else "TurkDetSans"
    return "Helvetica", "Helvetica-Bold"


def _safe_filename(source_name: str, generated_at: datetime) -> str:
    stem = Path(source_name).stem if source_name else "metin"
    stem = re.sub(r"[^0-9A-Za-zÇĞİÖŞÜçğıöşü_-]+", "_", stem).strip("_") or "metin"
    return f"TurkDet_Raporu_{stem}_{generated_at:%Y%m%d_%H%M%S}.pdf"


def _hash_input(text: str, source_bytes: bytes | None) -> str:
    payload = source_bytes if source_bytes else text.encode("utf-8")
    return sha256(payload).hexdigest()


def _paragraph_blocks(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    blocks = re.split(r"\n\s*\n+", normalized)
    output: list[str] = []
    for block in blocks:
        collapsed = re.sub(r"[ \t]*\n[ \t]*", " ", block)
        collapsed = re.sub(r"[ \t]+", " ", collapsed).strip()
        if collapsed:
            output.append(collapsed)
    return output


def _build_styles(font_regular: str, font_bold: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "brand",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=11,
            leading=14,
            textColor=ACCENT,
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=font_bold,
            fontSize=24,
            leading=29,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName=font_regular,
            fontSize=9.2,
            leading=13,
            textColor=MUTED,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontName=font_bold,
            fontSize=12.5,
            leading=16,
            textColor=INK,
            spaceBefore=2 * mm,
            spaceAfter=3 * mm,
        ),
        "result": ParagraphStyle(
            "result",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=14,
            leading=18,
            textColor=INK,
        ),
        "score": ParagraphStyle(
            "score",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=24,
            leading=28,
            textColor=ACCENT,
            alignment=TA_CENTER,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontName=font_regular,
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=font_regular,
            fontSize=9.5,
            leading=14.3,
            textColor=INK,
            spaceAfter=3.2 * mm,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=7.6,
            leading=10,
            textColor=MUTED,
        ),
        "value": ParagraphStyle(
            "value",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=10,
            leading=13,
            textColor=INK,
        ),
        "note": ParagraphStyle(
            "note",
            parent=base["Normal"],
            fontName=font_regular,
            fontSize=8.4,
            leading=12,
            textColor=WARNING_INK,
        ),
    }


def build_analysis_report(
    *,
    text: str,
    source_name: str,
    words: int,
    paragraphs: int,
    sentences_approx: int,
    characters: int,
    result_message: str,
    ai_probability: float | None,
    model_available: bool,
    source_bytes: bytes | None = None,
    status_note: str | None = None,
    generated_at: datetime | None = None,
) -> AnalysisReport:
    """Build a fixed-layout PDF report without inventing unavailable model output."""

    generated_at = generated_at or datetime.now().astimezone()
    input_hash = _hash_input(text, source_bytes)
    report_id = f"TD-{generated_at:%Y%m%d-%H%M%S}-{input_hash[:8].upper()}"
    file_name = _safe_filename(source_name, generated_at)
    font_regular, font_bold = _register_fonts()
    styles = _build_styles(font_regular, font_bold)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title="TürkDet Analiz Raporu",
        author="TürkDet",
        subject="Türkçe yapay zekâ metin analizi raporu",
    )

    story = []
    brand = Table(
        [[
            Paragraph("<b>TD</b>", ParagraphStyle("mark", fontName=font_bold, fontSize=11, textColor=colors.white, alignment=TA_CENTER, leading=15)),
            Paragraph("TürkDet", styles["brand"]),
        ]],
        colWidths=[10 * mm, 35 * mm],
        rowHeights=[10 * mm],
        hAlign="LEFT",
    )
    brand.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("BOX", (0, 0), (0, 0), 0, ACCENT),
    ]))
    story.append(brand)
    story.append(Spacer(1, 7 * mm))
    story.append(Paragraph("TürkDet Analiz Raporu", styles["title"]))
    story.append(Paragraph(
        "Türkçe metinlerde yapay zekâ üretimiyle uyumlu sinyalleri incelemek için oluşturulan sabit rapor.",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 6 * mm))

    meta_rows = [
        [Paragraph("BELGE", styles["label"]), Paragraph(escape(source_name or "Yapıştırılan metin"), styles["value"]),
         Paragraph("RAPOR NO", styles["label"]), Paragraph(report_id, styles["value"])],
        [Paragraph("ANALİZ TARİHİ", styles["label"]), Paragraph(generated_at.strftime("%d.%m.%Y %H:%M %z"), styles["value"]),
         Paragraph("DURUM", styles["label"]), Paragraph("Model sonucu hazır" if model_available else "Model sonucu üretilemedi", styles["value"])],
    ]
    meta = Table(meta_rows, colWidths=[24 * mm, 57 * mm, 25 * mm, 57 * mm], hAlign="LEFT")
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(meta)
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Genel sonuç", styles["section"]))
    score_text = "—" if ai_probability is None else f"%{max(0.0, min(1.0, ai_probability)) * 100:.1f}".replace(".", ",")
    score_cell = Table(
        [[Paragraph(score_text, styles["score"]), Paragraph(escape(result_message), styles["result"])]],
        colWidths=[45 * mm, 118 * mm],
    )
    score_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT if model_available else WARNING_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.8, ACCENT if model_available else colors.HexColor("#FEC84B")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_cell)
    if status_note:
        story.append(Spacer(1, 2.5 * mm))
        story.append(Paragraph(escape(status_note), styles["small"]))
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Belge özeti", styles["section"]))
    stats_table = Table(
        [[
            Paragraph("KELİME", styles["label"]),
            Paragraph("PARAGRAF", styles["label"]),
            Paragraph("YAKLAŞIK CÜMLE", styles["label"]),
            Paragraph("KARAKTER", styles["label"]),
        ], [
            Paragraph(f"{words:,}".replace(",", "."), styles["value"]),
            Paragraph(f"{paragraphs:,}".replace(",", "."), styles["value"]),
            Paragraph(f"{sentences_approx:,}".replace(",", "."), styles["value"]),
            Paragraph(f"{characters:,}".replace(",", "."), styles["value"]),
        ]],
        colWidths=[40.75 * mm] * 4,
    )
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Girdi doğrulama bilgisi", styles["section"]))
    spaced_hash = " ".join(input_hash[index:index + 16] for index in range(0, len(input_hash), 16))
    hash_table = Table(
        [[Paragraph("SHA-256", styles["label"]), Paragraph(spaced_hash, styles["small"])]],
        colWidths=[25 * mm, 138 * mm],
    )
    hash_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(hash_table)
    story.append(Spacer(1, 5 * mm))
    story.append(KeepTogether([
        Paragraph("Değerlendirme notu", styles["section"]),
        Table([[Paragraph(
            "TürkDet sonucu olasılıksal bir model çıktısıdır ve tek başına kesin yazarlık, akademik ihlal veya disiplin kararı kanıtı olarak kullanılmamalıdır. "
            "SHA-256 değeri analiz edilen girdiyi tanımlar; bu PDF henüz kriptografik olarak dijital imzalanmış değildir.",
            styles["note"],
        )]], colWidths=[163 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), WARNING_SOFT),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#FEC84B")),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])),
    ]))

    blocks = _paragraph_blocks(text)
    if blocks:
        story.append(PageBreak())
        story.append(Paragraph("Belge metni", styles["section"]))
        story.append(Paragraph(
            "Aşağıdaki içerik analiz sırasında kullanılan metnin rapor görünümüdür. Segment düzeyi skorları ayrıca doğrulanmadan gösterilmez.",
            styles["subtitle"],
        ))
        story.append(Spacer(1, 4 * mm))
        for block in blocks:
            story.append(Paragraph(escape(block), styles["body"]))

    def _footer(canvas, _doc) -> None:
        canvas.saveState()
        width, _height = A4
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(18 * mm, 12 * mm, width - 18 * mm, 12 * mm)
        canvas.setFont(font_regular, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 7.5 * mm, report_id)
        canvas.drawRightString(width - 18 * mm, 7.5 * mm, f"Sayfa {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return AnalysisReport(
        pdf_bytes=buffer.getvalue(),
        report_id=report_id,
        input_sha256=input_hash,
        file_name=file_name,
        generated_at=generated_at,
    )
