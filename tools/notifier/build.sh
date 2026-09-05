#!/bin/bash
# Build "Paititi Watch.app" — the thing that posts the watcher's notifications
# so they carry the Paititi mark instead of Script Editor's scroll.
#
#   bash tools/notifier/build.sh
#
# Idempotent: rebuilds over any previous copy. Run it again if the icon or the
# AppleScript changes. Nothing else in the repo depends on the app existing —
# watch_retreats.py falls back to plain osascript when it is absent, so a
# checkout on another machine still alerts, just with the generic icon.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$HOME/Applications/Paititi Watch.app"
ICON_SRC="$REPO/assets/brand/favicon.png"   # the dorje mark, 185x185
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$HOME/Applications"
rm -rf "$APP"
/usr/bin/osacompile -o "$APP" "$REPO/tools/notifier/notify.applescript"

# The icon. macOS wants an .icns of several sizes; the source is 185px, which
# is far more than a notification banner renders (~40pt), so the upscaled large
# entries only matter if the app is ever shown in Finder.
ICONSET="$WORK/paititi.iconset"
mkdir -p "$ICONSET"
for spec in "16 16x16" "32 16x16@2x" "32 32x32" "64 32x32@2x" \
            "128 128x128" "256 128x128@2x" "256 256x256" "512 256x256@2x" "512 512x512"; do
  set -- $spec
  /usr/bin/sips -z "$1" "$1" "$ICON_SRC" --out "$ICONSET/icon_$2.png" >/dev/null 2>&1
done
/usr/bin/iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/applet.icns"

# osacompile also ships a compiled Assets.car holding Script Editor's scroll
# artwork, and macOS prefers a catalogue over a loose .icns — leave it and the
# banner keeps the scroll no matter what applet.icns says. Deleting it is what
# actually makes the icon change; the applet runs fine without it, as the
# catalogue holds nothing but that icon.
rm -f "$APP/Contents/Resources/Assets.car"

# osacompile writes CFBundleIconFile=applet, which is what we just replaced —
# but give the bundle its own identifier so macOS files its notification
# permission under this app rather than lumping it in with every other applet.
/usr/bin/defaults write "$APP/Contents/Info.plist" CFBundleIdentifier "org.paititi.watch"
/usr/bin/defaults write "$APP/Contents/Info.plist" CFBundleName "Paititi Watch"
/usr/bin/plutil -convert xml1 "$APP/Contents/Info.plist"

# Re-sign, and note that this has to be the LAST thing that touches the bundle.
# osacompile signs what it produced; every edit above — the icon, the deleted
# catalogue, the Info.plist keys — invalidates that signature, and a broken
# signature does not announce itself. The app still launches, `open` still
# returns 0, and the notification is silently dropped. That is the whole
# failure, and `codesign -v` is the only thing that shows it.
/usr/bin/codesign --force --deep --sign - "$APP" 2>/dev/null
/usr/bin/codesign -v "$APP" 2>/dev/null && echo "signature: ok"

# The icon cache is keyed on the bundle's mtime; without this the old icon can
# persist until logout.
/usr/bin/touch "$APP"

echo "built: $APP"
echo
echo "Now run it once while you are watching, so macOS registers it and asks"
echo "for notification permission:"
echo "    python3 tools/watch_retreats.py --test"
