from __future__ import annotations

import pytest

from app.inference import InferenceUnavailableError, predict_text


def test_blank_text_is_rejected():
    with pytest.raises(ValueError):
        predict_text("   ")


def test_no_model_never_fabricates_prediction(monkeypatch):
    monkeypatch.delenv("TURKDET_MODEL_PATH", raising=False)
    with pytest.raises(InferenceUnavailableError):
        predict_text("Bu bir test metnidir.")
