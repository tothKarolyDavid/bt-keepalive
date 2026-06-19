from __future__ import annotations

import sys
from pathlib import Path

from btkeepalive import updater


def test_parse_version():
    assert updater.parse_version("v1.2.0") == (1, 2, 0)
    assert updater.parse_version("1.3.1-beta") == (1, 3, 1)
    assert updater.parse_version("2.0") == (2, 0)
    assert updater.parse_version("v0.0.1-alpha.2") == (0, 0, 1, 2)
    assert updater.parse_version("v") == ()


def test_cleanup_old_version_not_frozen(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    # Ensure it doesn't try to call unlink or raise exceptions
    unlinked = False

    def fake_unlink(self):
        nonlocal unlinked
        unlinked = True

    monkeypatch.setattr(Path, "unlink", fake_unlink)
    updater.cleanup_old_version()
    assert not unlinked


def test_cleanup_old_version_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Apps\BTKeepAlive.exe", raising=False)

    exists_checked = False
    unlinked = False

    def fake_is_file(self):
        nonlocal exists_checked
        if "BTKeepAlive.exe.old" in str(self):
            exists_checked = True
            return True
        return False

    def fake_unlink(self):
        nonlocal unlinked
        if "BTKeepAlive.exe.old" in str(self):
            unlinked = True

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(Path, "unlink", fake_unlink)

    updater.cleanup_old_version()
    assert exists_checked
    assert unlinked


def test_compute_sha256(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"hello")

    # sha256 of "hello" is
    # 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert updater.compute_sha256(test_file) == expected


def test_fetch_expected_sha256(monkeypatch):
    checksums_content = (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        "  BTKeepAlive.exe\n"
        "d56e6f669b6b7a66f499ff3cb51cd7ad03b22b64d1fcd81fa746b132890a78bb"
        "  BTKeepAlive-setup.exe\n"
    )

    class FakeResponse:
        status = 200

        def read(self):
            return checksums_content.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout=None: FakeResponse()
    )

    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert updater.fetch_expected_sha256("https://fakeurl/checksums.txt") == expected


def test_get_latest_release(monkeypatch):
    release_json = (
        '{"tag_name": "v1.3.0", "assets": ['
        '{"name": "BTKeepAlive.exe", "browser_download_url": "https://fake/BTKeepAlive.exe"},'
        '{"name": "SHA256SUMS.txt", "browser_download_url": "https://fake/SHA256SUMS.txt"}'
        "]}"
    )

    class FakeResponse:
        status = 200

        def read(self):
            return release_json.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout=None: FakeResponse()
    )

    result = updater.get_latest_release()
    assert result is not None
    assert result["tag_name"] == "v1.3.0"
    assert len(result["assets"]) == 2


def test_check_for_update_available_new_version(monkeypatch):
    monkeypatch.setattr(updater, "__version__", "1.2.0")

    release_json = (
        '{"tag_name": "v1.3.0", "assets": ['
        '{"name": "BTKeepAlive.exe", "browser_download_url": "https://fake/BTKeepAlive.exe"},'
        '{"name": "SHA256SUMS.txt", "browser_download_url": "https://fake/SHA256SUMS.txt"}'
        "]}"
    )

    class FakeResponse:
        status = 200

        def read(self):
            return release_json.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout=None: FakeResponse()
    )

    result = updater.check_for_update_available()
    assert result is not None
    assert result["version"] == "v1.3.0"
    assert result["download_url"] == "https://fake/BTKeepAlive.exe"
    assert result["checksum_url"] == "https://fake/SHA256SUMS.txt"


def test_check_for_update_available_no_new_version(monkeypatch):
    monkeypatch.setattr(updater, "__version__", "1.3.0")

    release_json = (
        '{"tag_name": "v1.3.0", "assets": ['
        '{"name": "BTKeepAlive.exe", "browser_download_url": "https://fake/BTKeepAlive.exe"},'
        '{"name": "SHA256SUMS.txt", "browser_download_url": "https://fake/SHA256SUMS.txt"}'
        "]}"
    )

    class FakeResponse:
        status = 200

        def read(self):
            return release_json.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout=None: FakeResponse()
    )

    result = updater.check_for_update_available()
    assert result is None


def test_apply_hot_swap_missing_executable(monkeypatch):
    monkeypatch.setattr(sys, "executable", r"C:\Apps\MissingExe.exe", raising=False)

    def fake_is_file(self):
        return False

    monkeypatch.setattr(Path, "is_file", fake_is_file)

    import pytest

    with pytest.raises(FileNotFoundError) as exc_info:
        updater.apply_hot_swap(Path(r"C:\Apps\BTKeepAlive.exe.new"))

    assert "moved or deleted since startup" in str(exc_info.value)


def test_download_worker_missing_executable(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Apps\MissingExe.exe", raising=False)

    # Mock fetch_expected_sha256 to return a dummy hash so we pass step 1
    monkeypatch.setattr(updater, "fetch_expected_sha256", lambda url: "dummy_hash")

    def fake_is_file(self):
        return False

    monkeypatch.setattr(Path, "is_file", fake_is_file)

    dialog = updater.DownloadProgressDialog(
        "v1.3.0", "http://fake/download", "http://fake/checksum"
    )
    dialog.download_worker()

    assert not dialog.success
    assert dialog.error_message is not None
    assert "moved or deleted since startup" in dialog.error_message


def test_apply_hot_swap_success(monkeypatch):
    import os
    import subprocess
    from pathlib import Path

    import pytest

    # Set up some dummy environment variables simulating a PyInstaller run
    monkeypatch.setenv("_MEIPASS", r"C:\Temp\_MEI12345")
    monkeypatch.setenv("_MEIPASS2", r"C:\Temp\_MEI12345")
    monkeypatch.setenv("SOME_OTHER_VAR", "hello")

    monkeypatch.setattr(sys, "executable", r"C:\Apps\BTKeepAlive.exe", raising=False)

    # Mock file checks/renaming/deletions
    renamed = []
    unlinked = []

    def fake_is_file(self):
        return True

    def fake_rename(self, target):
        renamed.append((str(self), str(target)))

    def fake_unlink(self):
        unlinked.append(str(self))

    monkeypatch.setattr(Path, "is_file", fake_is_file)
    monkeypatch.setattr(Path, "rename", fake_rename)
    monkeypatch.setattr(Path, "unlink", fake_unlink)

    # Mock subprocess.Popen and capture parameters
    popen_args = {}

    def fake_popen(args, **kwargs):
        popen_args["args"] = args
        popen_args.update(kwargs)
        return None

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    # Mock os._exit to raise a custom exception to stop execution instead of terminating
    class MockExitException(Exception):
        pass

    def fake_exit(code):
        raise MockExitException(f"exited with {code}")

    monkeypatch.setattr(os, "_exit", fake_exit)

    with pytest.raises(MockExitException) as exc_info:
        updater.apply_hot_swap(Path(r"C:\Apps\BTKeepAlive.exe.new"))

    assert "exited with 0" in str(exc_info.value)
    assert popen_args["args"] == [r"C:\Apps\BTKeepAlive.exe"]
    assert popen_args["creationflags"] == 0x00000008
    assert popen_args["close_fds"] is True
    assert popen_args["start_new_session"] is True

    # Check env cleaning
    env = popen_args["env"]
    assert env is not None
    assert env.get("PYINSTALLER_RESET_ENVIRONMENT") == "1"
    assert "_MEIPASS" not in env
    assert "_MEIPASS2" not in env
    assert env.get("SOME_OTHER_VAR") == "hello"

    # Verify expected file operations
    assert r"C:\Apps\BTKeepAlive.exe.old" in unlinked
    assert (r"C:\Apps\BTKeepAlive.exe", r"C:\Apps\BTKeepAlive.exe.old") in renamed
    assert (r"C:\Apps\BTKeepAlive.exe.new", r"C:\Apps\BTKeepAlive.exe") in renamed
