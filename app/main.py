from pathlib import Path
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .executor import build_script, WORKSPACE
from .paths import resource_path


app = FastAPI(title="EZPy2STL")

# Only answer requests addressed to localhost. A malicious web page can
# point its own hostname at 127.0.0.1 ("DNS rebinding") and then talk to
# this server from the browser -- and this server runs Python scripts. Such
# requests carry the attacker's hostname in the Host header, so refusing
# any other Host closes that route. ("testserver" is Starlette's test
# client.)
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.mount(
    "/static",
    StaticFiles(directory=str(resource_path("frontend"))),
    name="static",
)


class BuildRequest(BaseModel):
    script: str


class AutosaveRequest(BaseModel):
    script: str


# Where the crash/close recovery copy lives. Separate filename from
# workspace/model.py (the build input) so the two never collide.
AUTOSAVE_PATH = WORKSPACE / ".autosave.py"


# Whitelist of files produced by the most recent build, keyed by the name
# exposed to the frontend (path relative to WORKSPACE). Serving is limited
# to exactly these paths -- never an arbitrary filesystem path -- so a
# requested name can't escape the workspace directory.
_last_build_files: dict[str, Path] = {}


@app.get("/healthz")
def healthz():
    """Lets the desktop launcher confirm it is talking to this app and not
    to some other program that happens to be listening on the port."""
    return {"app": "EZPy2STL"}


@app.get("/")
def index():
    return FileResponse(
        resource_path("frontend/index.html")
    )


@app.get("/autosave")
def get_autosave():
    if not AUTOSAVE_PATH.exists():
        return {"content": None}

    try:
        return {"content": AUTOSAVE_PATH.read_text()}
    except OSError:
        return {"content": None}


@app.post("/autosave")
def post_autosave(request: AutosaveRequest):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    AUTOSAVE_PATH.write_text(request.script)
    return {"success": True}


@app.delete("/autosave")
def delete_autosave():
    if AUTOSAVE_PATH.exists():
        AUTOSAVE_PATH.unlink()
    return {"success": True}


@app.post("/build")
def build(request: BuildRequest):

    result = build_script(request.script)

    output = result["stdout"]

    if result["stderr"]:
        output += "\n\nERROR:\n" + result["stderr"]

    global _last_build_files
    _last_build_files = {
        str(p.relative_to(WORKSPACE)): p for p in result["files"]
    }

    return {
        "success": result["success"],
        "output": output,
        "files": sorted(_last_build_files.keys()),
    }


@app.get("/model/{name:path}")
def model(name: str):
    path = _last_build_files.get(name)

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Unknown or missing file")

    return FileResponse(
        path,
        media_type="application/octet-stream",
    )


@app.get("/download/{name:path}")
def download(name: str):
    path = _last_build_files.get(name)

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Unknown or missing file")

    return FileResponse(
        path,
        filename=Path(name).name,
        media_type="application/octet-stream",
    )


@app.post("/open-in-slicer/{name:path}")
def open_in_slicer(name: str):
    path = _last_build_files.get(name)

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Unknown or missing file")

    # macOS-only: hands the file to OrcaSlicer the same way double-clicking
    # it in Finder would (if OrcaSlicer is set as the default handler, this
    # isn't even strictly needed -- but naming it explicitly avoids relying
    # on a file-association default that might point elsewhere).
    try:
        result = subprocess.run(
            ["open", "-a", "OrcaSlicer", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="'open' command not found -- this endpoint only works on macOS.",
        )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not launch OrcaSlicer. Make sure it's installed as "
                "an Application named 'OrcaSlicer'. "
                f"({result.stderr.strip()})"
            ),
        )

    return {"success": True}
