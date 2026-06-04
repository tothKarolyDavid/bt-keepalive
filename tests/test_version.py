import tomllib
from pathlib import Path

from btkeepalive import __version__
from btkeepalive.__init__ import _FALLBACK_VERSION, _read_project_version


def _pyproject_version() -> str:
    root = Path(__file__).resolve().parents[1]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_version_matches_pyproject():
    assert __version__ == _pyproject_version()


def test_fallback_version_matches_pyproject():
    assert _FALLBACK_VERSION == _pyproject_version()


def test_version_without_pyproject(monkeypatch):
    class MissingPyprojectPath(Path):
        def is_file(self) -> bool:
            return False

    def fake_path(*args, **kwargs):
        return MissingPyprojectPath(*args, **kwargs)

    monkeypatch.setattr("btkeepalive.__init__.Path", fake_path)
    assert _read_project_version() == _pyproject_version()
