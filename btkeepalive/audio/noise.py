from __future__ import annotations

import numpy as np

PRESET_NAMES = ("white", "pink", "brown", "blue", "violet")

# Fixed gains: per-buffer peak normalization caused level jumps (clicks/pops).
_GAIN = {
    "white": 0.22,
    "pink": 0.055,
    "brown": 18.0,
    "blue": 0.22,
    "violet": 0.32,
}

# Leaky integrator for stationary brown noise (~-6 dB/octave).
_BROWN_LEAK = 0.998
_BROWN_DRIVE = 0.35


class NoiseGenerator:
    def __init__(self, preset: str) -> None:
        if preset not in PRESET_NAMES:
            raise ValueError(f"Unknown noise preset: {preset}")
        self.preset = preset
        self._pink_rows = np.zeros(16, dtype=np.float64)
        self._pink_counter = 0
        self._brown_state = 0.0
        self._blue_prev = 0.0
        self._violet_prev = (0.0, 0.0)

    def generate(self, n: int) -> np.ndarray:
        if self.preset == "white":
            return self._white(n)
        if self.preset == "pink":
            return self._pink(n)
        if self.preset == "brown":
            return self._brown(n)
        if self.preset == "blue":
            return self._blue(n)
        return self._violet(n)

    def _white(self, n: int) -> np.ndarray:
        return (np.random.standard_normal(n) * _GAIN["white"]).astype(np.float32)

    def _pink(self, n: int) -> np.ndarray:
        rows = self._pink_rows
        out = np.empty(n, dtype=np.float64)
        counter = self._pink_counter
        for i in range(n):
            counter += 1
            idx = min(((counter & -counter).bit_length() - 1), 15)
            rows[idx] = np.random.standard_normal()
            out[i] = rows.sum()
        self._pink_counter = counter
        self._pink_rows = rows
        return (out * _GAIN["pink"]).astype(np.float32)

    def _brown(self, n: int) -> np.ndarray:
        white = np.random.standard_normal(n)
        out = np.empty(n, dtype=np.float32)
        leak = _BROWN_LEAK
        drive = _BROWN_DRIVE
        gain = _GAIN[self.preset]
        state = self._brown_state
        for i in range(n):
            state = leak * state + (1.0 - leak) * drive * white[i]
            out[i] = state * gain
        self._brown_state = state
        return out

    def _blue(self, n: int) -> np.ndarray:
        white = np.random.standard_normal(n + 1)
        white[0] = self._blue_prev
        diff = np.diff(white)
        self._blue_prev = white[-1]
        return (diff * _GAIN["blue"]).astype(np.float32)

    def _violet(self, n: int) -> np.ndarray:
        white = np.random.standard_normal(n + 2)
        white[0], white[1] = self._violet_prev
        diff2 = np.diff(white, n=2)
        self._violet_prev = (white[-2], white[-1])
        return (diff2 * _GAIN["violet"]).astype(np.float32)
