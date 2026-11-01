# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for a self-contained macOS .app bundle, including
# build123d/OCP (OpenCascade bindings) rather than shelling out to a
# real Python interpreter for user scripts.
#
# This is the highest-risk part of the whole packaging effort: OCP is a
# large native extension and there's no widely-documented PyInstaller
# recipe for it (the build123d community's own portable distribution
# ships a full embedded Python interpreter rather than freezing OCP
# into one executable). collect_all() below is a best-effort attempt to
# grab everything OCP/build123d/pywebview need. If the built app fails
# to launch or a build fails with a "No module named ..." /
# "Library not loaded" error, that error message is exactly what's
# needed to fix this spec -- please paste it back rather than guessing
# at a fix.
#
# Build with:  uv run pyinstaller ezpy2stl.spec --noconfirm --clean

from PyInstaller.utils.hooks import collect_all

# LICENSE and THIRD_PARTY_NOTICES.md ship inside the .app so redistributed
# binaries carry their licence texts (regenerate the notices with
# tools/generate_notices.py whenever dependencies change).
datas = [('frontend', 'frontend'), ('LICENSE', '.'), ('THIRD_PARTY_NOTICES.md', '.')]
binaries = []
hiddenimports = [
    # uvicorn resolves these by string name at runtime (not a static
    # import PyInstaller's analysis can see), so they're listed by hand.
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'uvicorn.logging',
]

# Best-effort full collection for the packages most likely to have
# hidden imports, native binaries, or bundled data files that static
# analysis would otherwise miss.
for pkg in ('build123d', 'OCP', 'webview', 'lib3mf', 'PIL', 'potrace'):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EZPy2STL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Set to True temporarily if you need a Terminal window showing
    # print()/traceback output while debugging a launch failure.
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='EZPy2STL',
)

app = BUNDLE(
    coll,
    name='EZPy2STL.app',
    icon='resources/AppIcon.icns',
    bundle_identifier='com.elinussbaum.ezpy2stl',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '0.6.1',
    },
)
