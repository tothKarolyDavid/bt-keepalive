from __future__ import annotations

import tomllib
from pathlib import Path

# When pyproject.toml is absent (e.g. PyInstaller one-file); keep in sync with it.
_FALLBACK_VERSION = "1.4.0"


def _read_project_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.is_file():
        return _FALLBACK_VERSION
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


__version__ = _read_project_version()
