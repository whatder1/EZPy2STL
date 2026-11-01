"""
Native desktop launcher for EZPy2STL.

Runs the existing FastAPI app (unchanged) in a background thread, then
opens it in a real OS window via pywebview instead of a browser tab.
This is what makes Open/Save use native macOS file dialogs -- browsers
never expose a picked file's real filesystem path to JavaScript, and
Safari specifically opposes the File System Access API that would let
a webpage save back to an exact path. A native window has no such
restriction: the dialogs run in Python and hand back real paths.

Run with:  uv run python desktop.py
"""

import json
import logging
import logging.handlers
import os
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request

import uvicorn
import webview

from app.main import app as fastapi_app
from app.paths import app_support_dir, log_dir


# ------------------------------------------------------------
# LOGGING
#
# console=False in the packaged .app means a launch or startup
# failure is otherwise completely silent -- no Terminal window, no
# stderr anyone sees, the app just quits. This is the only visibility
# into that. Runs in dev mode too; it's harmless there and doesn't
# replace the terminal output you already see.
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            log_dir() / "app.log",
            maxBytes=2_000_000,
            backupCount=3,
        ),
    ],
)

logger = logging.getLogger("ezpy2stl.desktop")


def _log_uncaught(exc_type, exc_value, exc_tb):
    logger.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_tb)
    )


sys.excepthook = _log_uncaught


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"

PY_FILE_TYPES = ("Python Files (*.py)", "All files (*.*)")
IMAGE_FILE_TYPES = (
    "Images (*.svg;*.png;*.jpg;*.jpeg)",
    "All files (*.*)",
)

RECENT_FILES_PATH = app_support_dir() / "recent_files.json"
MAX_RECENT_FILES = 8


def _load_recent():
    if not RECENT_FILES_PATH.exists():
        return []

    try:
        paths = json.loads(RECENT_FILES_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return []

    # Prune entries whose file no longer exists, and persist the
    # cleaned-up list so this doesn't need to happen on every call.
    existing = [p for p in paths if os.path.exists(p)]

    if existing != paths:
        _save_recent(existing)

    return existing


def _save_recent(paths):
    try:
        RECENT_FILES_PATH.write_text(json.dumps(paths))
    except OSError:
        logger.warning("Could not write recent files list", exc_info=True)


def _add_recent(path):
    paths = _load_recent()
    paths = [p for p in paths if p != path]
    paths.insert(0, path)
    _save_recent(paths[:MAX_RECENT_FILES])


class Api:
    """Exposed to the frontend as window.pywebview.api.<method>(...)."""

    def open_file(self):
        window = webview.windows[0]

        result = window.create_file_dialog(
            webview.FileDialog.OPEN,
            file_types=PY_FILE_TYPES,
        )

        if not result:
            return None

        path = result[0]
        return self._read_path(path)

    def pick_image(self):
        """Native file picker for the parameter panel's Browse button.
        Returns the chosen path as a string (or None if cancelled). It
        deliberately returns only the path, never file contents -- the
        script reads the file itself when it runs."""

        window = webview.windows[0]

        result = window.create_file_dialog(
            webview.FileDialog.OPEN,
            file_types=IMAGE_FILE_TYPES,
        )

        if not result:
            return None

        return result[0]

    def open_recent(self, path):
        """Open a path from the recent-files list. Only reads paths
        that are actually tracked as recent -- this is invoked from
        the frontend, and validating against our own known-good list
        (rather than trusting an arbitrary path string) keeps this
        from becoming a general-purpose arbitrary-file-read call."""

        if path not in _load_recent():
            return {"error": "Not a recognized recent file."}

        return self._read_path(path)

    def _read_path(self, path):
        try:
            with open(path, "r") as f:
                content = f.read()
        except OSError as exc:
            return {"error": str(exc)}

        _add_recent(path)

        return {
            "path": path,
            "name": os.path.basename(path),
            "content": content,
        }

    def get_recent_files(self):
        return [
            {"path": p, "name": os.path.basename(p)}
            for p in _load_recent()
        ]

    def save_file(self, content, path):
        """Overwrite an already-known path -- no dialog. Used for 'Save'
        once a file has been opened or 'Save As'-d at least once."""

        try:
            with open(path, "w") as f:
                f.write(content)
        except OSError as exc:
            return {"error": str(exc)}

        _add_recent(path)

        return {"path": path}

    def save_file_as(self, content):
        window = webview.windows[0]

        result = window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename="model.py",
            file_types=PY_FILE_TYPES,
        )

        if not result:
            return None

        path = result[0] if isinstance(result, (list, tuple)) else result

        try:
            with open(path, "w") as f:
                f.write(content)
        except OSError as exc:
            return {"error": str(exc)}

        _add_recent(path)

        return {"path": path}

    def download_file(self, name):
        """Save a built output file (STL/STEP/3MF) to disk via a native
        dialog. Not routed through the browser's <a download> anchor --
        that attribute is unreliable inside WKWebView (the engine
        pywebview uses on macOS): it works fine in a real browser tab,
        which is why it worked before switching to the desktop app, but
        not reliably inside the embedded webview."""

        try:
            with urllib.request.urlopen(
                f"{URL}/download/{urllib.parse.quote(name)}", timeout=10
            ) as response:
                data = response.read()
        except urllib.error.URLError as exc:
            return {"error": f"Could not fetch {name}: {exc}"}

        window = webview.windows[0]

        suggested = os.path.basename(name)
        extension = os.path.splitext(suggested)[1].lstrip(".") or "stl"

        result = window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=suggested,
            file_types=(f"{extension.upper()} files (*.{extension})",),
        )

        if not result:
            return None

        path = result[0] if isinstance(result, (list, tuple)) else result

        try:
            with open(path, "wb") as f:
                f.write(data)
        except OSError as exc:
            return {"error": str(exc)}

        return {"path": path}


def start_server():
    try:
        uvicorn.run(fastapi_app, host=HOST, port=PORT, log_level="warning")
    except Exception:
        logger.critical("Server thread crashed", exc_info=True)


def wait_for_server(timeout=10):
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            urllib.request.urlopen(URL, timeout=0.5)
            return True
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.1)

    return False


def run_user_script(path: str) -> int:
    """Entry point used when this same frozen binary is re-invoked as a
    subprocess to run one build123d script in isolation (see
    app/executor.py's _script_subprocess_args). Only reachable in a
    frozen build -- in dev mode, executor.py just runs a real
    `python script.py` instead and this is never called.

    Runs the target file the same way `python path` would (fresh
    __main__ namespace), and translates the outcome into a process exit
    code so the parent's subprocess.run(...).returncode still means
    what it always has."""

    import runpy

    try:
        runpy.run_path(path, run_name="__main__")
    except SystemExit as exc:
        if exc.code is None:
            return 0
        return exc.code if isinstance(exc.code, int) else 1
    except Exception:
        traceback.print_exc()
        return 1

    return 0


def main():
    logger.info("Starting EZPy2STL")

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    if not wait_for_server():
        logger.critical(f"Server did not start at {URL} within the timeout.")
        raise RuntimeError(
            f"Server did not start at {URL} within the timeout."
        )

    logger.info("Server up, opening window")

    api = Api()

    webview.create_window(
        "EZPy2STL",
        URL,
        js_api=api,
        width=1440,
        height=920,
        min_size=(1000, 650),
        resizable=True,
    )

    webview.start()

    logger.info("Window closed, exiting")


if __name__ == "__main__":

    if len(sys.argv) >= 3 and sys.argv[1] == "--run-user-script":
        sys.exit(run_user_script(sys.argv[2]))
    else:
        try:
            main()
        except Exception:
            logger.critical("Fatal error during startup", exc_info=True)
            raise
