import sys

import pytest

from btkeepalive import startup


def test_exe_path_empty_when_not_frozen(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert startup.exe_path() == ""


def test_exe_path_when_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Apps\BTKeepAlive.exe", raising=False)
    assert startup.exe_path() == r"C:\Apps\BTKeepAlive.exe"


def test_set_startup_enabled_requires_exe_when_enabling(monkeypatch):
    monkeypatch.setattr(startup, "exe_path", lambda: "")
    assert startup.set_startup_enabled(True) is False


def test_is_startup_enabled_reads_registry(monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows only")

    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            pass

    def fake_open(key, subkey, reserved, access):
        return FakeKey()

    monkeypatch.setattr("winreg.OpenKey", fake_open)
    monkeypatch.setattr("winreg.QueryValueEx", lambda key, name: (r"C:\x.exe", 1))
    assert startup.is_startup_enabled() is True


def test_is_startup_enabled_missing_value(monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows only")

    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            pass

    def fake_open(key, subkey, reserved, access):
        return FakeKey()

    def raise_not_found(key, name):
        raise FileNotFoundError

    monkeypatch.setattr("winreg.OpenKey", fake_open)
    monkeypatch.setattr("winreg.QueryValueEx", raise_not_found)
    assert startup.is_startup_enabled() is False
