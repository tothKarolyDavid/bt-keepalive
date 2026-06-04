"""Windows tray icon — build the popup menu once; never rebuild on clicks."""

from __future__ import annotations

import functools
import sys

import pystray

if sys.platform == "win32":
    from pystray._win32 import Icon as _WinIcon

    class WinTrayIcon(_WinIcon):
        """Rebuild the menu before each popup so radio/check state stays current."""

        def update_menu(self) -> None:
            if getattr(self, "_menu_handle", None) is not None:
                return
            super().update_menu()

        def _on_notify(self, wparam, lparam) -> None:
            from pystray._util import win32 as win32

            if self.menu and lparam == win32.WM_RBUTTONUP:
                super().update_menu()
            super()._on_notify(wparam, lparam)

        def _handler(self, callback):  # noqa: ANN001
            @functools.wraps(callback)
            def inner(*args, **kwargs):
                callback(self)

            return inner

    def create_tray_icon(*args, **kwargs) -> pystray.Icon:
        return WinTrayIcon(*args, **kwargs)

else:

    def create_tray_icon(*args, **kwargs) -> pystray.Icon:
        return pystray.Icon(*args, **kwargs)
