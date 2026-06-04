from __future__ import annotations

import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    mutex_name = "Global\\BTKeepAlive_SingleInstance_Mutex"
    ERROR_ALREADY_EXISTS = 183

    def acquire() -> bool:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [
            wintypes.LPCVOID,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        handle = kernel32.CreateMutexW(None, True, mutex_name)
        if not handle:
            return True
        err = ctypes.get_last_error()
        if err == ERROR_ALREADY_EXISTS:
            return False
        return True
else:

    def acquire() -> bool:
        return True
