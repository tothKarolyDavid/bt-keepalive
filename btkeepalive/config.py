from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "BTKeepAlive"
PRESETS = ("white", "pink", "brown", "blue", "violet", "binaural40")
CARRIER_OPTIONS = (100, 150, 200, 250, 300)
VOLUME_OPTIONS = (0.005, 0.01, 0.02, 0.05, 0.08, 0.12, 0.2)

DEFAULT_CONFIG: dict[str, Any] = {
    "preset": "brown",
    "volume": 0.02,
    "carrier_hz": 200,
    "sample_rate": 44100,
    "buffer_seconds": 2,
    "autoplay": True,
    "launch_at_startup": False,
    "playing": True,
}


def config_dir() -> Path:
    base = os.environ.get("APPDATA")
    if not base:
        base = str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return deepcopy(DEFAULT_CONFIG)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return deepcopy(DEFAULT_CONFIG)
    merged = deepcopy(DEFAULT_CONFIG)
    merged.update(data)
    if merged["preset"] not in PRESETS:
        merged["preset"] = DEFAULT_CONFIG["preset"]
    if merged["carrier_hz"] not in CARRIER_OPTIONS:
        merged["carrier_hz"] = DEFAULT_CONFIG["carrier_hz"]
    try:
        volume = float(merged["volume"])
    except (TypeError, ValueError):
        volume = DEFAULT_CONFIG["volume"]
    if volume <= 0 or volume > 1:
        volume = DEFAULT_CONFIG["volume"]
    merged["volume"] = min(VOLUME_OPTIONS, key=lambda v: abs(v - volume))
    return merged


def save_config(config: dict[str, Any]) -> None:
    path = config_path()
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    tmp.replace(path)
