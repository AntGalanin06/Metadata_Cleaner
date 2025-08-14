#!/bin/bash
# macOS DMG creator for Metadata Cleaner

set -e

APP_NAME="Metadata Cleaner"
APP_VERSION="1.0.1"
DMG_NAME="MetadataCleaner-macOS"

echo "📦 Creating macOS DMG package..."

# Check dependencies
if ! command -v create-dmg >/dev/null 2>&1; then
    echo "Installing create-dmg..."
    if command -v brew >/dev/null 2>&1; then
        brew install create-dmg
    else
        echo "❌ Homebrew not found. Please install create-dmg manually:"
        echo "   brew install create-dmg"
        exit 1
    fi
fi

# Check if app exists
if [[ ! -d "dist/MetadataCleaner.app" ]]; then
    echo "❌ MetadataCleaner.app not found in dist/"
    echo "Run 'python build.py' first"
    exit 1
fi

# Create temporary DMG staging directory
DMG_STAGING="dist/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

# Copy app to staging
cp -R "dist/MetadataCleaner.app" "$DMG_STAGING/"

# Copy license file (English-only version)
if [[ -f "docs/LICENSE_INSTALLER.txt" ]]; then
    cp "docs/LICENSE_INSTALLER.txt" "$DMG_STAGING/License.txt"
fi

# Create README for DMG
cat > "$DMG_STAGING/README.txt" << EOF
Metadata Cleaner for macOS
==========================

Installation:
1. Drag MetadataCleaner.app to your Applications folder
2. Double-click to launch
3. Grant necessary permissions when prompted

Requirements:
- macOS 10.15 (Catalina) or later
- Intel or Apple Silicon Mac

Support:
- GitHub: https://github.com/AntGalanin06/Metadata_Cleaner
- Issues: https://github.com/AntGalanin06/Metadata_Cleaner/issues

Privacy Notice:
All file processing happens locally on your Mac.
No data is transmitted over the internet.

Version: ${APP_VERSION}
License: MIT
EOF

# Create DMG
echo "🔨 Creating DMG..."
create-dmg \
    --volname "$APP_NAME" \
    --volicon "assets/icons/icon.icns" \
    --window-pos 200 120 \
    --window-size 800 600 \
    --icon-size 80 \
    --icon "MetadataCleaner.app" 200 150 \
    --icon "README.txt" 200 300 \
    --icon "License.txt" 200 450 \
    --hide-extension "MetadataCleaner.app" \
    --app-drop-link 600 150 \
    --background "assets/screenshots/main-light-theme.png" \
    --text-size 14 \
    "dist/${DMG_NAME}.dmg" \
    "$DMG_STAGING"

# Cleanup
rm -rf "$DMG_STAGING"

echo "✅ macOS DMG created: dist/${DMG_NAME}.dmg"
echo "📦 Distribute this file to macOS users"
echo "🔐 Consider code signing for distribution outside App Store"
