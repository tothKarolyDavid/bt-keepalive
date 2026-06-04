from __future__ import annotations

import sys
import threading

from btkeepalive import __version__
from btkeepalive.app_log import log_audio_error, log_error, log_info
from btkeepalive.config import config_dir, load_config, save_config
from btkeepalive.single_instance import acquire
from btkeepalive.startup import is_startup_enabled, set_startup_enabled
from btkeepalive.stream import AudioStream
from btkeepalive.tray_ui import TrayApp


class Application:
    def __init__(self, *, no_autoplay: bool = False) -> None:
        self._config = load_config()
        if no_autoplay:
            self._config["autoplay"] = False
        self._config_lock = threading.Lock()
        self._audio = AudioStream(self._get_config_safe, on_error=self._log_audio_error)
        self._tray: TrayApp | None = None

    def _log_audio_error(self, message: str) -> None:
        log_audio_error(message)

    def _get_config_safe(self) -> dict:
        with self._config_lock:
            return dict(self._config)

    def _preview_volume(self, volume: float) -> None:
        """Hear volume changes while the dialog slider moves; does not save."""
        self._audio.set_volume(float(volume))

    def _set_volume(self, volume: float) -> None:
        """Update volume only — never touch the audio stream or tray menu tree."""
        snapshot: dict | None = None
        with self._config_lock:
            if abs(float(self._config.get("volume", 0)) - volume) < 1e-9:
                return
            self._config["volume"] = volume
            snapshot = dict(self._config)
        self._audio.set_volume(volume)
        if snapshot is not None:
            threading.Thread(target=save_config, args=(snapshot,), daemon=True).start()

    def _update_config(self, config: dict) -> None:
        restart_stream = False
        playing: bool | None = None
        startup_change: bool | None = None
        snapshot: dict | None = None
        mode_changed = False
        old_startup = False
        with self._config_lock:
            old_startup = self._config.get("launch_at_startup", False)
            old_sample_rate = self._config.get("sample_rate")
            old_keepalive_mode = self._config.get("keepalive_mode")
            self._config.update(config)

            startup = self._config.get("launch_at_startup", False)
            if startup != old_startup:
                if getattr(sys, "frozen", False):
                    startup_change = startup
                else:
                    self._config["launch_at_startup"] = False

            if self._config.get("sample_rate") != old_sample_rate:
                restart_stream = True

            playing = self._config.get("playing", True)
            snapshot = dict(self._config)
            mode_changed = self._config.get("keepalive_mode") != old_keepalive_mode

        if mode_changed:
            self._audio.reset_pulse_phase()
        if startup_change is not None:
            ok = set_startup_enabled(startup_change)
            if not ok:
                with self._config_lock:
                    self._config["launch_at_startup"] = old_startup
                snapshot = dict(self._config)
                log_error("startup registry update failed")
        if snapshot is not None:
            threading.Thread(target=save_config, args=(snapshot,), daemon=True).start()

        if restart_stream:
            self._audio.stop()
        if playing:
            if restart_stream or not self._audio.is_running():
                try:
                    self._audio.start()
                except Exception as exc:
                    log_error("stream restart failed: %s (see audio-errors.log)", exc)
        else:
            self._audio.stop()

    def _sync_startup_registry(self) -> None:
        if not getattr(sys, "frozen", False):
            return
        enabled = self._config.get("launch_at_startup", False)
        if enabled:
            if not set_startup_enabled(True):
                with self._config_lock:
                    self._config["launch_at_startup"] = False
                log_error("startup registry sync failed on launch")
        elif is_startup_enabled():
            set_startup_enabled(False)

    def run(self) -> int:
        if not acquire():
            log_info("second instance blocked")
            return 0

        log_info("starting BT KeepAlive %s", __version__)
        self._sync_startup_registry()

        if self._config.get("autoplay", True) and self._config.get("playing", True):
            try:
                self._audio.start()
            except Exception as exc:
                log_error(
                    "initial audio start failed: %s (see %s)",
                    exc,
                    config_dir() / "audio-errors.log",
                )
                print(f"Failed to start audio: {exc}", file=sys.stderr)
                return 1

        self._tray = TrayApp(
            get_config=self._get_config_safe,
            update_config=self._update_config,
            set_volume=self._set_volume,
            preview_volume=self._preview_volume,
            on_quit=self._shutdown,
        )
        self._tray.run()
        return 0

    def _shutdown(self) -> None:
        log_info("shutting down")
        self._audio.stop()
