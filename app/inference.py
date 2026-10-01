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


# Install result-only layout refinements after the base result overrides are in
# place. This keeps the main input layout untouched.
from .result_layout_spacing import install_result_layout_spacing as _install_result_layout_spacing

_install_result_layout_spacing()


# Keep the input-mode selector sticky when the selected segment is clicked again
# and normalize the public-facing score label without changing model behavior.
from .input_behavior_fixes import install_input_behavior_fixes as _install_input_behavior_fixes

_install_input_behavior_fixes()


# Install Streamlit-only persistence after the inference API above exists. This
# keeps the visible analysis stable when the theme toggle reruns the app while
# preserving the same analyzed input and cached report output.
from .analysis_persistence import install_analysis_persistence as _install_analysis_persistence

_install_analysis_persistence()
