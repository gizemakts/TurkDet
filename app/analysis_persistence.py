"""Keep the last TürkDet analysis stable across theme-triggered reruns.

The Streamlit theme toggle reruns the script. This module preserves the most
recent analysis for that rerun only, so switching between dark and light mode
does not discard the visible report or rerun model inference unnecessarily.
"""

from __future__ import annotations

from hashlib import sha256
import sys

import streamlit as st

from app import report_pdf


_LAST_SIGNATURE = "_turkdet_last_analysis_signature"
_THEME_RESTORE_REQUEST = "_turkdet_theme_restore_request"
_RESTORING = "_turkdet_restoring_analysis"
_PREDICTION_CACHE = "_turkdet_prediction_cache"
_REPORT_CACHE = "_turkdet_report_cache"


def _current_input_signature() -> str:
    mode = str(st.session_state.get("input_mode") or "")

    if mode == "Belge yükle":
        text = str(st.session_state.get("uploaded_text_buffer") or "")
        name = str(st.session_state.get("uploaded_name_buffer") or "")
    else:
        text = str(
            st.session_state.get("pasted_text_buffer")
            or st.session_state.get("pasted_text_widget")
            or ""
        )
        name = ""

    if not text.strip():
        return ""

    payload = f"{mode}\x1f{name}\x1f{text}".encode("utf-8")
    return sha256(payload).hexdigest()


def _clear_analysis_cache() -> None:
    st.session_state.pop(_PREDICTION_CACHE, None)
    st.session_state.pop(_REPORT_CACHE, None)


def _install_button_persistence() -> None:
    if getattr(st.button, "_turkdet_analysis_persistence", False):
        return

    native_button = st.button

    def persistent_button(label, *args, **kwargs):
        clicked = native_button(label, *args, **kwargs)
        key = kwargs.get("key")

        if key == "theme_toggle":
            if clicked:
                st.session_state[_THEME_RESTORE_REQUEST] = True
            return clicked

        if str(label) != "Analizi Başlat":
            return clicked

        signature = _current_input_signature()

        if clicked:
            previous = st.session_state.get(_LAST_SIGNATURE)
            if previous != signature:
                _clear_analysis_cache()
            st.session_state[_LAST_SIGNATURE] = signature
            st.session_state[_RESTORING] = False
            st.session_state[_THEME_RESTORE_REQUEST] = False
            return True

        restore_requested = bool(st.session_state.pop(_THEME_RESTORE_REQUEST, False))
        prediction_cache = st.session_state.get(_PREDICTION_CACHE)
        cached_signature = (
            prediction_cache.get("signature")
            if isinstance(prediction_cache, dict)
            else None
        )
        can_restore = (
            restore_requested
            and not bool(kwargs.get("disabled", False))
            and bool(signature)
            and signature == st.session_state.get(_LAST_SIGNATURE)
            and signature == cached_signature
        )

        st.session_state[_RESTORING] = bool(can_restore)
        return bool(can_restore)

    persistent_button._turkdet_analysis_persistence = True
    st.button = persistent_button


def _install_prediction_cache(inference_module) -> None:
    native_predict = inference_module.predict_text
    if getattr(native_predict, "_turkdet_analysis_persistence", False):
        return

    def persistent_predict(text: str):
        signature = _current_input_signature()
        cache = st.session_state.get(_PREDICTION_CACHE)

        if (
            st.session_state.get(_RESTORING, False)
            and isinstance(cache, dict)
            and cache.get("signature") == signature
        ):
            kind = cache.get("kind")
            if kind == "prediction":
                return inference_module.Prediction(
                    label=str(cache["label"]),
                    ai_probability=float(cache["ai_probability"]),
                    threshold=float(cache["threshold"]),
                )
            if kind == "unavailable":
                raise inference_module.InferenceUnavailableError(str(cache.get("message") or ""))

        try:
            result = native_predict(text)
        except inference_module.InferenceUnavailableError as exc:
            if signature:
                st.session_state[_PREDICTION_CACHE] = {
                    "signature": signature,
                    "kind": "unavailable",
                    "message": str(exc),
                }
            raise
        except Exception:
            st.session_state.pop(_PREDICTION_CACHE, None)
            raise

        if signature:
            st.session_state[_PREDICTION_CACHE] = {
                "signature": signature,
                "kind": "prediction",
                "label": result.label,
                "ai_probability": result.ai_probability,
                "threshold": result.threshold,
            }
        return result

    persistent_predict._turkdet_analysis_persistence = True
    inference_module.predict_text = persistent_predict


def _install_report_cache() -> None:
    native_builder = report_pdf.build_analysis_report
    if getattr(native_builder, "_turkdet_analysis_persistence", False):
        return

    def persistent_builder(*args, **kwargs):
        signature = _current_input_signature()
        cache = st.session_state.get(_REPORT_CACHE)

        if (
            st.session_state.get(_RESTORING, False)
            and isinstance(cache, dict)
            and cache.get("signature") == signature
            and cache.get("report") is not None
        ):
            st.session_state[_RESTORING] = False
            return cache["report"]

        report = native_builder(*args, **kwargs)
        if signature:
            st.session_state[_REPORT_CACHE] = {
                "signature": signature,
                "report": report,
            }
        st.session_state[_RESTORING] = False
        return report

    persistent_builder._turkdet_analysis_persistence = True
    report_pdf.build_analysis_report = persistent_builder


def install_analysis_persistence() -> None:
    """Install one-time wrappers after app.inference has finished defining its API."""

    inference_module = sys.modules.get("app.inference")
    if inference_module is None or not hasattr(inference_module, "predict_text"):
        return

    _install_button_persistence()
    _install_prediction_cache(inference_module)
    _install_report_cache()
