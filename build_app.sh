#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Cleaning extended attributes (avoids an ad-hoc codesign warning about"
echo "resource forks / Finder metadata left over from zip/unzip)..."
find . -name ".DS_Store" -delete
xattr -cr . 2>/dev/null || true

echo "Installing build-time dependencies (PyInstaller)..."
uv sync --extra build

echo ""
echo "Building EZPy2STL.app..."
uv run pyinstaller ezpy2stl.spec --noconfirm --clean

echo ""
echo "Smoke-testing the bundle (the imports user scripts rely on)..."
CHECK="$(mktemp -t ezpy2stl_check).py"
cat > "$CHECK" <<'PY'
import build123d, lib3mf, numpy
from PIL import Image
import potrace
print("bundle imports OK")
PY
if ! dist/EZPy2STL.app/Contents/MacOS/EZPy2STL --run-user-script "$CHECK"; then
    rm -f "$CHECK"
    echo "ERROR: the built app cannot import a required package (see above)." >&2
    echo "Do not use this build. Check the collect_all(...) list in ezpy2stl.spec." >&2
    exit 1
fi
rm -f "$CHECK"

echo ""
echo "Done: dist/EZPy2STL.app"
echo ""
echo "First launch will be blocked by Gatekeeper since this isn't code-signed."
echo "One-time fix, either:"
echo "  - Right-click the app in Finder -> Open -> Open, or"
echo "  - Run: xattr -cr 'dist/EZPy2STL.app'"
