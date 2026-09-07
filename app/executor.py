import subprocess
import sys
from pathlib import Path

from .paths import is_frozen, app_support_dir


BASE_DIR = Path(__file__).resolve().parent.parent

# Dev mode keeps the workspace next to the project (what you're already
# used to). Frozen mode can't write inside the .app bundle itself, so it
# goes to a normal per-user data directory instead.
if is_frozen():
    WORKSPACE = app_support_dir() / "workspace"
else:
    WORKSPACE = BASE_DIR / "workspace"


def _script_subprocess_args(script_path: Path) -> list[str]:

    if is_frozen():
        # sys.executable is this frozen app's own bootloader here, not a
        # general-purpose Python interpreter -- it can't run
        # `<bootloader> script.py` the way `python script.py` works. So
        # instead we re-launch the same frozen binary with a flag that
        # desktop.py's entry point recognizes: it runs the script via
        # runpy in that fresh process instead of starting the GUI again.
        # This is the same self-relaunch pattern PyInstaller documents
        # for multiprocessing.freeze_support().
        return [sys.executable, "--run-user-script", str(script_path)]

    return [sys.executable, str(script_path)]


def build_script(script: str):
    """Run the user's script in an isolated workspace directory and report
    every .stl file it produced. Scripts may write any number of files
    under any relative path -- we don't assume a fixed output filename."""

    WORKSPACE.mkdir(parents=True, exist_ok=True)

    script_path = WORKSPACE / "model.py"
    script_path.write_text(script)

    # Clear STL files left over from a previous build so we only pick up
    # files this run actually produced (not stale ones from last time).
    for stl in WORKSPACE.rglob("*.stl"):
        stl.unlink()

    try:
        process = subprocess.run(
            _script_subprocess_args(script_path),
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "success": False,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + "\n\nBuild timed out after 120 seconds.",
            "files": [],
        }

    produced = sorted(WORKSPACE.rglob("*.stl"))

    return {
        "success": process.returncode == 0 and len(produced) > 0,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "files": produced,
    }
