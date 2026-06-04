from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "BTKeepAlive"
PRESETS = ("white", "pink", "brown", "blue", "violet", "silent", "binaural40")
CARRIER_OPTIONS = (100, 150, 200, 250, 300)
KEEPALIVE_MODE_CONTINUOUS = "continuous"
KEEPALIVE_MODE_PULSE = "pulse"
KEEPALIVE_MODES = (KEEPALIVE_MODE_CONTINUOUS, KEEPALIVE_MODE_PULSE)
# Short quiet burst before typical ~60s BT sleep (see SoundKeeper).
PULSE_DURATION_SEC = 1.0
PULSE_INTERVAL_SEC = 55.0
PULSE_AMPLITUDE = 0.0001
# Tray shortcuts only; config accepts any value in (0, 1].
VOLUME_PRESETS = (0.0001, 0.001, 0.005, 0.01, 0.02, 0.05, 0.08, 0.12, 0.2)
VOLUME_QUICK_PRESETS = (0.01, 0.02, 0.05)
VOLUME_OPTIONS = VOLUME_PRESETS  # backwards compatibility

DEFAULT_CONFIG: dict[str, Any] = {
    "preset": "brown",
    "volume": 0.02,
    "carrier_hz": 200,
    "sample_rate": 44100,
    # Approximate audio callback duration in seconds (capped when opening stream).
    "buffer_seconds": 0.012,
    "keepalive_mode": KEEPALIVE_MODE_CONTINUOUS,
    "pulse_duration_sec": PULSE_DURATION_SEC,
    "pulse_interval_sec": PULSE_INTERVAL_SEC,
    "pulse_amplitude": PULSE_AMPLITUDE,
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


def format_volume_label(vol: float, *, for_input: bool = False) -> str:
    """Human-readable percent string; `for_input` omits the % suffix for the dialog."""
    pct = float(vol) * 100
    if for_input:
        if pct >= 1:
            return f"{pct:g}"
        return f"{pct:.6f}".rstrip("0").rstrip(".")
    body = f"{pct:.4f}".rstrip("0").rstrip(".")
    return f"{body}%"


def normalize_volume(volume: float) -> float:
    """Clamp invalid values to the default; otherwise keep the exact gain."""
    try:
        vol = float(volume)
    except (TypeError, ValueError):
        return float(DEFAULT_CONFIG["volume"])
    if vol <= 0 or vol > 1:
        return float(DEFAULT_CONFIG["volume"])
    return vol


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
    if merged.get("keepalive_mode") not in KEEPALIVE_MODES:
        merged["keepalive_mode"] = DEFAULT_CONFIG["keepalive_mode"]
    try:
        merged["pulse_duration_sec"] = max(
            0.1, float(merged.get("pulse_duration_sec", PULSE_DURATION_SEC))
        )
        merged["pulse_interval_sec"] = max(
            merged["pulse_duration_sec"] + 1.0,
            float(merged.get("pulse_interval_sec", PULSE_INTERVAL_SEC)),
        )
        amp = float(merged.get("pulse_amplitude", PULSE_AMPLITUDE))
        merged["pulse_amplitude"] = min(max(amp, 1e-6), 0.01)
    except (TypeError, ValueError):
        merged["pulse_duration_sec"] = PULSE_DURATION_SEC
        merged["pulse_interval_sec"] = PULSE_INTERVAL_SEC
        merged["pulse_amplitude"] = PULSE_AMPLITUDE
    if merged["carrier_hz"] not in CARRIER_OPTIONS:
        merged["carrier_hz"] = DEFAULT_CONFIG["carrier_hz"]
    merged["volume"] = normalize_volume(merged.get("volume", DEFAULT_CONFIG["volume"]))
    return merged


def save_config(config: dict[str, Any]) -> None:
    path = config_path()
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    tmp.replace(path)
