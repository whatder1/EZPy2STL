# EZPy2STL

A local macOS app for iterating on [build123d](https://build123d.readthedocs.io/) Python scripts: edit a script, see the resulting model in a 3D viewer oriented the way it'll sit on a print bed, tweak the script's top-level constants through an auto-generated parameter panel, build, then download the generated files (STL, plus STEP/3MF) or send them straight to OrcaSlicer.

It runs two ways:
- **From source**, as a FastAPI backend with a native window (via [pywebview](https://pywebview.flowrl.com/)) — this is the normal development setup.
- **As a standalone `.app`**, with build123d/OCP frozen in via PyInstaller, so it runs without a Python environment installed at all.

## Why it exists

Editing a build123d script normally means round-tripping between an editor, a terminal, and a separate STL viewer. This collapses that into one window: script on the left, live 3D preview on the right, with native Open/Save and a one-click handoff to OrcaSlicer.

## Requirements

- macOS. Native Open/Save dialogs and "Open in OrcaSlicer" are macOS-specific (they shell out to `open -a OrcaSlicer` and use pywebview's Cocoa backend). The FastAPI + build123d core is not inherently macOS-only, but this repo's tooling (the `.app` build, the OrcaSlicer integration) assumes it.
- Python 3.11 to 3.14 (see `requires-python` in `pyproject.toml`). 3.10 was dropped so the lockfile carries one patched version of each package; the 3.10-only versions of Pillow and dnspython were stuck on releases with known vulnerabilities.
- [uv](https://docs.astral.sh/uv/) for dependency management — this project doesn't use plain `pip`/`venv` directly.

## Quick start (development mode)

```bash
git clone https://github.com/whatder1/EZPy2STL.git
cd EZPy2STL
uv sync
uv run python desktop.py
```

This opens a native window backed by a local FastAPI server. The editor starts blank: open a `.py` script (or paste one in), adjust any top-level constants in the Parameters panel, click Build, and use Save / Save As / Open in OrcaSlicer as needed.

There's also a browser-only mode, mainly useful for quick debugging with dev tools open:

```bash
uv run uvicorn app.main:app --reload
```

then visit `http://127.0.0.1:8000` (the desktop app picks a free port on its own; only this browser mode uses 8000). Open/Save won't fully work here — browsers deliberately don't expose a picked file's real filesystem path to JavaScript, and Safari specifically opposes the newer API that would allow saving back to an exact path. Prefer `desktop.py` for real use.

## Building the standalone `.app`

```bash
./build_app.sh
```

This installs PyInstaller, then freezes build123d/OCP, pywebview, FastAPI, and the frontend into `dist/EZPy2STL.app`.

To also produce a drag-to-Applications disk image:

```bash
./make_dmg.sh
```

That writes `dist/EZPy2STL-<version>.dmg`, with the version read from `pyproject.toml` (for example `dist/EZPy2STL-0.7.2.dmg`). Release builds on GitHub use the same name.

**First launch will be blocked by Gatekeeper once**, since this isn't code-signed:
- Right-click the app → Open → Open, or
- `xattr -cr 'dist/EZPy2STL.app'`

This isn't a bug to fix — genuinely frictionless distribution requires Apple code signing + notarization, which needs a paid Apple Developer Program membership. Without that, this one-time prompt is unavoidable for any app built this way, not just this one.

If cloning strips the executable bit off the shell scripts, restore it with `chmod +x build_app.sh make_dmg.sh`.

## Keeping dependencies up to date

Everything is pinned in `pyproject.toml` / `uv.lock`. Add a new dependency to `pyproject.toml`, run `uv lock`, and if it ships native code or data files, add it to the `collect_all(...)` list in `ezpy2stl.spec` (this is how `lib3mf`, `PIL` and `potrace` are bundled). Three ways to stay current as build123d, pywebview, FastAPI, and PyInstaller release new versions:

1. **Automatic (already set up):** `.github/dependabot.yml` has GitHub check weekly for new versions of everything in `pyproject.toml`/`uv.lock`, and open a pull request per update. It also watches the versions pinned in the GitHub Actions workflow.

   **Before merging any Dependabot PR:** `.github/workflows/build-macos-app.yml` now runs a build-only check (no release published) on every PR that touches `pyproject.toml`, `uv.lock`, `ezpy2stl.spec`, or the app/frontend code — so a red X on the PR means don't merge it, something broke. But CI passing isn't the same as verified working: pull the branch and run the same steps yourself before trusting it —
   ```bash
   git fetch origin
   git checkout <dependabot-branch-name>
   uv sync
   uv run python desktop.py   # smoke-test in dev mode
   ./build_app.sh              # rebuild the actual .app and try it for real
   ```
   Merge one PR at a time, not batched — if something breaks, you'll know exactly which update did it. This isn't a hypothetical: both the `requires-python` mismatch and the `lib3mf` packaging break earlier in this project's history were exactly this kind of routine-looking version bump that silently broke something CI alone wouldn't have caught before this check existed.

2. **Manual, on demand:**
   ```bash
   uv lock --upgrade         # recompute uv.lock against the newest versions pyproject.toml allows
   uv sync
   uv run python desktop.py  # smoke-test in dev mode first
   ./build_app.sh            # then rebuild the .app before trusting it further
   ```
   Pay closest attention after upgrading **build123d**/**cadquery-ocp** (the CAD kernel) or **pywebview** (the native window/dialog layer) — these are the two most likely to need a follow-up tweak to `ezpy2stl.spec`'s `collect_all(...)` list if their internal module structure changes between versions.

3. **Front-end libraries** (Three.js, CodeMirror, the IBM Plex fonts) are copied into `frontend/vendor/` rather than loaded from a CDN, so the app works offline and no third-party host can inject code into a page that can run Python. They aren't managed by uv or Dependabot: to upgrade one, follow `frontend/vendor/README.md` and update the versions listed there.

## Architecture

- `app/main.py` — FastAPI backend: serves the frontend, runs submitted scripts, serves the resulting STL(s).
- `app/executor.py` — runs a script in an isolated subprocess. In dev mode that's a real Python interpreter; in the frozen `.app` it's a self-relaunch of the same frozen binary with a `--run-user-script` flag, since a frozen executable can't be invoked as `python script.py` the way a real interpreter can. See the comments in this file for the full reasoning.
- `app/paths.py` — resolves file paths correctly whether running from source or from inside the frozen `.app` (bundled resources vs. a writable per-user data directory).
- `desktop.py` — the native app entry point: starts the FastAPI server in a background thread, opens a pywebview window pointing at it, and exposes native Open/Save dialogs to the frontend via `window.pywebview.api`.
- `frontend/` — the UI itself: script editor, an auto-detected parameter panel (built from any `NAME = value  # comment` lines in the loaded script), a Three.js viewer, the file list/download/OrcaSlicer controls, and a View menu (toolbar) for showing/hiding any of those panels. `frontend/vendor/` holds the bundled third-party libraries.
- `ezpy2stl.spec` — the PyInstaller spec for the standalone `.app`.
- `resources/AppIcon.icns` — the app icon.

## Running scripts: workspace, files and images

- Scripts run with their working directory set to a dedicated workspace folder (in the frozen app: `~/Library/Application Support/EZPy2STL/workspace`), not next to the `.py` file. Output files (`*.stl`, `*.step`, `*.3mf`) written there appear in the file list.
- **Use full paths for any input file** a script reads (an SVG, PNG or JPG for example), e.g. `"/Users/you/Documents/logo.svg"`. A bare filename only works if the file is in the workspace folder.
- Parameters that hold a file path (names ending in `IMAGE`, `PATH` or `FILE`, or a `[browse]` tag in the comment) get a **Browse...** button in the Parameters panel. It needs the desktop app; in a plain browser tab, paste a full path.
- Two more comment tags shape the Parameters panel (they're ordinary `#` comments, so the script still runs anywhere):
  - `# [choice: blank|text|image] hint` turns a string constant into a **dropdown** of those values.
  - `# [when LID_ART=text] hint` shows that row only while `LID_ART` equals `text` (works with dropdowns and True/False switches), so unused settings disappear.
- `pillow` and `potracer` are bundled, so scripts can load PNG/JPG files and trace them into vector shapes (the card-box generator's `LID_IMAGE` option uses this).
- Logs: `~/Library/Logs/EZPy2STL/app.log`. Include it when reporting a bug.

## Known limitations

- macOS only, by design of the current tooling.
- Ad-hoc signed only, not notarized — see the Gatekeeper note above.
- **Security scope, stated plainly:** the backend executes arbitrary Python you give it, with your full user-account permissions. That's an acceptable trade-off for a single-user local tool bound to `127.0.0.1` — never expose this past localhost without adding real authentication first. Mitigations in place: it listens only on localhost on a random port, refuses any request whose `Host` header isn't localhost (blocks DNS-rebinding from web pages), serves only files the last build produced, and loads no third-party scripts. It does **not** authenticate other programs running as you on the same Mac.
- No script version history. Unsaved editor changes are autosaved and offered back on next launch, but that is a safety net, not history: use Save/Save As.
- Every "Build" click in the frozen `.app` re-imports the full FastAPI/pywebview stack before running your script (a side effect of the self-relaunch approach above), so builds are somewhat slower there than in dev mode.

## Tests

```bash
uv run --extra test pytest        # backend, file-serving whitelist, Host check, build fast path
node --test frontend/params.test.mjs   # parameter parsing
```

CI runs both on every pull request and tag.

## Releases and versioning

`.github/workflows/build-macos-app.yml` builds `EZPy2STL.app` + `.dmg` on GitHub's macOS runners (currently `macos-15`; GitHub retires old runner images, so expect to bump this label now and then) and attaches them to a GitHub Release whenever you push a version tag. Pull requests get tests plus a build-only check with no release. A tag build first checks that the tag matches the version in `pyproject.toml` and `ezpy2stl.spec` and that `CHANGELOG.md` has a section for it, then publishes the `.dmg` with that section as the release notes. Only the final publish step has write access.

Each push that should ship gets its own version: bump `version` in `pyproject.toml`, `CFBundleShortVersionString` in `ezpy2stl.spec`, and add an entry to `CHANGELOG.md`, then:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Don't move or re-push a tag after its build has run: the release is already published, so cut the next version instead. Delete the workflow file if you'd rather not have automated builds.

See `CHANGELOG.md` for what changed in each version.

## License

Copyright (C) 2026 Eli Nussbaum.

EZPy2STL is free software, released under the **GNU General Public License, version 2 or (at your option) any later version** (GPL-2.0-or-later). See [`LICENSE`](LICENSE).

It bundles third-party packages under their own licenses, including build123d and OCP (Apache-2.0), potracer (GPLv2+), Pillow (MIT-CMU) and lib3mf (BSD). Full licence texts for every bundled package are in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), which is also copied into the `.app`. Regenerate it whenever dependencies change (it reads the packages installed in your environment, so run it from the one you build with):

```bash
uv sync --extra build
uv run python tools/generate_notices.py
```

The "or later" wording matters: Apache-2.0 code is only compatible with GPL version 3, so recipients need the option of GPLv3 for the combined app.

## Update check

On launch the app asks GitHub whether a newer release exists and, if so,
shows a banner with a Download button (it opens the release page; you
install the new DMG as usual). It makes one request to `api.github.com`
and sends nothing identifying. To turn it off, launch with
`EZPY2STL_NO_UPDATE_CHECK=1`.
