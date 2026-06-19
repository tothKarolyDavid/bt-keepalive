from __future__ import annotations

import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd

from btkeepalive.app_log import log_error, log_info
from btkeepalive.audio.binaural import BinauralGenerator
from btkeepalive.audio.noise import NoiseGenerator
from btkeepalive.config import KEEPALIVE_MODE_PULSE
from btkeepalive.device_monitor import get_default_audio_endpoint_id


def blocksize_from_buffer_seconds(sample_rate: int, buffer_seconds: float) -> int:
    """Audio callback frame count from sample rate and target buffer duration."""
    sr = int(sample_rate)
    buf_sec = float(buffer_seconds)
    return max(64, min(8192, int(sr * buf_sec)))


def mono_to_stereo(mono: np.ndarray) -> np.ndarray:
    stereo = np.empty((mono.shape[0], 2), dtype=np.float32)
    stereo[:, 0] = mono
    stereo[:, 1] = mono
    return stereo


class AudioStream:
    def __init__(
        self,
        get_settings: Callable[[], dict],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._get_settings = get_settings
        self._on_error = on_error
        self._lock = threading.Lock()
        self._stream: sd.OutputStream | None = None
        self._noise: NoiseGenerator | None = None
        self._binaural: BinauralGenerator | None = None
        self._last_preset: str | None = None
        self._last_carrier: float | None = None
        self._last_keepalive_mode: str | None = None
        self._sample_rate: int = 44100
        self._live_volume: float = 0.02
        self._pulse_pos: int = 0
        self._monitor_thread: threading.Thread | None = None
        self._stop_monitor_event: threading.Event | None = None
        self._last_device_id: str | None = None
        self._last_error_logged: str | None = None

    def set_volume(self, volume: float) -> None:
        self._live_volume = float(volume)

    def reset_pulse_phase(self) -> None:
        self._pulse_pos = 0

    def _sync_mode(self, settings: dict) -> None:
        mode = settings.get("keepalive_mode", "continuous")
        if mode != self._last_keepalive_mode:
            self._pulse_pos = 0
            self._last_keepalive_mode = mode

    def _ensure_generators(self, settings: dict) -> None:
        preset = settings["preset"]
        sr = int(settings["sample_rate"])
        carrier = float(settings["carrier_hz"])
        self._sample_rate = sr

        if preset != "binaural40":
            if self._noise is None or self._last_preset != preset:
                self._noise = NoiseGenerator(preset)
                self._last_preset = preset
            self._binaural = None
        else:
            if (
                self._binaural is None
                or self._last_preset != preset
                or self._last_carrier != carrier
            ):
                self._binaural = BinauralGenerator(sr, carrier)
                self._last_preset = preset
                self._last_carrier = carrier
            self._noise = None

    def _fill_pulse(self, outdata: np.ndarray, frames: int, settings: dict) -> None:
        sr = int(settings["sample_rate"])
        duration = float(settings.get("pulse_duration_sec", 1.0))
        interval = float(settings.get("pulse_interval_sec", 55.0))
        amplitude = float(settings.get("pulse_amplitude", 0.0001))

        cycle = max(1, int(interval * sr))
        pulse_len = min(max(1, int(duration * sr)), cycle - 1)

        indices = self._pulse_pos + np.arange(frames, dtype=np.int64)
        in_pulse = (indices % cycle) < pulse_len
        outdata.fill(0)
        pulse_frames = int(np.count_nonzero(in_pulse))
        if pulse_frames:
            t = indices[in_pulse] / sr
            val = (amplitude * np.sin(2 * np.pi * 1.0 * t)).astype(np.float32)
            outdata[in_pulse, 0] = val
            outdata[in_pulse, 1] = val
        self._pulse_pos = int(self._pulse_pos + frames)
        if self._pulse_pos >= cycle * 1000:
            self._pulse_pos %= cycle

    def _callback(self, outdata, frames, _time_info, status) -> None:
        if status and self._on_error:
            self._on_error(str(status))
        settings = self._get_settings()
        if not settings.get("playing", True):
            outdata.fill(0)
            return
        try:
            with self._lock:
                self._sync_mode(settings)
                if settings.get("keepalive_mode") == KEEPALIVE_MODE_PULSE:
                    self._fill_pulse(outdata, frames, settings)
                    return

                self._ensure_generators(settings)
                preset = settings["preset"]
                volume = self._live_volume
                noise = self._noise
                binaural = self._binaural

            if preset == "binaural40":
                if binaural is None:
                    raise RuntimeError("binaural generator not ready")
                chunk = binaural.generate(frames)
            else:
                if noise is None:
                    raise RuntimeError("noise generator not ready")
                chunk = mono_to_stereo(noise.generate(frames))

            outdata[:] = np.clip(chunk * volume, -1.0, 1.0).astype(np.float32)
        except Exception as exc:
            if self._on_error:
                self._on_error(str(exc))
            outdata.fill(0)

    def is_running(self) -> bool:
        with self._lock:
            if self._stream is None:
                return False
            try:
                return self._stream.active
            except Exception:
                return False

    def _stop_unsafe(self) -> sd.OutputStream | None:
        if self._stop_monitor_event is not None:
            self._stop_monitor_event.set()
        self._monitor_thread = None
        self._stop_monitor_event = None

        stream = self._stream
        self._stream = None
        self._noise = None
        self._binaural = None
        self._last_preset = None
        self._last_carrier = None
        self._last_keepalive_mode = None
        self._pulse_pos = 0
        return stream

    def start(self) -> None:
        settings = self._get_settings()
        sr = int(settings["sample_rate"])
        self._live_volume = float(settings.get("volume", 0.02))
        self._pulse_pos = 0
        self._last_keepalive_mode = settings.get("keepalive_mode")
        blocksize = blocksize_from_buffer_seconds(
            sr, float(settings.get("buffer_seconds", 0.012))
        )

        try:
            current_device_id = get_default_audio_endpoint_id()
        except Exception:
            current_device_id = None

        stream_to_close = None
        with self._lock:
            if self._stream is not None:
                try:
                    active = self._stream.active
                except Exception:
                    active = False
                if active:
                    return
                stream_to_close = self._stop_unsafe()

        if stream_to_close is not None:
            try:
                stream_to_close.stop()
            except Exception:
                pass
            try:
                stream_to_close.close()
            except Exception:
                pass

        with self._lock:
            if self._stream is not None:
                return

            self._last_device_id = current_device_id

            self._stream = sd.OutputStream(
                samplerate=sr,
                channels=2,
                dtype="float32",
                blocksize=blocksize,
                callback=self._callback,
            )
            self._stream.start()

            if current_device_id is not None:
                self._stop_monitor_event = threading.Event()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    args=(self._stop_monitor_event,),
                    daemon=True,
                )
                self._monitor_thread.start()

    def stop(self) -> None:
        stream = None
        with self._lock:
            stream = self._stop_unsafe()
        if stream is not None:
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass

    def _recreate_stream(self, stop_event: threading.Event) -> bool:
        """Attempt to stop the stream, re-initialize sounddevice,
        and start a new stream.

        Returns True if successful, False otherwise.
        """
        self.stop()
        try:
            sd._terminate()
            sd._initialize()
        except Exception as e:
            log_error("Failed to re-initialize sounddevice: %s", e)
        try:
            self.start()
            self._last_error_logged = None
            return True
        except Exception as e:
            err_msg = str(e)
            if err_msg != getattr(self, "_last_error_logged", None):
                log_error("Failed to restart stream: %s. Will retry...", err_msg)
                self._last_error_logged = err_msg
            stop_event.clear()
            return False

    def _monitor_loop(self, stop_event: threading.Event) -> None:
        while not stop_event.wait(3.0):
            settings = self._get_settings()
            if not settings.get("playing", True):
                break

            if not self.is_running():
                log_info("Audio stream stopped unexpectedly. Attempting to restart...")
                if self._recreate_stream(stop_event):
                    break
                continue

            try:
                current_id = get_default_audio_endpoint_id()
            except Exception:
                continue

            if current_id is None:
                continue

            with self._lock:
                last_id = self._last_device_id

            if current_id != last_id:
                log_info(
                    "Default audio output device changed from %s to %s. "
                    "Restarting stream.",
                    last_id,
                    current_id,
                )
                if self._recreate_stream(stop_event):
                    break
