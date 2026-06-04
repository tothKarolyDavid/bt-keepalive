from __future__ import annotations

import functools
import sys
from collections.abc import Callable

import pystray
from PIL import Image

from btkeepalive.config import (
    CARRIER_OPTIONS,
    KEEPALIVE_MODE_CONTINUOUS,
    KEEPALIVE_MODE_PULSE,
    PRESETS,
    PULSE_INTERVAL_SEC,
    VOLUME_PRESETS,
    format_volume_label,
)
from btkeepalive.icon_art import render_icon
from btkeepalive.volume_input import request_volume_change
from btkeepalive.win_tray import create_tray_icon

PRESET_LABELS = {
    "white": "White noise",
    "pink": "Pink noise",
    "brown": "Brown noise",
    "blue": "Blue noise",
    "violet": "Violet noise",
    "binaural40": "40 Hz binaural",
}


def _volume_matches(vol: float, target: float) -> bool:
    return abs(float(vol) - float(target)) < 1e-9


def _make_icon(active: bool) -> Image.Image:
    return render_icon(active=active, size=64)


class TrayApp:
    def __init__(
        self,
        get_config: Callable[[], dict],
        update_config: Callable[[dict], None],
        on_quit: Callable[[], None],
        set_volume: Callable[[float], None] | None = None,
        preview_volume: Callable[[float], None] | None = None,
    ) -> None:
        self._get_config = get_config
        self._update_config = update_config
        self._set_volume_only = set_volume
        self._preview_volume_only = preview_volume
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None

    def _sync_title(self) -> None:
        if self._icon is None:
            return
        cfg = self._get_config()
        state = "Playing" if cfg.get("playing", True) else "Paused"
        if cfg.get("keepalive_mode") == KEEPALIVE_MODE_PULSE:
            interval = int(float(cfg.get("pulse_interval_sec", PULSE_INTERVAL_SEC)))
            self._icon.title = (
                f"BT KeepAlive: Pulse keepalive every {interval}s ({state})"
            )
            return
        preset = cfg.get("preset", "brown")
        label = PRESET_LABELS.get(preset, preset)
        vol = format_volume_label(float(cfg.get("volume", 0.02)))
        self._icon.title = f"BT KeepAlive: {label}, {vol} ({state})"

    def _refresh_icon(self) -> None:
        if self._icon is None:
            return
        cfg = self._get_config()
        self._icon.icon = _make_icon(cfg.get("playing", True))

    def _set_playing(self, playing: bool) -> None:
        cfg = self._get_config()
        cfg["playing"] = playing
        self._update_config(cfg)
        self._refresh_icon()
        self._sync_title()

    def _toggle_playing(self) -> None:
        cfg = self._get_config()
        self._set_playing(not cfg.get("playing", True))

    def _action_preset(self, preset: str, _icon, _item) -> None:
        self._set_preset(preset)

    def _action_volume(self, volume: float, _icon, _item) -> None:
        self._set_volume(volume)

    def _adjust_volume_label(self) -> str:
        vol = float(self._get_config().get("volume", 0.02))
        return f"Adjust volume… ({format_volume_label(vol)})"

    def _action_set_volume(self, _icon, _item) -> None:
        current = float(self._get_config().get("volume", 0.02))

        def apply(new_volume: float | None) -> None:
            if new_volume is not None:
                self._set_volume(new_volume)

        request_volume_change(
            current,
            apply,
            on_preview=self._preview_volume_only,
        )

    def _action_carrier(self, carrier_hz: int, _icon, _item) -> None:
        cfg = self._get_config()
        cfg["carrier_hz"] = carrier_hz
        self._update_config(cfg)
        self._sync_title()

    def _set_preset(self, preset: str) -> None:
        cfg = self._get_config()
        if (
            cfg.get("preset") == preset
            and cfg.get("keepalive_mode") == KEEPALIVE_MODE_CONTINUOUS
        ):
            return
        cfg["preset"] = preset
        cfg["keepalive_mode"] = KEEPALIVE_MODE_CONTINUOUS
        self._update_config(cfg)
        self._sync_title()

    def _set_volume(self, volume: float) -> None:
        if self._set_volume_only is not None:
            self._set_volume_only(volume)
            self._sync_title()
            return
        cfg = self._get_config()
        cfg["volume"] = volume
        self._update_config(cfg)
        self._sync_title()

    def _is_inaudible_profile(self) -> bool:
        return self._get_config().get("keepalive_mode") == KEEPALIVE_MODE_PULSE

    def _toggle_inaudible(self) -> None:
        cfg = self._get_config()
        if self._is_inaudible_profile():
            cfg["keepalive_mode"] = KEEPALIVE_MODE_CONTINUOUS
        else:
            cfg["keepalive_mode"] = KEEPALIVE_MODE_PULSE
        self._update_config(cfg)
        self._sync_title()

    def _toggle_startup(self) -> None:
        cfg = self._get_config()
        cfg["launch_at_startup"] = not cfg.get("launch_at_startup", False)
        self._update_config(cfg)

    def _build_menu(self) -> pystray.Menu:
        sound_items = [
            pystray.MenuItem(
                PRESET_LABELS[p],
                functools.partial(self._action_preset, p),
                checked=lambda item, preset=p: (
                    self._get_config().get("preset", "brown") == preset
                    and self._get_config().get("keepalive_mode")
                    == KEEPALIVE_MODE_CONTINUOUS
                ),
                radio=True,
            )
            for p in PRESETS
        ]

        volume_items = [
            pystray.MenuItem(
                lambda item: self._adjust_volume_label(),
                self._action_set_volume,
            ),
            pystray.Menu.SEPARATOR,
            *[
                pystray.MenuItem(
                    format_volume_label(vol),
                    functools.partial(self._action_volume, vol),
                    checked=lambda item, volume=vol: _volume_matches(
                        self._get_config().get("volume", 0.02), volume
                    ),
                    radio=True,
                )
                for vol in VOLUME_PRESETS
            ],
        ]

        carrier_items = [
            pystray.MenuItem(
                f"{hz} Hz",
                functools.partial(self._action_carrier, hz),
                checked=lambda item, carrier_hz=hz: (
                    self._get_config().get("carrier_hz", 200) == carrier_hz
                ),
                radio=True,
            )
            for hz in CARRIER_OPTIONS
        ]

        return pystray.Menu(
            pystray.MenuItem(
                lambda item: (
                    "Pause" if self._get_config().get("playing", True) else "Play"
                ),
                lambda _: self._toggle_playing(),
            ),
            pystray.MenuItem(
                "Pulse keepalive",
                lambda _: self._toggle_inaudible(),
                checked=lambda item: self._is_inaudible_profile(),
            ),
            pystray.MenuItem("Sound", pystray.Menu(*sound_items)),
            pystray.MenuItem("Volume", pystray.Menu(*volume_items)),
            pystray.MenuItem("Binaural carrier", pystray.Menu(*carrier_items)),
            pystray.MenuItem(
                "Launch at startup",
                lambda _: self._toggle_startup(),
                checked=lambda item: self._get_config().get("launch_at_startup", False),
                enabled=lambda item: getattr(sys, "frozen", False),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda _: self._quit()),
        )

    def _quit(self) -> None:
        if self._icon:
            self._icon.stop()
        self._on_quit()

    def _on_setup(self, icon: pystray.Icon) -> None:
        icon.visible = True
        self._sync_title()

    def run(self) -> None:
        cfg = self._get_config()
        self._icon = create_tray_icon(
            "BTKeepAlive",
            _make_icon(cfg.get("playing", True)),
            "BT KeepAlive",
            menu=self._build_menu(),
        )
        self._icon.run(setup=self._on_setup)
