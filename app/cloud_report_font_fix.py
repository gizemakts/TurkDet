"""Cloud-safe PDF typography for TürkDet reports."""

from __future__ import annotations

from copy import copy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app import report_pdf


_ISTANBUL = ZoneInfo("Europe/Istanbul")


def _cloud_safe_register_fonts() -> tuple[str, str]:
    """Always provide embedded fonts with Turkish glyph coverage."""

    package_fonts = Path(reportlab.__file__).resolve().parent / "fonts"
    regular = package_fonts / "Vera.ttf"
    bold = package_fonts / "VeraBd.ttf"

    if not regular.is_file() or not bold.is_file():
        return report_pdf._original_register_fonts()

    if "TurkDetSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("TurkDetSans", str(regular)))
    if "TurkDetSansBold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("TurkDetSansBold", str(bold)))

    return "TurkDetSans", "TurkDetSansBold"


def _cloud_safe_paragraph(text, *args, **kwargs):
    """Keep long report IDs on one line in the metadata table."""

    if isinstance(text, str) and text.startswith("TD-") and args:
        style = copy(args[0])
        style.fontSize = min(float(getattr(style, "fontSize", 10)), 8.2)
        style.leading = min(float(getattr(style, "leading", 12)), 10)
        args = (style, *args[1:])
    return report_pdf._original_paragraph(text, *args, **kwargs)


def _cloud_safe_builder(*args, **kwargs):
    """Generate report timestamps in Türkiye local time on cloud hosts."""

    if kwargs.get("generated_at") is None:
        kwargs["generated_at"] = datetime.now(_ISTANBUL)
    return report_pdf._original_build_analysis_report(*args, **kwargs)


if not hasattr(report_pdf, "_original_register_fonts"):
    report_pdf._original_register_fonts = report_pdf._register_fonts
    report_pdf._register_fonts = _cloud_safe_register_fonts

if not hasattr(report_pdf, "_original_paragraph"):
    report_pdf._original_paragraph = report_pdf.Paragraph
    report_pdf.Paragraph = _cloud_safe_paragraph

if not hasattr(report_pdf, "_original_build_analysis_report"):
    report_pdf._original_build_analysis_report = report_pdf.build_analysis_report
    report_pdf.build_analysis_report = _cloud_safe_builder
