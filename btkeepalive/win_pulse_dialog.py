"""Pulse keepalive interval picker (tkinter, worker thread)."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

PULSE_INTERVAL_MIN = 10.0
PULSE_INTERVAL_MAX = 300.0


def parse_pulse_interval(text: str) -> float | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value < PULSE_INTERVAL_MIN or value > PULSE_INTERVAL_MAX:
        return None
    return value


def prompt_pulse_interval_dialog(current_sec: float) -> float | None:
    if sys.platform != "win32":
        return None

    initial = max(PULSE_INTERVAL_MIN, min(PULSE_INTERVAL_MAX, float(current_sec)))
    result: dict[str, float | None] = {"value": None}
    error_var = tk.StringVar(value="")

    root = tk.Tk()
    root.title("BT KeepAlive — Pulse interval")
    root.resizable(False, False)
    try:
        root.attributes("-topmost", True)
    except tk.TclError:
        pass

    main = ttk.Frame(root, padding=20)
    main.grid(row=0, column=0)

    ttk.Label(
        main,
        text=(
            "Seconds between quiet pulses. Lower values keep Bluetooth awake more "
            "often but use slightly more power."
        ),
        wraplength=360,
        justify=tk.CENTER,
    ).grid(row=0, column=0, pady=(0, 12))

    entry_var = tk.StringVar(
        value=f"{int(initial)}" if initial == int(initial) else f"{initial:g}"
    )
    entry = ttk.Entry(main, textvariable=entry_var, width=10, justify=tk.CENTER)
    entry.grid(row=1, column=0, pady=(0, 4))
    ttk.Label(main, text="seconds (10–300)").grid(row=2, column=0, pady=(0, 8))

    error_label = ttk.Label(main, textvariable=error_var, foreground="#a00000")
    error_label.grid(row=3, column=0, pady=(0, 12))

    btn_row = ttk.Frame(main)
    btn_row.grid(row=4, column=0, sticky="e")

    def on_cancel() -> None:
        result["value"] = None
        root.destroy()

    def on_apply() -> None:
        parsed = parse_pulse_interval(entry_var.get())
        if parsed is None:
            error_var.set("Enter a number between 10 and 300.")
            return
        error_var.set("")
        result["value"] = parsed
        root.destroy()

    ttk.Button(btn_row, text="Cancel", command=on_cancel).pack(
        side=tk.RIGHT, padx=(8, 0)
    )
    ttk.Button(btn_row, text="Apply", command=on_apply).pack(side=tk.RIGHT)
    root.bind("<Return>", lambda _e: on_apply())
    root.bind("<Escape>", lambda _e: on_cancel())
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"+{x}+{y}")

    entry.focus_set()
    entry.select_range(0, tk.END)
    root.mainloop()
    return result["value"]
