import sys
from unittest.mock import patch

from btkeepalive.device_monitor import get_default_audio_endpoint_id


def test_get_default_audio_endpoint_id_non_windows():
    with patch("sys.platform", "linux"):
        assert get_default_audio_endpoint_id() is None


def test_get_default_audio_endpoint_id_windows_success():
    if sys.platform != "win32":
        # Can only fully run on Windows or by mocking ctypes
        return

    # Let's ensure it runs and either returns a string (device ID)
    # or None (if no devices)
    res = get_default_audio_endpoint_id()
    if res is not None:
        assert isinstance(res, str)
