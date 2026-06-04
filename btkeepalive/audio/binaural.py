from __future__ import annotations

import numpy as np

BEAT_HZ = 40.0


class BinauralGenerator:
    def __init__(
        self,
        sample_rate: int,
        carrier_hz: float,
        beat_hz: float = BEAT_HZ,
    ) -> None:
        self.sample_rate = sample_rate
        self.carrier_hz = carrier_hz
        self.beat_hz = beat_hz
        self._phase_left = 0.0
        self._phase_right = 0.0

    def generate(self, n: int) -> np.ndarray:
        sr = self.sample_rate
        left_hz = self.carrier_hz
        right_hz = self.carrier_hz + self.beat_hz
        if right_hz >= sr / 2:
            right_hz = sr / 2 - 1.0

        t = (np.arange(n, dtype=np.float64) + self._phase_left) / sr
        left = np.sin(2.0 * np.pi * left_hz * t)

        t_r = (np.arange(n, dtype=np.float64) + self._phase_right) / sr
        right = np.sin(2.0 * np.pi * right_hz * t_r)

        self._phase_left = (self._phase_left + n) % sr
        self._phase_right = (self._phase_right + n) % sr

        stereo = np.empty((n, 2), dtype=np.float32)
        stereo[:, 0] = left.astype(np.float32)
        stereo[:, 1] = right.astype(np.float32)
        return stereo
