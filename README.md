# BT KeepAlive

Windows tray app that plays a continuous, low-volume audio stream so Bluetooth headphones do not sleep and cut off the first seconds of new sounds.

## Features

- **Noise presets:** white, pink, brown, blue, violet
- **40 Hz binaural beats** with adjustable carrier (100–300 Hz)
- **Volume** presets from 0.5% to 20%
- **Launch at startup** (registry, when running the `.exe`)
- **System tray** controls: play/pause, sound, volume, quit

## Quick start (development)

```powershell
cd C:\Users\Karoly\Projects\bt-keepalive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m btkeepalive
```

Right-click the green tray icon to change sound and volume. Default is **brown noise** at **2%** volume.

## Build executable

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\build.ps1
```

Copy `dist\BTKeepAlive.exe` to a permanent folder (e.g. `%LOCALAPPDATA%\Programs\BTKeepAlive\`), run it, then enable **Launch at startup** from the tray menu.

> **Note:** “Launch at startup” only registers when running the built `.exe`, not `python -m btkeepalive`.
