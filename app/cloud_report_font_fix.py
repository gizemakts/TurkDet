"""Cloud-safe PDF font fallback for TürkDet reports."""

from __future__ import annotations

from pathlib import Path

import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app import report_pdf


def _cloud_safe_register_fonts() -> tuple[str, str]:
    """Always provide an embedded font with Turkish glyph coverage."""

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


if not hasattr(report_pdf, "_original_register_fonts"):
    report_pdf._original_register_fonts = report_pdf._register_fonts
    report_pdf._register_fonts = _cloud_safe_register_fonts
