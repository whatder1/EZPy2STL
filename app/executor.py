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

# Output formats we detect and offer for viewing/download. STL previews
# in the 3D viewer; STEP and 3MF are listed for download / OrcaSlicer
# but not previewed (no loader for them in the current viewer).
OUTPUT_PATTERNS = ("*.stl", "*.step", "*.stp", "*.3mf")

# Wraps build123d.export_stl so every call to it also produces sibling
# .step and .3mf files from the same in-memory part -- not a lossy
# STL-to-STEP conversion, the real geometry each format's exporter
# would produce if the script had called it directly. This makes STEP
# and 3MF export automatic for every script, without editing any of
# them. Lives in its own file (rather than being prepended inline)
# so it doesn't shift the user's own script's line numbers by more
# than the one `exec(...)` line that pulls it in.
_AUTO_EXPORT_HELPER_SOURCE = '''\
# Auto-added by EZPy2STL -- not part of your script.
# Wraps build123d.export_stl so every STL export also produces a
# sibling .step and .3mf file from the same part, automatically.
# Everything here is wrapped in one try/except: if this setup fails
# for any reason (build123d not importable, a future API change,
# whatever), your actual script below still runs normally -- this is
# a bonus, not something that should ever be able to break a build.
try:
    import build123d as _ezpy2stl_build123d

    _ezpy2stl_original_export_stl = _ezpy2stl_build123d.export_stl

    def _ezpy2stl_export_stl_wrapper(part, path, *args, **kwargs):
        result = _ezpy2stl_original_export_stl(part, path, *args, **kwargs)

        path_str = str(path)
        base = path_str[:-4] if path_str.lower().endswith(".stl") else path_str

        try:
            _ezpy2stl_build123d.export_step(part, base + ".step")
        except Exception as _e:
            import sys as _sys
            print(f"[EZPy2STL] Could not auto-export STEP: {_e}", file=_sys.stderr)

        try:
            _ezpy2stl_mesher = _ezpy2stl_build123d.Mesher()
            _ezpy2stl_mesher.add_shape(part)
            _ezpy2stl_mesher.write(base + ".3mf")
        except Exception as _e:
            import sys as _sys
            print(f"[EZPy2STL] Could not auto-export 3MF: {_e}", file=_sys.stderr)

        return result

    _ezpy2stl_build123d.export_stl = _ezpy2stl_export_stl_wrapper

except Exception as _ezpy2stl_setup_error:
    import sys as _sys
    print(
        f"[EZPy2STL] Auto STEP/3MF export not enabled: {_ezpy2stl_setup_error}",
        file=_sys.stderr,
    )
'''


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


def _to_text(value) -> str:
    """subprocess.TimeoutExpired's .stdout/.stderr can come back as
    None, str, or raw bytes depending on how much output was already
    buffered when the process got killed -- not something specific to
    our code, just a CPython subtlety worth not trusting blindly."""

    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def build_script(script: str, timeout: float = 120):
    """Run the user's script in an isolated workspace directory and report
    every output file it produced (STL, STEP, or 3MF). Scripts may write
    any number of files under any relative path -- we don't assume a
    fixed output filename.

    timeout is a parameter (not a hardcoded constant) specifically so
    tests can pass a short one instead of waiting on the real 120s
    default."""

    WORKSPACE.mkdir(parents=True, exist_ok=True)

    helper_path = WORKSPACE / "_ezpy2stl_auto_export.py"
    helper_path.write_text(_AUTO_EXPORT_HELPER_SOURCE)

    script_path = WORKSPACE / "model.py"
    script_path.write_text(
        f'exec(open(r"{helper_path}").read())\n' + script
    )

    # Clear output files left over from a previous build so we only pick
    # up files this run actually produced (not stale ones from last
    # time).
    for pattern in OUTPUT_PATTERNS:
        for f in WORKSPACE.rglob(pattern):
            f.unlink()

    try:
        process = subprocess.run(
            _script_subprocess_args(script_path),
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "success": False,
            "stdout": _to_text(exc.stdout),
            "stderr": _to_text(exc.stderr) + f"\n\nBuild timed out after {timeout} seconds.",
            "files": [],
        }

    produced = sorted(
        f for pattern in OUTPUT_PATTERNS for f in WORKSPACE.rglob(pattern)
    )

    return {
        "success": process.returncode == 0 and len(produced) > 0,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "files": produced,
    }
