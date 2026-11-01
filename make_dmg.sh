#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# The version comes from pyproject.toml -- the same number the release
# workflow checks against the git tag -- so the file is EZPy2STL-0.7.2.dmg.
VERSION=$(sed -nE 's/^version *= *"([^"]+)".*/\1/p' pyproject.toml | head -1)
if [ -z "$VERSION" ]; then
    echo "Could not read the version from pyproject.toml."
    exit 1
fi

APP="dist/EZPy2STL.app"
DMG="dist/EZPy2STL-${VERSION}.dmg"

if [ ! -d "$APP" ]; then
    echo "No built app found at '$APP'. Run ./build_app.sh first."
    exit 1
fi

rm -f "$DMG"

TMPDIR=$(mktemp -d)
cp -R "$APP" "$TMPDIR/"
ln -s /Applications "$TMPDIR/Applications"

hdiutil create -volname "EZPy2STL" -srcfolder "$TMPDIR" -ov -format UDZO "$DMG"

rm -rf "$TMPDIR"

echo "Created: $DMG"
echo "Opening this mounts a window with the app + an Applications shortcut to drag it into."
