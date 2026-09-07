"""
Path resolution that works both when running from source (uv run ...)
and when frozen into a PyInstaller .app bundle. Relative paths like
"frontend" assume cwd == project root, which is true in dev but NOT
guaranteed once launched from Finder as a double-clickable app -- and
writable data (build output) must never live inside the bundle itself,
since a signed .app is effectively read-only in normal use.
"""

import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_path(relative: str) -> Path:
    """Read-only bundled resources (e.g. the frontend/ static files)."""

    if is_frozen():
        # PyInstaller --onefile extracts to sys._MEIPASS at runtime.
        # --onedir / .app bundles instead place bundled data alongside
        # the frozen executable.
        base = Path(getattr(sys, "_MEIPASS", None) or Path(sys.executable).resolve().parent)
    else:
        base = Path(__file__).resolve().parent.parent

    return base / relative


def app_support_dir() -> Path:
    """Writable, per-user location for build output. Only used when
    frozen -- dev mode keeps writing next to the project like before,
    since that's the workflow you're already used to."""

    path = Path.home() / "Library" / "Application Support" / "EZPy2STL"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    """Where startup/crash logs go. Used regardless of frozen state --
    console=False in the packaged .app means a launch failure is
    otherwise completely silent (no Terminal, no error, just nothing),
    so this is the only way to see what happened."""

    path = Path.home() / "Library" / "Logs" / "EZPy2STL"
    path.mkdir(parents=True, exist_ok=True)
    return path
