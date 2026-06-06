import numpy as np

from btkeepalive.config import KEEPALIVE_MODE_PULSE
from btkeepalive.stream import AudioStream, blocksize_from_buffer_seconds


def test_blocksize_from_buffer_seconds_default():
    assert blocksize_from_buffer_seconds(44100, 0.012) == 529


def test_blocksize_clamps_low_and_high():
    assert blocksize_from_buffer_seconds(8000, 0.001) == 64
    assert blocksize_from_buffer_seconds(48000, 1.0) == 8192


def _pulse_settings(**overrides) -> dict:
    base = {
        "sample_rate": 44100,
        "pulse_duration_sec": 1.0,
        "pulse_interval_sec": 55.0,
        "pulse_amplitude": 0.0001,
        "keepalive_mode": KEEPALIVE_MODE_PULSE,
        "playing": True,
    }
    base.update(overrides)
    return base


def test_fill_pulse_has_energy_at_cycle_start():
    stream = AudioStream(lambda: _pulse_settings())
    outdata = np.zeros((256, 2), dtype=np.float32)
    stream._pulse_pos = 0
    stream._fill_pulse(outdata, 256, _pulse_settings())
    assert np.any(outdata != 0)


def test_fill_pulse_generates_sine_wave():
    stream = AudioStream(lambda: _pulse_settings())
    outdata = np.zeros((256, 2), dtype=np.float32)
    stream._pulse_pos = 0
    settings = _pulse_settings()
    stream._fill_pulse(outdata, 256, settings)
    
    sr = settings["sample_rate"]
    amplitude = settings["pulse_amplitude"]
    indices = np.arange(256)
    expected = (amplitude * np.sin(2 * np.pi * 1.0 * indices / sr)).astype(np.float32)
    
    assert np.allclose(outdata[:, 0], expected)
    assert np.allclose(outdata[:, 1], expected)


def test_fill_pulse_silent_between_pulses():
    stream = AudioStream(lambda: _pulse_settings())
    sr = 44100
    cycle = int(55 * sr)
    pulse_len = min(int(1.0 * sr), cycle - 1)
    stream._pulse_pos = pulse_len
    outdata = np.zeros((128, 2), dtype=np.float32)
    stream._fill_pulse(outdata, 128, _pulse_settings())
    assert not np.any(outdata)


def test_fill_pulse_wraps_position():
    stream = AudioStream(lambda: _pulse_settings())
    sr = 44100
    cycle = max(1, int(55 * sr))
    stream._pulse_pos = cycle * 1000
    outdata = np.zeros((64, 2), dtype=np.float32)
    stream._fill_pulse(outdata, 64, _pulse_settings())
    assert stream._pulse_pos < cycle * 1000


def test_callback_silent_when_paused():
    stream = AudioStream(lambda: _pulse_settings(playing=False))
    outdata = np.ones((32, 2), dtype=np.float32)
    stream._callback(outdata, 32, None, None)
    assert not np.any(outdata)


def test_reset_pulse_phase():
    stream = AudioStream(lambda: _pulse_settings())
    stream._pulse_pos = 999
    stream.reset_pulse_phase()
    assert stream._pulse_pos == 0
