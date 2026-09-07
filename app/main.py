from pathlib import Path
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .executor import build_script, WORKSPACE
from .paths import resource_path


app = FastAPI(title="EZPy2STL")

app.mount(
    "/static",
    StaticFiles(directory=str(resource_path("frontend"))),
    name="static",
)


class BuildRequest(BaseModel):
    script: str


# Whitelist of files produced by the most recent build, keyed by the name
# exposed to the frontend (path relative to WORKSPACE). Serving is limited
# to exactly these paths -- never an arbitrary filesystem path -- so a
# requested name can't escape the workspace directory.
_last_build_files: dict[str, Path] = {}


@app.get("/")
def index():
    return FileResponse(
        resource_path("frontend/index.html")
    )


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
