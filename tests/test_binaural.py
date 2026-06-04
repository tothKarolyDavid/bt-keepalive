import numpy as np

from btkeepalive.audio.binaural import BEAT_HZ, BinauralGenerator


def test_binaural_generates_finite_stereo():
    gen = BinauralGenerator(44100, 200)
    out = gen.generate(1024)
    assert out.shape == (1024, 2)
    assert np.all(np.isfinite(out))


def test_binaural_beat_frequency():
    assert BinauralGenerator(44100, 200).beat_hz == BEAT_HZ


def test_binaural_clamps_right_channel_near_nyquist():
    gen = BinauralGenerator(8000, 3900)
    out = gen.generate(64)
    assert np.all(np.isfinite(out))
