import sys

import pytest

from btkeepalive.single_instance import acquire


def test_acquire_on_non_windows_always_allows():
    if sys.platform == "win32":
        pytest.skip("second instance behavior is OS-specific on Windows")
    assert acquire() is True
