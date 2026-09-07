#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP="dist/EZPy2STL.app"
DMG="dist/EZPy2STL.dmg"

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
