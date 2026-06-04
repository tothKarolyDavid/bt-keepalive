"""Volume picker (tkinter on a worker thread; reliable slider rendering on Windows)."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from btkeepalive.config import (
    VOLUME_QUICK_PRESETS,
    format_volume_label,
    normalize_volume,
)
from btkeepalive.volume_input import parse_volume_percent

# 1 unit = 0.01% → 0.01% .. 100.00%
SLIDER_MIN = 1
SLIDER_MAX = 10000


def _pos_to_gain(pos: int) -> float:
    clamped = max(SLIDER_MIN, min(SLIDER_MAX, int(pos)))
    return clamped / 10000.0


def _gain_to_pos(gain: float) -> int:
    gain = max(_pos_to_gain(SLIDER_MIN), min(1.0, float(gain)))
    return int(round(gain * 10000))


def _use_windows_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    for theme in ("vista", "winnative", "xpnative", "clam"):
        try:
            style.theme_use(theme)
            return
        except tk.TclError:
            continue


def prompt_volume_dialog(
    current_gain: float,
    on_preview: Callable[[float], None] | None = None,
) -> float | None:
    """Modal volume UI; blocks the calling thread. Returns gain or None."""
    if sys.platform != "win32":
        return None

    initial = normalize_volume(current_gain)
    result: dict[str, float | None] = {"value": None}
    syncing = {"busy": False}

    root = tk.Tk()
    root.title("BT KeepAlive: Volume")
    root.resizable(False, False)
    try:
        root.attributes("-topmost", True)
    except tk.TclError:
        pass
    _use_windows_theme(root)

    pos_var = tk.IntVar(value=_gain_to_pos(initial))
    entry_var = tk.StringVar(value=format_volume_label(initial, for_input=True))
    error_var = tk.StringVar(value="")

    main = ttk.Frame(root, padding=20)
    main.grid(row=0, column=0, sticky="nsew")

    ttk.Label(
        main,
        text=("Keep the sound quiet: just loud enough for Bluetooth to stay awake."),
        wraplength=400,
        justify=tk.CENTER,
    ).grid(row=0, column=0, columnspan=3, pady=(0, 4))

    ttk.Label(
        main,
        text=(
            "Drag the slider or type an exact percent to hear changes. "
            "Cancel restores your previous level."
        ),
        wraplength=400,
        justify=tk.CENTER,
        foreground="#505050",
    ).grid(row=1, column=0, columnspan=3, pady=(0, 12))

    percent_label = tk.Label(
        main,
        text=format_volume_label(initial),
        font=("Segoe UI", 22, "bold"),
    )
    percent_label.grid(row=2, column=0, columnspan=3, pady=(0, 12))

    def preview(gain: float) -> None:
        if on_preview is not None:
            on_preview(gain)

    def sync_display(gain: float, *, update_entry: bool) -> None:
        if syncing["busy"]:
            return
        syncing["busy"] = True
        gain = normalize_volume(gain)
        pos_var.set(_gain_to_pos(gain))
        percent_label.config(text=format_volume_label(gain))
        if update_entry:
            entry_var.set(format_volume_label(gain, for_input=True))
        syncing["busy"] = False
        preview(gain)

    def apply_gain(gain: float) -> None:
        sync_display(gain, update_entry=True)

    def on_entry_change(*_args: object) -> None:
        if syncing["busy"]:
            return
        text = entry_var.get().strip()
        if not text:
            error_var.set("")
            return
        gain = parse_volume_percent(text)
        if gain is None:
            error_var.set("Enter a percent between 0.01 and 100.")
            return
        error_var.set("")
        sync_display(gain, update_entry=False)

    def on_scale(value: str) -> None:
        if syncing["busy"]:
            return
        apply_gain(_pos_to_gain(int(float(value))))

    scale = ttk.Scale(
        main,
        from_=SLIDER_MIN,
        to=SLIDER_MAX,
        orient=tk.HORIZONTAL,
        variable=pos_var,
        length=400,
        command=on_scale,
    )
    scale.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 4))

    ends = ttk.Frame(main)
    ends.grid(row=4, column=0, columnspan=3, sticky="ew")
    ttk.Label(ends, text="Quiet · 0.01%").pack(side=tk.LEFT)
    ttk.Label(ends, text="100% · Loud").pack(side=tk.RIGHT)

    exact_row = ttk.Frame(main)
    exact_row.grid(row=5, column=0, columnspan=3, pady=(16, 8), sticky="w")
    ttk.Label(exact_row, text="Exact value:").pack(side=tk.LEFT, padx=(0, 8))
    entry = ttk.Entry(exact_row, textvariable=entry_var, width=12, justify=tk.CENTER)
    entry.pack(side=tk.LEFT)
    ttk.Label(exact_row, text="%").pack(side=tk.LEFT, padx=(4, 0))
    entry_var.trace_add("write", on_entry_change)

    ttk.Label(main, textvariable=error_var, foreground="#a00000").grid(
        row=6, column=0, columnspan=3, pady=(0, 8)
    )

    preset_row = ttk.Frame(main)
    preset_row.grid(row=7, column=0, columnspan=3, pady=(0, 16))
    for preset_gain in VOLUME_QUICK_PRESETS:
        label = format_volume_label(preset_gain)
        ttk.Button(
            preset_row,
            text=label,
            width=6,
            command=lambda g=preset_gain: apply_gain(g),
        ).pack(side=tk.LEFT, padx=4)

    btn_row = ttk.Frame(main)
    btn_row.grid(row=8, column=0, columnspan=3, sticky="e")

    def on_cancel() -> None:
        preview(initial)
        result["value"] = None
        root.destroy()

    def on_apply() -> None:
        text = entry_var.get().strip()
        gain: float | None = None
        if text:
            gain = parse_volume_percent(text)
            if gain is None:
                error_var.set("Enter a percent between 0.01 and 100.")
                return
        if gain is None:
            gain = normalize_volume(_pos_to_gain(pos_var.get()))
        else:
            gain = normalize_volume(gain)
        error_var.set("")
        result["value"] = gain
        root.destroy()

    ttk.Button(btn_row, text="Cancel", command=on_cancel).pack(
        side=tk.RIGHT, padx=(8, 0)
    )
    apply_btn = ttk.Button(btn_row, text="Apply", command=on_apply)
    apply_btn.pack(side=tk.RIGHT)
    root.bind("<Return>", lambda _event: on_apply())
    root.bind("<Escape>", lambda _event: on_cancel())
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.update_idletasks()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"+{x}+{y}")

    entry.focus_set()
    entry.select_range(0, tk.END)

    root.mainloop()
    return result["value"]  # type: ignore[return-value]
