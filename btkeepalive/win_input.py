"""Small Win32 helpers shared by dialogs."""

from __future__ import annotations

import sys
import ctypes

if sys.platform != "win32":
    raise RuntimeError("win_input is only supported on Windows")

user32 = ctypes.WinDLL("user32", use_last_error=True)

MB_OK = 0x00000000
MB_ICONERROR = 0x00000010


def message_box(title: str, text: str, *, error: bool = False) -> None:
    flags = MB_OK | (MB_ICONERROR if error else 0)
    user32.MessageBoxW(None, text, title, flags)
