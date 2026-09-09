# Changelog

All notable changes to EZPy2STL are recorded here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

## [0.4.2]

### Changed
- Toolbar button order: Open, Build, Save, Save As -- Build moved up
  next to Open rather than sitting after Save/Save As.
- View menu moved out of the button group entirely and pinned to the
  far right edge of the toolbar (same `margin-left: auto` pattern
  already used for the current-filename label), rather than sitting
  immediately after Build.

## [0.4.1]

### Fixed
- `pyproject.toml`'s `version` and `ezpy2stl.spec`'s
  `CFBundleShortVersionString` were never bumped alongside the
  v0.3.1/v0.4.0 releases (both still said 0.3.0) -- purely cosmetic,
  didn't affect functionality, but worth keeping accurate since
  they're the source the built .app's own version metadata comes
  from.

## [0.4.0]

### Added
- View menu (toolbar) with checkboxes to show/hide each panel:
  Parameters, Script editor, Console/output, Generated files, 3D
  viewer. Hidden panels vanish completely (not collapsed to a header
  bar); closing a panel also hides the divider that resizes it, since
  a divider with nothing to resize is a dead control. Closing the 3D
  viewer stretches the script/console column to full width instead of
  leaving a blank gap.
- State is in-memory/per-session only -- everything reopens on
  relaunch. Not persisted to disk (would need a small `desktop.py`
  API addition, similar to recent-files, if that's wanted later).

## [0.3.1]

### Changed
- Generated files list is now grouped by type: STLs first, STEP/3MF
  companions below. STEP/3MF are hidden by default behind a "Show
  STEP / 3MF" toggle in the panel header (view-only -- doesn't affect
  what actually gets exported).
- Generated files panel now has a fixed, draggable height (same
  divider pattern as Parameters/console) with its own scrollbar,
  instead of growing unbounded and pushing files off-screen with no
  way to reach them.

### Fixed
- `selectFile()`'s active-row highlighting looped over direct
  children only; broke once file rows were nested inside per-type
  group containers. Now walks all `.file-row` elements regardless of
  nesting.

## [0.3.0]

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
- Automatic STEP and 3MF export: any `export_stl(part, path)` call in
  a script now also produces sibling `.step` and `.3mf` files from the
  same in-memory part, regardless of whether the script asks for them.
  Wrapped in error handling throughout -- a failure in the bonus
  formats surfaces in the build output but never breaks the STL build
  itself.
- `download_file` native API: Download now goes through a native Save
  dialog instead of an HTML `<a download>` link, which turned out to
  be unreliable inside WKWebView (the desktop app's embedded browser
  engine) even though it worked fine in a plain browser tab.
- `tests/test_executor.py` (pytest) and `frontend/params.test.mjs`
  (Node's built-in test runner) covering the workspace-isolation
  logic, the auto STEP/3MF export mechanism, and parameter-detection
  logic.
- `frontend/params.js`: parameter-parsing logic extracted out of
  `app.js` so it's testable without a browser.

### Fixed
- A race condition where `hasNativeApi` could stay `false` even when
  running the real desktop app, if pywebview's ready event fired
  before the page finished registering the listener for it (made more
  likely once CodeMirror's CDN scripts started delaying page load).
  Save/Save As/Download would incorrectly claim they needed the
  desktop app.
- The initial auto-export implementation assumed a plain
  `build123d.export_3mf(part, path)` function; the real API is a
  separate `Mesher` class (`Mesher().add_shape(part).write(path)`).
- A `subprocess.TimeoutExpired.stdout`/`.stderr` type inconsistency
  (can come back as `None`, `str`, or raw `bytes` depending on timing)
  that could crash the timeout-handling path itself.

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
