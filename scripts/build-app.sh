#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
swift build -c release
APP="$(pwd)/dist/RigAndBone2D.app"
mkdir -p "$APP/Contents/MacOS"
cp .build/release/RigAndBone2D "$APP/Contents/MacOS/RigAndBone2D"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>RigAndBone2D</string>
<key>CFBundleIdentifier</key><string>local.frostnova.rigandbone2d</string>
<key>CFBundleName</key><string>RigAndBone2D</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.2.0</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
<key>CFBundleDocumentTypes</key><array><dict>
<key>CFBundleTypeName</key><string>RigAndBone2D Project</string>
<key>CFBundleTypeExtensions</key><array><string>rig2d</string></array>
<key>CFBundleTypeRole</key><string>Editor</string>
</dict></array>
</dict></plist>
PLIST
codesign --force --sign - "$APP"
printf 'Built %s\n' "$APP"
