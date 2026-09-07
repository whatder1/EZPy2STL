# Changelog

All notable changes to EZPy2STL are recorded here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Startup/crash logging to `~/Library/Logs/EZPy2STL/app.log`. The
  packaged app runs with no console window, so a launch failure was
  previously completely silent -- this is the only way to see what
  happened.
- Autosave: the script editor is saved to a recovery file every few
  seconds. On next launch, if a recovery copy exists, a banner offers
  to restore or discard it (never silently, so it can't clobber an
  intentional blank start).
- Recent files: the last 8 opened/saved files are tracked and
  available from a dropdown next to Open.
- Syntax highlighting and line numbers in the script editor (CodeMirror).
- STEP and 3MF files are now detected as build output alongside STL
  (previously STL-only). Non-STL formats are listed for
  download/OrcaSlicer but not previewed -- no loader for them in the
  current 3D viewer.
- `tests/test_executor.py` (pytest) and `frontend/params.test.mjs`
  (Node's built-in test runner) covering the workspace-isolation logic
  and parameter-detection logic respectively.
- `frontend/params.js`: parameter-parsing logic extracted out of
  `app.js` so it's testable without a browser.

## [0.2.1]
### Added
- CI check that builds (but doesn't publish) on every pull request
  touching dependency or app files -- catches a broken Dependabot
  update before merging, not after.
- Documented the merge discipline in the README: pull a Dependabot
  branch and smoke-test/rebuild locally before merging, one PR at a
  time.

## [0.2.0]
### Fixed
- `lib3mf`'s compiled binary wasn't being bundled by PyInstaller
  (`collect_all` didn't reach it), which broke every build in the
  packaged `.app` since `import build123d` pulls it in unconditionally
  via `build123d.mesher`.
### Added
- Draggable panel dividers: script/viewer split, and within the left
  column, Parameters/script and script/console splits.
- Native window is explicitly resizable.
- Editor starts blank instead of pre-loading a default example script.

## [0.1.0]
Initial release.
- FastAPI + build123d backend; converts a Python build123d script to
  STL and previews it in a Three.js viewer, oriented to match how it
  would sit on a print bed.
- Native desktop shell via pywebview (`desktop.py`), with real
  Open/Save/Save As dialogs -- not possible from a plain browser tab,
  since browsers never expose a picked file's real filesystem path to
  JavaScript.
- Multi-file build output support (a script can produce more than one
  STL).
- "Open in OrcaSlicer" per output file.
- Auto-detected parameter panel: any top-level `NAME = value  #
  comment` line in the loaded script becomes an editable form control.
- Standalone `.app` packaging via PyInstaller, bundling build123d/OCP
  directly (no separate Python install required to run it).
- GitHub Actions: automated `.app`/`.dmg` build + GitHub Release on
  tag push; Dependabot for `uv` and `github-actions` ecosystems.
