"""Generate assets/icon.ico for the tray, PyInstaller exe, and Inno Setup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btkeepalive.icon_art import ico_sizes, render_master_for_ico

OUT = ROOT / "assets" / "icon.ico"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = render_master_for_ico()
    img.save(OUT, format="ICO", sizes=ico_sizes())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
