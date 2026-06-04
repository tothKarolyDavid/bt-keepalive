"""Pulse interval dialog on a worker thread (same pattern as volume)."""

from __future__ import annotations

import threading
from collections.abc import Callable

from btkeepalive.win_pulse_dialog import prompt_pulse_interval_dialog


def request_pulse_interval_change(
    current_sec: float,
    on_result: Callable[[float | None], None],
) -> None:
    def worker() -> None:
        try:
            result = prompt_pulse_interval_dialog(current_sec)
        except Exception:
            result = None
        on_result(result)

    threading.Thread(target=worker, name="pulse-dialog", daemon=True).start()
