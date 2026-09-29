"""Premium bidirectional document uploader used by the TürkDet interface."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "turkdet_document_uploader",
    path=str(Path(__file__).resolve().parent / "frontend"),
)

_ALLOWED_EXTENSIONS = {".txt", ".docx", ".pdf"}


@dataclass(frozen=True)
class DocumentUploadEvent:
    """A validated event returned by the browser-side uploader."""

    kind: str
    name: str = ""
    data: bytes = b""
    size: int = 0
    mime_type: str = ""
    message: str = ""


def document_uploader(
    *,
    theme_mode: str,
    selected_name: str = "",
    selected_size: int = 0,
    max_size_mb: int = 10,
    key: str,
) -> DocumentUploadEvent | None:
    """Render TürkDet's uploader and return a validated selection/clear event."""

    result = _COMPONENT(
        theme_mode="dark" if theme_mode == "dark" else "light",
        accepted_extensions=sorted(_ALLOWED_EXTENSIONS),
        max_size_mb=max_size_mb,
        selected_name=selected_name,
        selected_size=int(selected_size or 0),
        default=None,
        key=key,
    )

    if not isinstance(result, dict):
        return None

    action = str(result.get("action") or "")
    if action == "cleared":
        return DocumentUploadEvent(kind="cleared")
    if action != "selected":
        return None

    name = str(result.get("name") or "").strip()
    mime_type = str(result.get("mime_type") or "")
    encoded = result.get("data_base64")

    try:
        reported_size = int(result.get("size") or 0)
    except (TypeError, ValueError):
        reported_size = 0

    suffix = Path(name).suffix.lower()
    if not name or suffix not in _ALLOWED_EXTENSIONS:
        return DocumentUploadEvent(
            kind="error",
            message="Yalnızca TXT, DOCX veya PDF dosyaları yüklenebilir.",
        )

    max_bytes = max_size_mb * 1024 * 1024
    if reported_size > max_bytes:
        return DocumentUploadEvent(
            kind="error",
            message=f"Dosya boyutu {max_size_mb} MB sınırını aşıyor.",
        )

    if not isinstance(encoded, str) or not encoded:
        return DocumentUploadEvent(
            kind="error",
            message="Dosya tarayıcıdan okunamadı. Lütfen yeniden seçin.",
        )

    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        return DocumentUploadEvent(
            kind="error",
            message="Dosya verisi doğrulanamadı. Lütfen yeniden seçin.",
        )

    if len(data) > max_bytes:
        return DocumentUploadEvent(
            kind="error",
            message=f"Dosya boyutu {max_size_mb} MB sınırını aşıyor.",
        )

    return DocumentUploadEvent(
        kind="selected",
        name=name,
        data=data,
        size=len(data),
        mime_type=mime_type,
    )
