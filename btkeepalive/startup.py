from __future__ import annotations

import sys
import winreg

APP_RUN_NAME = "BTKeepAlive"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return ""


def is_startup_enabled() -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ
        ) as key:
            winreg.QueryValueEx(key, APP_RUN_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_startup_enabled(enabled: bool) -> bool:
    path = exe_path()
    if not path and enabled:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_RUN_NAME, 0, winreg.REG_SZ, path)
            else:
                try:
                    winreg.DeleteValue(key, APP_RUN_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
