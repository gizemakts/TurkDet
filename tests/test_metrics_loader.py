from __future__ import annotations

import json

from app.metrics_loader import _load_json


def test_missing_json_is_pending(tmp_path):
    result = _load_json(tmp_path / "missing.json")
    assert result.available is False
    assert result.data == {}


def test_json_object_loads(tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps({"auc": 0.95}), encoding="utf-8")
    result = _load_json(path)
    assert result.available is True
    assert result.data["auc"] == 0.95


def test_non_object_json_is_rejected(tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text("[]", encoding="utf-8")
    result = _load_json(path)
    assert result.available is False
