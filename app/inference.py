"""Side-effect-free inference interface for TürkDet."""

from __future__ import annotations

from dataclasses import dataclass

from . import result_ui_overrides as _result_ui_overrides  # noqa: F401
from .model_loader import get_model_status


class InferenceUnavailableError(RuntimeError):
    """Raised when production inference has not been safely connected yet."""


@dataclass(frozen=True)
class Prediction:
    label: str
    ai_probability: float
    threshold: float


def predict_text(text: str) -> Prediction:
    """Run TürkDet inference when a validated production adapter is available.

    No fallback heuristic or fabricated probability is used. This is deliberate:
    the research UI must never present synthetic detector outputs as model results.
    """
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Analiz için boş olmayan bir metin gerekli.")

    status = get_model_status()
    if not status.available:
        raise InferenceUnavailableError(status.message)

    raise InferenceUnavailableError(
        "Model artifact mevcut, ancak mevcut araştırma kodundaki doğrulanmış inference "
        "giriş noktası henüz bu adaptöre bağlanmadı."
    )
