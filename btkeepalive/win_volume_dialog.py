"""Volume picker dialog with slider, live preview, and quick presets."""

from __future__ import annotations

import sys
from collections.abc import Callable
from ctypes import WINFUNCTYPE, byref, cast, create_unicode_buffer, sizeof, wintypes
import ctypes

from btkeepalive.config import format_volume_label, normalize_volume
from btkeepalive.volume_input import parse_volume_text
from btkeepalive.win_input import message_box

if sys.platform != "win32":
    raise RuntimeError("win_volume_dialog is only supported on Windows")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
comctl32 = ctypes.WinDLL("comctl32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WPARAM = wintypes.WPARAM
LPARAM = wintypes.LPARAM
HWND = wintypes.HWND
HINSTANCE = wintypes.HINSTANCE

CW_USEDEFAULT = 0x80000000
WS_CAPTION = 0x00C00000
WS_SYSMENU = 0x00080000
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_TABSTOP = 0x00010000
ES_AUTOHSCROLL = 0x0080
BS_DEFPUSHBUTTON = 0x0001
BS_PUSHBUTTON = 0x00000000
SS_CENTER = 0x00000001
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_HSCROLL = 0x0114
WM_KEYDOWN = 0x0100
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
SWP_NOZORDER = 0x0004
SWP_NOSIZE = 0x0001
TBS_HORZ = 0x0000
TBS_NOTICKS = 0x0010
TBM_GETPOS = 0x0400
TBM_SETPOS = 0x0405
TBM_SETRANGEMIN = 0x0407
TBM_SETRANGEMAX = 0x0408
TBM_SETLINESIZE = 0x0417
TBM_SETPAGESIZE = 0x0418

# 1 unit = 0.01% → 0.01% .. 100.00%
SLIDER_MIN = 1
SLIDER_MAX = 10000

ID_OK = 1
ID_CANCEL = 2
ID_EDIT = 100
ID_SLIDER = 101
ID_VALUE_LABEL = 102
ID_PRESET_BASE = 200

_QUICK_PRESETS = (
    (0.01, "1%"),
    (0.02, "2%"),
    (0.05, "5%"),
)

_CLASS_NAME = "BTKeepAlive_VolumeDlg_v3"
_hinstance = kernel32.GetModuleHandleW(None)
_class_registered = False
_comctl_initialized = False
_dialogs: dict[int, dict] = {}


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HANDLE),
    ]


class INITCOMMONCONTROLSEX(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("dwICC", wintypes.DWORD)]


WNDPROC = WINFUNCTYPE(LRESULT, HWND, wintypes.UINT, WPARAM, LPARAM)


def _pos_to_gain(pos: int) -> float:
    clamped = max(SLIDER_MIN, min(SLIDER_MAX, int(pos)))
    return clamped / 10000.0


def _gain_to_pos(gain: float) -> int:
    gain = max(_pos_to_gain(SLIDER_MIN), min(1.0, float(gain)))
    return int(round(gain * 10000))


def _init_comctl() -> None:
    global _comctl_initialized
    if _comctl_initialized:
        return
    icc = INITCOMMONCONTROLSEX()
    icc.dwSize = sizeof(icc)
    icc.dwICC = 0x0004  # ICC_BAR_CLASSES
    comctl32.InitCommonControlsEx(byref(icc))
    _comctl_initialized = True


@WNDPROC
def _dialog_proc(hwnd: HWND, msg: int, wparam: WPARAM, lparam: LPARAM) -> LRESULT:
    state = _dialogs.get(int(hwnd))

    if state is not None and msg == WM_HSCROLL:
        slider = state.get("slider")
        if slider and int(lparam) == int(slider):
            _sync_from_slider(state)

    if state is not None:
        if msg == WM_KEYDOWN:
            key = int(wparam)
            if key == VK_RETURN:
                _finish(hwnd, state, accept=True)
                return 0
            if key == VK_ESCAPE:
                _finish(hwnd, state, accept=False)
                return 0

        if msg == WM_COMMAND:
            cmd = int(wparam & 0xFFFF)
            if cmd == ID_OK:
                _finish(hwnd, state, accept=True)
                return 0
            if cmd == ID_CANCEL:
                _finish(hwnd, state, accept=False)
                return 0
            if ID_PRESET_BASE <= cmd < ID_PRESET_BASE + len(_QUICK_PRESETS):
                preset_gain = _QUICK_PRESETS[cmd - ID_PRESET_BASE][0]
                _apply_gain(state, preset_gain)
                return 0

        if msg == WM_DESTROY:
            _dialogs.pop(int(hwnd), None)
            user32.PostQuitMessage(0)
            return 0

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


_dialog_proc_ref = _dialog_proc


def _ensure_class() -> None:
    global _class_registered
    _init_comctl()
    if _class_registered:
        return
    wc = WNDCLASSEXW()
    wc.cbSize = sizeof(wc)
    wc.lpfnWndProc = cast(_dialog_proc_ref, ctypes.c_void_p)
    wc.hInstance = _hinstance
    wc.hCursor = user32.LoadCursorW(None, 32512)
    wc.hbrBackground = wintypes.HANDLE(6)
    wc.lpszClassName = _CLASS_NAME
    if not user32.RegisterClassExW(byref(wc)):
        raise ctypes.WinError(ctypes.get_last_error())
    _class_registered = True


def _set_static_text(hwnd: HWND | None, text: str) -> None:
    if hwnd:
        user32.SetWindowTextW(hwnd, text)


def _get_edit_text(hwnd_edit: HWND) -> str:
    length = user32.GetWindowTextLengthW(hwnd_edit)
    buf = create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd_edit, buf, length + 1)
    return buf.value


def _fire_preview(state: dict) -> None:
    preview = state.get("on_preview")
    if preview is not None:
        preview(float(state["gain"]))


def _update_value_label(state: dict, gain: float) -> None:
    _set_static_text(state.get("value_label"), format_volume_label(gain))


def _set_edit_from_gain(state: dict, gain: float) -> None:
    edit = state.get("edit")
    if not edit:
        return
    state["syncing"] = True
    user32.SetWindowTextW(edit, format_volume_label(gain, for_input=True))
    state["syncing"] = False


def _set_slider_from_gain(state: dict, gain: float) -> None:
    slider = state.get("slider")
    if not slider:
        return
    state["syncing"] = True
    user32.SendMessageW(slider, TBM_SETPOS, 1, _gain_to_pos(gain))
    state["syncing"] = False


def _apply_gain(state: dict, gain: float) -> None:
    state["gain"] = normalize_volume(gain)
    _update_value_label(state, state["gain"])
    _set_edit_from_gain(state, state["gain"])
    _set_slider_from_gain(state, state["gain"])
    _fire_preview(state)


def _sync_from_slider(state: dict) -> None:
    if state.get("syncing"):
        return
    slider = state.get("slider")
    if not slider:
        return
    pos = int(user32.SendMessageW(slider, TBM_GETPOS, 0, 0))
    gain = _pos_to_gain(pos)
    state["gain"] = normalize_volume(gain)
    _update_value_label(state, state["gain"])
    _set_edit_from_gain(state, state["gain"])
    _fire_preview(state)


def _read_gain_from_controls(state: dict) -> float | None:
    edit = state.get("edit")
    if edit:
        text = _get_edit_text(edit).strip()
        if text:
            parsed = parse_volume_text(text)
            if parsed is not None:
                return normalize_volume(parsed)
    slider = state.get("slider")
    if slider:
        pos = int(user32.SendMessageW(slider, TBM_GETPOS, 0, 0))
        return normalize_volume(_pos_to_gain(pos))
    return None


def _restore_initial(state: dict) -> None:
    preview = state.get("on_preview")
    if preview is not None:
        preview(float(state["initial_gain"]))


def _finish(hwnd: HWND, state: dict, *, accept: bool) -> None:
    if not accept:
        _restore_initial(state)
        state["result"] = None
        user32.DestroyWindow(hwnd)
        return
    gain = _read_gain_from_controls(state)
    if gain is None:
        message_box(
            "Invalid volume",
            "Enter a percent between 0.01 and 100 (e.g. 2 or 0.5), "
            "or use the slider.",
            error=True,
        )
        return
    state["result"] = gain
    user32.DestroyWindow(hwnd)


def _center_window(hwnd: HWND, width: int, height: int) -> None:
    rect = wintypes.RECT(0, 0, width, height)
    style = user32.GetWindowLongW(hwnd, -16)
    user32.AdjustWindowRect(byref(rect), style, False)
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    user32.SetWindowPos(hwnd, None, x, y, 0, 0, SWP_NOZORDER | SWP_NOSIZE)


def prompt_volume_dialog(
    current_gain: float,
    on_preview: Callable[[float], None] | None = None,
) -> float | None:
    """Modal volume UI; blocks the calling thread. Returns gain or None."""
    _ensure_class()

    dlg_w, dlg_h = 460, 310
    hwnd = user32.CreateWindowExW(
        0,
        _CLASS_NAME,
        "Volume",
        WS_POPUP | WS_CAPTION | WS_SYSMENU,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        dlg_w,
        dlg_h,
        None,
        None,
        _hinstance,
        None,
    )
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())

    gain = normalize_volume(current_gain)
    state: dict = {
        "result": None,
        "gain": gain,
        "initial_gain": gain,
        "syncing": False,
        "on_preview": on_preview,
        "slider": None,
        "edit": None,
        "value_label": None,
    }
    _dialogs[int(hwnd)] = state

    margin = 16
    inner_w = dlg_w - margin * 2
    slider_y = 88
    slider_h = 40

    user32.CreateWindowExW(
        0,
        "Static",
        "Keep the sound quiet — just loud enough for Bluetooth to stay awake.\r\n"
        "You will hear the volume change while you drag the slider.",
        WS_CHILD | WS_VISIBLE,
        margin,
        10,
        inner_w,
        36,
        hwnd,
        None,
        _hinstance,
        None,
    )

    value_label = user32.CreateWindowExW(
        0,
        "Static",
        format_volume_label(gain),
        WS_CHILD | WS_VISIBLE | SS_CENTER,
        margin,
        50,
        inner_w,
        30,
        hwnd,
        ctypes.c_void_p(ID_VALUE_LABEL),
        _hinstance,
        None,
    )
    state["value_label"] = value_label

    slider = user32.CreateWindowExW(
        0,
        "msctls_trackbar32",
        None,
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | TBS_HORZ | TBS_NOTICKS,
        margin,
        slider_y,
        inner_w,
        slider_h,
        hwnd,
        ctypes.c_void_p(ID_SLIDER),
        _hinstance,
        None,
    )
    state["slider"] = slider
    user32.SendMessageW(slider, TBM_SETRANGEMIN, 0, SLIDER_MIN)
    user32.SendMessageW(slider, TBM_SETRANGEMAX, 0, SLIDER_MAX)
    user32.SendMessageW(slider, TBM_SETLINESIZE, 0, 1)
    user32.SendMessageW(slider, TBM_SETPAGESIZE, 0, 100)
    _set_slider_from_gain(state, gain)

    label_y = slider_y + slider_h + 6
    user32.CreateWindowExW(
        0,
        "Static",
        "Quiet",
        WS_CHILD | WS_VISIBLE,
        margin,
        label_y,
        40,
        16,
        hwnd,
        None,
        _hinstance,
        None,
    )
    user32.CreateWindowExW(
        0,
        "Static",
        "Loud",
        WS_CHILD | WS_VISIBLE,
        margin + inner_w - 40,
        label_y,
        40,
        16,
        hwnd,
        None,
        _hinstance,
        None,
    )
    user32.CreateWindowExW(
        0,
        "Static",
        "0.01%",
        WS_CHILD | WS_VISIBLE,
        margin,
        label_y + 18,
        52,
        16,
        hwnd,
        None,
        _hinstance,
        None,
    )
    user32.CreateWindowExW(
        0,
        "Static",
        "100%",
        WS_CHILD | WS_VISIBLE,
        margin + inner_w - 52,
        label_y + 18,
        52,
        16,
        hwnd,
        None,
        _hinstance,
        None,
    )

    user32.CreateWindowExW(
        0,
        "Static",
        "Exact value:",
        WS_CHILD | WS_VISIBLE,
        margin,
        168,
        90,
        20,
        hwnd,
        None,
        _hinstance,
        None,
    )
    edit = user32.CreateWindowExW(
        0x00000200,
        "Edit",
        format_volume_label(gain, for_input=True),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_AUTOHSCROLL,
        margin + 96,
        164,
        80,
        24,
        hwnd,
        ctypes.c_void_p(ID_EDIT),
        _hinstance,
        None,
    )
    state["edit"] = edit
    user32.CreateWindowExW(
        0,
        "Static",
        "%",
        WS_CHILD | WS_VISIBLE,
        margin + 182,
        168,
        20,
        20,
        hwnd,
        None,
        _hinstance,
        None,
    )

    preset_x = margin
    for idx, (preset_gain, label) in enumerate(_QUICK_PRESETS):
        user32.CreateWindowExW(
            0,
            "Button",
            label,
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
            preset_x,
            202,
            52,
            26,
            hwnd,
            ctypes.c_void_p(ID_PRESET_BASE + idx),
            _hinstance,
            None,
        )
        preset_x += 58

    user32.CreateWindowExW(
        0,
        "Button",
        "Apply",
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_DEFPUSHBUTTON,
        dlg_w - margin - 178,
        258,
        82,
        30,
        hwnd,
        ctypes.c_void_p(ID_OK),
        _hinstance,
        None,
    )
    user32.CreateWindowExW(
        0,
        "Button",
        "Cancel",
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
        dlg_w - margin - 88,
        258,
        82,
        30,
        hwnd,
        ctypes.c_void_p(ID_CANCEL),
        _hinstance,
        None,
    )

    user32.ShowWindow(hwnd, 5)
    _center_window(hwnd, dlg_w, dlg_h)
    user32.SetForegroundWindow(hwnd)
    if slider:
        user32.SetFocus(slider)

    msg = wintypes.MSG()
    while user32.GetMessageW(byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(byref(msg))
        user32.DispatchMessageW(byref(msg))

    return state.get("result")
