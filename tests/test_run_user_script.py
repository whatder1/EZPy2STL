"""
Tests for the `--run-user-script` fast path at the top of desktop.py.

Every Build in the packaged app re-launches the frozen binary with this
flag. The fast path must run the script WITHOUT importing the GUI/server
stack (pywebview, uvicorn, the FastAPI app) -- that import cost was being
paid on every single build. These tests prove it by planting fake
`webview` / `uvicorn` / `fastapi` modules that explode if imported.

Run with:  uv run pytest
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def booby_trapped_imports(tmp_path):
    """A directory that shadows the heavy modules with ones that fail."""
    trap = tmp_path / "trap"
    trap.mkdir()
    for name in ("webview", "uvicorn", "fastapi"):
        (trap / f"{name}.py").write_text(
            f'raise ImportError("heavy module {name} was imported")\n'
        )
    return trap


def run_fast_path(script_text, trap, tmp_path):
    script = tmp_path / "user_script.py"
    script.write_text(script_text)

    return subprocess.run(
        [sys.executable, str(ROOT / "desktop.py"), "--run-user-script", str(script)],
        cwd=tmp_path,
        env={"PYTHONPATH": str(trap), "PATH": "", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_runs_script_without_importing_the_gui_stack(booby_trapped_imports, tmp_path):
    result = run_fast_path('print("hello from user script")', booby_trapped_imports, tmp_path)

    assert result.returncode == 0, result.stderr
    assert "hello from user script" in result.stdout
    assert "heavy module" not in result.stderr


def test_script_runs_as_main(booby_trapped_imports, tmp_path):
    result = run_fast_path('print(__name__)', booby_trapped_imports, tmp_path)
    assert result.stdout.strip() == "__main__"


def test_exit_code_is_passed_through(booby_trapped_imports, tmp_path):
    result = run_fast_path("import sys; sys.exit(3)", booby_trapped_imports, tmp_path)
    assert result.returncode == 3


def test_exception_gives_exit_1_and_a_traceback(booby_trapped_imports, tmp_path):
    result = run_fast_path('raise ValueError("boom")', booby_trapped_imports, tmp_path)

    assert result.returncode == 1
    assert "ValueError: boom" in result.stderr


def test_fast_path_does_not_create_log_files(booby_trapped_imports, tmp_path):
    """It exits before the app's logging setup, so a build subprocess never
    opens (or rotates) the main app log."""
    run_fast_path("pass", booby_trapped_imports, tmp_path)
    assert not (tmp_path / "Library").exists()
