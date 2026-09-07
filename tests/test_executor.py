"""
Tests for app/executor.py -- specifically the workspace isolation and
multi-format output detection logic. These use trivial scripts that
write fake files without importing build123d, so they run fast and
don't need OCP installed to verify the *logic* (isolation, cleanup,
timeout handling) is correct.

Run with:  uv run pytest
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.executor import build_script, WORKSPACE  # noqa: E402


@pytest.fixture(autouse=True)
def clean_workspace():
    """Every test starts from an empty workspace."""
    if WORKSPACE.exists():
        for f in WORKSPACE.iterdir():
            if f.is_file():
                f.unlink()
    yield


def test_simple_script_succeeds_and_reports_stl():
    script = 'open("box.stl", "w").write("fake stl")'
    result = build_script(script, timeout=10)

    assert result["success"] is True
    assert [f.name for f in result["files"]] == ["box.stl"]


def test_detects_stl_step_and_3mf():
    script = """
open("box.stl", "w").write("x")
open("box.step", "w").write("x")
open("box.3mf", "w").write("x")
open("notes.txt", "w").write("x")
"""
    result = build_script(script, timeout=10)

    names = sorted(f.name for f in result["files"])
    assert names == ["box.3mf", "box.step", "box.stl"]


def test_no_output_files_means_failure_even_if_script_succeeds():
    script = 'print("ran fine but wrote nothing")'
    result = build_script(script, timeout=10)

    assert result["success"] is False
    assert result["files"] == []


def test_script_error_is_captured_in_stderr():
    script = 'raise ValueError("deliberate failure")'
    result = build_script(script, timeout=10)

    assert result["success"] is False
    assert "ValueError" in result["stderr"]
    assert "deliberate failure" in result["stderr"]


def test_stale_files_cleared_between_builds():
    build_script('open("first.stl", "w").write("x")', timeout=10)
    result = build_script('open("second.stl", "w").write("x")', timeout=10)

    names = sorted(f.name for f in result["files"])
    assert names == ["second.stl"], (
        "a file from the previous build leaked into this one's results"
    )


def test_timeout_is_reported_cleanly():
    script = "import time; time.sleep(5)"
    result = build_script(script, timeout=1)

    assert result["success"] is False
    assert "timed out" in result["stderr"].lower()


def test_script_runs_with_workspace_as_cwd():
    # A script using a bare relative filename should land in WORKSPACE,
    # not the caller's cwd -- this is the isolation guarantee that
    # prevents stray output files scattering into the project root
    # (the exact bug this whole workspace-isolation design fixed).
    script = 'open("here.stl", "w").write("x")'
    build_script(script, timeout=10)

    assert (WORKSPACE / "here.stl").exists()


@pytest.fixture
def fake_build123d(tmp_path, monkeypatch):
    """A minimal stand-in for build123d so the export_stl auto-wrap
    logic can be tested without the real (huge) OCP dependency."""

    fake_pkg_dir = tmp_path / "fake_pkgs"
    fake_pkg_dir.mkdir()

    (fake_pkg_dir / "build123d.py").write_text('''
def export_stl(part, path, *args, **kwargs):
    with open(path, "w") as f:
        f.write(f"fake stl for {part}")

def export_step(part, path, *args, **kwargs):
    with open(path, "w") as f:
        f.write(f"fake step for {part}")

class Mesher:
    def __init__(self, *args, **kwargs):
        self._shapes = []

    def add_shape(self, shape, *args, **kwargs):
        self._shapes.append(shape)

    def write(self, path):
        with open(path, "w") as f:
            f.write(f"fake 3mf for {self._shapes}")
''')

    monkeypatch.setenv("PYTHONPATH", str(fake_pkg_dir))
    yield


def test_auto_exports_step_and_3mf_alongside_stl(fake_build123d):
    script = 'from build123d import *\nexport_stl("part", "model.stl")\n'
    result = build_script(script, timeout=10)

    names = sorted(f.name for f in result["files"])
    assert names == ["model.3mf", "model.step", "model.stl"], (
        "a plain export_stl() call should automatically also produce "
        "STEP and 3MF, regardless of what the script itself asked for"
    )
    assert result["success"] is True
