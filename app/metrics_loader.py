"""Machine-readable metrics and benchmark artifact loaders."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS_PATH = PROJECT_ROOT / "artifacts" / "final_metrics.json"
DEFAULT_BENCHMARK_PATH = PROJECT_ROOT / "artifacts" / "benchmark.json"


@dataclass(frozen=True)
class ArtifactLoadResult:
    available: bool
    path: Path
    data: dict[str, Any]
    message: str


def _resolve_path(env_name: str, default: Path) -> Path:
    raw = os.getenv(env_name, "").strip()
    return Path(raw).expanduser() if raw else default


def _load_json(path: Path) -> ArtifactLoadResult:
    if not path.is_file():
        return ArtifactLoadResult(False, path, {}, "Artifact henüz mevcut değil.")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ArtifactLoadResult(False, path, {}, f"Artifact okunamadı: {exc}")

    if not isinstance(payload, dict):
        return ArtifactLoadResult(False, path, {}, "Artifact kökü JSON nesnesi olmalıdır.")

    return ArtifactLoadResult(True, path, payload, "Artifact başarıyla yüklendi.")


def load_final_metrics() -> ArtifactLoadResult:
    path = _resolve_path("TURKDET_METRICS_PATH", DEFAULT_METRICS_PATH)
    return _load_json(path)


def load_benchmark() -> ArtifactLoadResult:
    path = _resolve_path("TURKDET_BENCHMARK_PATH", DEFAULT_BENCHMARK_PATH)
    return _load_json(path)
