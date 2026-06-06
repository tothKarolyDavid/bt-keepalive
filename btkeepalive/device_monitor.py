from __future__ import annotations

import sys


def get_default_audio_endpoint_id() -> str | None:
    """Get the current default Windows audio render endpoint ID (GUID).

    Returns None on failure or on non-Windows platforms.
    """
    if sys.platform != "win32":
        return None

    import ctypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    CLSID_MMDeviceEnumerator = GUID(
        0xBCDE0395,
        0xE52F,
        0x467C,
        (ctypes.c_ubyte * 8)(0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E),
    )
    IID_IMMDeviceEnumerator = GUID(
        0xA95664D2,
        0x9614,
        0x4F35,
        (ctypes.c_ubyte * 8)(0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6),
    )

    GetDefaultAudioEndpoint_Proto = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
    )

    GetId_Proto = ctypes.WINFUNCTYPE(
        ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)
    )

    Release_Proto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)

    ole32 = ctypes.windll.ole32
    hr = ole32.CoInitialize(None)
    co_initialized = hr in (0, 1)

    pEnumerator = ctypes.c_void_p()
    CLSCTX_ALL = 23
    hr = ole32.CoCreateInstance(
        ctypes.byref(CLSID_MMDeviceEnumerator),
        None,
        CLSCTX_ALL,
        ctypes.byref(IID_IMMDeviceEnumerator),
        ctypes.byref(pEnumerator),
    )
    if hr != 0:
        if co_initialized:
            ole32.CoUninitialize()
        return None

    try:
        vtable_address = ctypes.cast(
            pEnumerator, ctypes.POINTER(ctypes.c_void_p)
        ).contents.value
        vtbl = ctypes.cast(vtable_address, ctypes.POINTER(ctypes.c_void_p))

        GetDefaultAudioEndpoint = GetDefaultAudioEndpoint_Proto(vtbl[4])

        pDevice = ctypes.c_void_p()
        # eRender = 0, eConsole = 0
        hr = GetDefaultAudioEndpoint(pEnumerator, 0, 0, ctypes.byref(pDevice))
        if hr != 0:
            return None

        try:
            vtable_device_address = ctypes.cast(
                pDevice, ctypes.POINTER(ctypes.c_void_p)
            ).contents.value
            vtbl_device = ctypes.cast(
                vtable_device_address, ctypes.POINTER(ctypes.c_void_p)
            )

            GetId = GetId_Proto(vtbl_device[5])

            pstrId = ctypes.c_wchar_p()
            hr = GetId(pDevice, ctypes.byref(pstrId))
            if hr != 0:
                return None

            device_id = pstrId.value
            ole32.CoTaskMemFree(pstrId)
            return device_id
        finally:
            Release = Release_Proto(vtbl_device[2])
            Release(pDevice)
    finally:
        Release = Release_Proto(vtbl[2])
        Release(pEnumerator)
        if co_initialized:
            ole32.CoUninitialize()
