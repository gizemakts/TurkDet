"""Model artifact discovery for the TürkDet web application.

This module intentionally does not import the research/training pipeline. The
production model adapter can be connected later without creating import side
effects or retraining a model from the web app.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelStatus:
    available: bool
    path: Path | None
    message: str


def resolve_model_path() -> Path | None:
    """Return an explicitly configured model artifact path, if it exists."""
    raw_path = os.getenv("TURKDET_MODEL_PATH", "").strip()
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    return path if path.is_file() else None


def get_model_status() -> ModelStatus:
    """Describe whether a production model artifact is currently available."""
    path = resolve_model_path()
    if path is None:
        return ModelStatus(
            available=False,
            path=None,
            message=(
                "Üretim modeli henüz web uygulamasına bağlanmadı. "
                "TURKDET_MODEL_PATH ile doğrulanmış final/frozen artifact belirtildiğinde "
                "inference adaptörü etkinleştirilebilir."
            ),
        )
    return ModelStatus(
        available=True,
        path=path,
        message="Model artifact bulundu; inference adaptörü bağlantısı bekleniyor.",
    )
