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

import os
import sys
import threading
import time
import urllib.error
import urllib.request

import uvicorn
import webview

from app.main import app as fastapi_app


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"

PY_FILE_TYPES = ("Python Files (*.py)", "All files (*.*)")


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

        try:
            with open(path, "r") as f:
                content = f.read()
        except OSError as exc:
            return {"error": str(exc)}

        return {
            "path": path,
            "name": os.path.basename(path),
            "content": content,
        }

    def save_file(self, content, path):
        """Overwrite an already-known path -- no dialog. Used for 'Save'
        once a file has been opened or 'Save As'-d at least once."""

        try:
            with open(path, "w") as f:
                f.write(content)
        except OSError as exc:
            return {"error": str(exc)}

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

        return {"path": path}


def start_server():
    uvicorn.run(fastapi_app, host=HOST, port=PORT, log_level="warning")


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
    import traceback

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
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    if not wait_for_server():
        raise RuntimeError(
            f"Server did not start at {URL} within the timeout."
        )

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


if __name__ == "__main__":

    if len(sys.argv) >= 3 and sys.argv[1] == "--run-user-script":
        sys.exit(run_user_script(sys.argv[2]))
    else:
        main()
