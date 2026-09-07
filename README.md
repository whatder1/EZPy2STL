# EZPy2STL

A local macOS app for iterating on [build123d](https://build123d.readthedocs.io/) Python scripts: edit a script, see the resulting model in a 3D viewer oriented the way it'll sit on a print bed, tweak the script's top-level constants through an auto-generated parameter panel, build, then download the STL or send it straight to OrcaSlicer.

It runs two ways:
- **From source**, as a FastAPI backend with a native window (via [pywebview](https://pywebview.flowrl.com/)) — this is the normal development setup.
- **As a standalone `.app`**, with build123d/OCP frozen in via PyInstaller, so it runs without a Python environment installed at all.

## Why it exists

Editing a build123d script normally means round-tripping between an editor, a terminal, and a separate STL viewer. This collapses that into one window: script on the left, live 3D preview on the right, with native Open/Save and a one-click handoff to OrcaSlicer.

## Requirements

- macOS. Native Open/Save dialogs and "Open in OrcaSlicer" are macOS-specific (they shell out to `open -a OrcaSlicer` and use pywebview's Cocoa backend). The FastAPI + build123d core is not inherently macOS-only, but this repo's tooling (the `.app` build, the OrcaSlicer integration) assumes it.
- Python 3.9+
- [uv](https://docs.astral.sh/uv/) for dependency management — this project doesn't use plain `pip`/`venv` directly.

## Quick start (development mode)

```bash
git clone <this-repo-url>
cd ezpy2stl
uv sync
uv run python desktop.py
```

This opens a native window backed by a local FastAPI server. Open a `.py` script (or edit the default one), adjust any top-level constants in the Parameters panel, click Build, and use Save / Save As / Open in OrcaSlicer as needed.

There's also a browser-only mode, mainly useful for quick debugging with dev tools open:

```bash
uv run uvicorn app.main:app --reload
```

then visit `http://127.0.0.1:8000`. Open/Save won't fully work here — browsers deliberately don't expose a picked file's real filesystem path to JavaScript, and Safari specifically opposes the newer API that would allow saving back to an exact path. Prefer `desktop.py` for real use.

## Building the standalone `.app`

```bash
./build_app.sh
```

This installs PyInstaller, then freezes build123d/OCP, pywebview, FastAPI, and the frontend into `dist/EZPy2STL.app`.

To also produce a drag-to-Applications disk image:

```bash
./make_dmg.sh
```

**First launch will be blocked by Gatekeeper once**, since this isn't code-signed:
- Right-click the app → Open → Open, or
- `xattr -cr 'dist/EZPy2STL.app'`

This isn't a bug to fix — genuinely frictionless distribution requires Apple code signing + notarization, which needs a paid Apple Developer Program membership. Without that, this one-time prompt is unavoidable for any app built this way, not just this one.

If cloning strips the executable bit off the shell scripts, restore it with `chmod +x build_app.sh make_dmg.sh`.

## Keeping dependencies up to date

Everything is pinned in `pyproject.toml` / `uv.lock`. Three ways to stay current as build123d, pywebview, FastAPI, and PyInstaller release new versions:

1. **Automatic (already set up):** `.github/dependabot.yml` has GitHub check weekly for new versions of everything in `pyproject.toml`/`uv.lock`, and open a pull request per update. It also watches the versions pinned in the GitHub Actions workflow. Review each PR, and prefer merging one at a time — if something breaks, you'll know which update did it.

2. **Manual, on demand:**
   ```bash
   uv lock --upgrade         # recompute uv.lock against the newest versions pyproject.toml allows
   uv sync
   uv run python desktop.py  # smoke-test in dev mode first
   ./build_app.sh            # then rebuild the .app before trusting it further
   ```
   Pay closest attention after upgrading **build123d**/**cadquery-ocp** (the CAD kernel) or **pywebview** (the native window/dialog layer) — these are the two most likely to need a follow-up tweak to `ezpy2stl.spec`'s `collect_all(...)` list if their internal module structure changes between versions.

3. **Three.js**, used only in the browser frontend, is pinned separately via CDN URLs in `frontend/index.html` (the import map) and `frontend/app.js` — it isn't managed by uv at all. Bump the version number in both places together if you want a newer release.

## Architecture

- `app/main.py` — FastAPI backend: serves the frontend, runs submitted scripts, serves the resulting STL(s).
- `app/executor.py` — runs a script in an isolated subprocess. In dev mode that's a real Python interpreter; in the frozen `.app` it's a self-relaunch of the same frozen binary with a `--run-user-script` flag, since a frozen executable can't be invoked as `python script.py` the way a real interpreter can. See the comments in this file for the full reasoning.
- `app/paths.py` — resolves file paths correctly whether running from source or from inside the frozen `.app` (bundled resources vs. a writable per-user data directory).
- `desktop.py` — the native app entry point: starts the FastAPI server in a background thread, opens a pywebview window pointing at it, and exposes native Open/Save dialogs to the frontend via `window.pywebview.api`.
- `frontend/` — the UI itself: script editor, an auto-detected parameter panel (built from any `NAME = value  # comment` lines in the loaded script), a Three.js viewer, and the file list/download/OrcaSlicer controls.
- `ezpy2stl.spec` — the PyInstaller spec for the standalone `.app`.
- `resources/AppIcon.icns` — the app icon.

## Known limitations

- macOS only, by design of the current tooling.
- Not code-signed or notarized — see the Gatekeeper note above.
- **Security scope, stated plainly:** the backend executes arbitrary Python you give it, with your full user-account permissions. That's an acceptable trade-off for a single-user local tool bound to `127.0.0.1` — never expose this past localhost without adding real authentication first.
- No script version history — closing the app loses unsaved editor changes unless you've used Save/Save As.
- Every "Build" click in the frozen `.app` re-imports the full FastAPI/pywebview stack before running your script (a side effect of the self-relaunch approach above), so builds are somewhat slower there than in dev mode.

## Optional: automated `.app` builds on tag push

`.github/workflows/build-macos-app.yml` builds `EZPy2STL.app` + `.dmg` on GitHub's macOS runners and attaches them to a GitHub Release whenever you push a version tag:

```bash
git tag v0.2.0
git push --tags
```

This hasn't been exercised on a real GitHub Actions run — the first tag push is the actual test. If it fails, the Actions log will point at the real cause; that's worth more than guessing at a fix in advance. Delete the workflow file if you'd rather not have it.
