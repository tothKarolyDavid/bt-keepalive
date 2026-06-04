import json

import pytest

from btkeepalive.config import (
    DEFAULT_CONFIG,
    load_config,
    normalize_volume,
    save_config,
)


def test_normalize_volume_clamps_invalid():
    assert normalize_volume(-1) == DEFAULT_CONFIG["volume"]
    assert normalize_volume(2) == DEFAULT_CONFIG["volume"]
    assert normalize_volume("x") == DEFAULT_CONFIG["volume"]


def test_normalize_volume_keeps_valid():
    assert normalize_volume(0.05) == pytest.approx(0.05)


def test_load_config_merges_defaults(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "BTKeepAlive"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.json"
    cfg_file.write_text(
        json.dumps({"volume": 0.03, "preset": "pink"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("btkeepalive.config.config_path", lambda: cfg_file)
    monkeypatch.setattr("btkeepalive.config.config_dir", lambda: cfg_dir)
    merged = load_config()
    assert merged["volume"] == pytest.approx(0.03)
    assert merged["preset"] == "pink"
    assert merged["carrier_hz"] == DEFAULT_CONFIG["carrier_hz"]


def test_load_config_corrupt_json(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "BTKeepAlive"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.json"
    cfg_file.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr("btkeepalive.config.config_path", lambda: cfg_file)
    merged = load_config()
    assert merged["preset"] == DEFAULT_CONFIG["preset"]


def test_save_config_atomic(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "BTKeepAlive"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.json"
    monkeypatch.setattr("btkeepalive.config.config_path", lambda: cfg_file)
    data = dict(DEFAULT_CONFIG)
    data["volume"] = 0.04
    save_config(data)
    loaded = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert loaded["volume"] == 0.04


def test_pulse_interval_minimum(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "BTKeepAlive"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.json"
    cfg_file.write_text(
        json.dumps({"pulse_interval_sec": 0.5, "pulse_duration_sec": 1.0}),
        encoding="utf-8",
    )
    monkeypatch.setattr("btkeepalive.config.config_path", lambda: cfg_file)
    merged = load_config()
    assert merged["pulse_interval_sec"] >= merged["pulse_duration_sec"] + 1.0
