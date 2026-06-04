"""Parse and prompt for playback volume (percent or 0–1 fraction)."""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable

from btkeepalive.config import DEFAULT_CONFIG


def parse_volume_percent(text: str) -> float | None:
    """Parse input for a field labeled with % (1 → 1%, 0.5 → 0.5%)."""
    raw = text.strip()
    if not raw:
        return None
    cleaned = raw.replace("%", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value <= 0 or value > 100:
        return None
    return value / 100.0


def parse_volume_text(text: str) -> float | None:
    """Parse free-form input; returns linear gain in (0, 1] or None if invalid."""
    raw = text.strip()
    if not raw:
        return None
    has_percent = "%" in raw
    cleaned = raw.replace("%", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if has_percent:
        gain = value / 100.0
    elif 0 < value < 1:
        gain = value
    elif value >= 1:
        gain = value / 100.0
    else:
        return None
    if gain <= 0 or gain > 1:
        return None
    return gain


def prompt_volume_change(
    current: float,
    on_preview: Callable[[float], None] | None = None,
) -> float | None:
    """Show a dialog on the current thread (use from a worker thread only)."""
    if sys.platform != "win32":
        return None

    from btkeepalive.win_volume_dialog import prompt_volume_dialog

    return prompt_volume_dialog(current, on_preview=on_preview)


def request_volume_change(
    current: float,
    on_result: Callable[[float | None], None],
    on_preview: Callable[[float], None] | None = None,
) -> None:
    """Open the volume dialog without blocking the tray icon message loop."""

    def worker() -> None:
        try:
            result = prompt_volume_change(current, on_preview=on_preview)
        except Exception:
            result = None
        on_result(result)

    threading.Thread(target=worker, name="volume-dialog", daemon=True).start()


def default_volume() -> float:
    return float(DEFAULT_CONFIG["volume"])
