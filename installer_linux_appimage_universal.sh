#!/bin/bash
# AppImage builder for Metadata Cleaner with auto-architecture detection

set -e

APP_NAME="MetadataCleaner"
APP_VERSION="1.0.1"

# Auto-detect architecture
SYSTEM_ARCH=$(uname -m)
case "$SYSTEM_ARCH" in
    "x86_64")
        ARCH="x64"
        APPIMAGE_TOOL_ARCH="x86_64"
        ;;
    "aarch64"|"arm64")
        ARCH="arm64"
        APPIMAGE_TOOL_ARCH="aarch64"
        ;;
    *)
        echo "❌ Unsupported architecture: $SYSTEM_ARCH"
        echo "Supported: x86_64, aarch64/arm64"
        exit 1
        ;;
esac

echo "📦 Building AppImage for Linux..."
echo "🔍 Detected architecture: $SYSTEM_ARCH → AppImage: $ARCH"

# Check if built application exists
if [[ ! -d "dist/MetadataCleaner" ]]; then
    echo "❌ Built application not found in dist/MetadataCleaner"
    echo "Run 'python build.py' first"
    exit 1
fi

# Download appimagetool if needed
APPIMAGETOOL="appimagetool-${APPIMAGE_TOOL_ARCH}.AppImage"
if [[ ! -f "$APPIMAGETOOL" ]]; then
    echo "📥 Downloading AppImageTool for ${APPIMAGE_TOOL_ARCH}..."
    wget -O "$APPIMAGETOOL" "https://github.com/AppImage/AppImageKit/releases/download/continuous/${APPIMAGETOOL}"
    chmod +x "$APPIMAGETOOL"
fi

# Create AppDir structure
APPDIR="dist/${APP_NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy application
cp -r "dist/MetadataCleaner"/* "$APPDIR/usr/bin/"
chmod +x "$APPDIR/usr/bin/MetadataCleaner"

# Copy icon
if [[ -f "assets/icons/icon.png" ]]; then
    cp "assets/icons/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/metadata-cleaner.png"
    cp "assets/icons/icon.png" "$APPDIR/metadata-cleaner.png" # Also as top-level icon
else
    echo "⚠️  Warning: Icon file not found at assets/icons/icon.png"
fi

# Create AppRun
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
EXEC="${HERE}/usr/bin/MetadataCleaner"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${EXEC}" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Create desktop file
cat > "$APPDIR/metadata-cleaner.desktop" << EOF
[Desktop Entry]
Name=Metadata Cleaner
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Exec=MetadataCleaner
Icon=metadata-cleaner
Type=Application
Categories=Utility;Privacy;
Terminal=false
StartupWMClass=MetadataCleaner
StartupNotify=true
MimeType=image/jpeg;image/png;image/gif;application/pdf;application/vnd.openxmlformats-officedocument.wordprocessingml.document;
Keywords=metadata;exif;privacy;cleaner;
X-AppImage-Version=${APP_VERSION}
EOF

# Copy desktop file to usr/share/applications
cp "$APPDIR/metadata-cleaner.desktop" "$APPDIR/usr/share/applications/"

# Create AppImage
echo "🔨 Building AppImage..."
APPIMAGE_OUTPUT="dist/MetadataCleaner-Linux-${ARCH}.AppImage"

# Try with APPIMAGE_EXTRACT_AND_RUN first
if APPIMAGE_EXTRACT_AND_RUN=1 ./"$APPIMAGETOOL" --no-appstream "$APPDIR" "$APPIMAGE_OUTPUT" 2>/dev/null; then
    echo "✅ AppImage created successfully with FUSE"
elif ./"$APPIMAGETOOL" --appimage-extract-and-run --no-appstream "$APPDIR" "$APPIMAGE_OUTPUT" 2>/dev/null; then
    echo "✅ AppImage created successfully without FUSE"
else
    echo "⚠️  AppImageTool failed, creating portable archive instead..."
    cd dist
    tar czf "${APP_NAME}-Linux-Portable.tar.gz" MetadataCleaner/
    cd ..
    echo "✅ Portable archive created: dist/${APP_NAME}-Linux-Portable.tar.gz"
    echo "📖 Usage: Extract archive and run ./MetadataCleaner"
    exit 0
fi

# Make AppImage executable
chmod +x "$APPIMAGE_OUTPUT"

echo "✅ AppImage created: $APPIMAGE_OUTPUT"
echo "📦 Distribute this single file to Linux users"
echo "🚀 Run with: ./${APP_NAME}-Linux-${ARCH}.AppImage"

# Cleanup
rm -rf "$APPDIR"
