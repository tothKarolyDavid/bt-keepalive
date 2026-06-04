import numpy as np
import pytest

from btkeepalive.audio.noise import PRESET_NAMES, NoiseGenerator


@pytest.mark.parametrize("preset", PRESET_NAMES)
def test_noise_generates_finite(preset):
    gen = NoiseGenerator(preset)
    out = gen.generate(1024)
    assert out.shape == (1024,)
    assert np.all(np.isfinite(out))


def test_unknown_preset_raises():
    with pytest.raises(ValueError, match="Unknown"):
        NoiseGenerator("purple")
