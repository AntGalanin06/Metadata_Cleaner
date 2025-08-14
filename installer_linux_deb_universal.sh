#!/bin/bash
# Debian package builder for Metadata Cleaner with auto-architecture detection

set -e

APP_NAME="metadata-cleaner"
APP_VERSION="1.0.1"

# Auto-detect architecture
SYSTEM_ARCH=$(uname -m)
case "$SYSTEM_ARCH" in
    "x86_64")
        ARCH="amd64"
        ;;
    "aarch64"|"arm64")
        ARCH="arm64"
        ;;
    *)
        echo "❌ Unsupported architecture: $SYSTEM_ARCH"
        echo "Supported: x86_64 (amd64), aarch64/arm64"
        exit 1
        ;;
esac

PACKAGE_NAME="MetadataCleaner-Linux-${ARCH}.deb"
echo "🔍 Detected architecture: $SYSTEM_ARCH → Debian: $ARCH"

# Create package structure
echo "📦 Building Debian package..."
mkdir -p "dist/${PACKAGE_NAME}/DEBIAN"
mkdir -p "dist/${PACKAGE_NAME}/opt/metadata-cleaner"
mkdir -p "dist/${PACKAGE_NAME}/usr/share/applications"
mkdir -p "dist/${PACKAGE_NAME}/usr/share/pixmaps"
mkdir -p "dist/${PACKAGE_NAME}/usr/local/bin"

# Control file
cat > "dist/${PACKAGE_NAME}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libgtk-3-0, libglib2.0-0, libcairo2, libpango-1.0-0
Maintainer: AntGalanin06 <contact@example.com>
Description: Remove metadata from files
 Metadata Cleaner is a privacy tool that removes metadata from various file types
 including images (JPG, PNG, GIF, HEIC), documents (DOCX, PPTX, XLSX),
 PDF files, and videos (MP4, MOV).
 .
 All processing is done locally on your device for maximum privacy.
Homepage: https://github.com/AntGalanin06/Metadata_Cleaner
EOF

# Install script
cat > "dist/${PACKAGE_NAME}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Update MIME database
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime
fi

echo "Metadata Cleaner installed successfully!"
echo "Launch from applications menu or run: metadata-cleaner"
EOF

# Uninstall script
cat > "dist/${PACKAGE_NAME}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Update desktop database after removal
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi
EOF

# Make scripts executable
chmod 755 "dist/${PACKAGE_NAME}/DEBIAN/postinst"
chmod 755 "dist/${PACKAGE_NAME}/DEBIAN/prerm"

# Copy application files
if [[ -d "dist/MetadataCleaner" ]]; then
    cp -r "dist/MetadataCleaner"/* "dist/${PACKAGE_NAME}/opt/metadata-cleaner/"
    chmod +x "dist/${PACKAGE_NAME}/opt/metadata-cleaner/MetadataCleaner"
else
    echo "❌ Built application not found in dist/MetadataCleaner"
    echo "Run 'python build.py' first"
    exit 1
fi

# Copy icon
if [[ -f "assets/icons/icon.png" ]]; then
    cp "assets/icons/icon.png" "dist/${PACKAGE_NAME}/usr/share/pixmaps/metadata-cleaner.png"
fi

# Desktop file
cat > "dist/${PACKAGE_NAME}/usr/share/applications/metadata-cleaner.desktop" << EOF
[Desktop Entry]
Name=Metadata Cleaner
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Exec=/opt/metadata-cleaner/MetadataCleaner
Icon=metadata-cleaner
Terminal=false
Type=Application
Categories=Utility;Privacy;
StartupWMClass=MetadataCleaner
StartupNotify=true
MimeType=image/jpeg;image/png;image/gif;application/pdf;application/vnd.openxmlformats-officedocument.wordprocessingml.document;
Keywords=metadata;exif;privacy;cleaner;
EOF

# Create symbolic link script
cat > "dist/${PACKAGE_NAME}/usr/local/bin/metadata-cleaner" << EOF
#!/bin/bash
exec /opt/metadata-cleaner/MetadataCleaner "\$@"
EOF
chmod +x "dist/${PACKAGE_NAME}/usr/local/bin/metadata-cleaner"

# Build package
dpkg-deb --build "dist/${PACKAGE_NAME}"

echo "✅ Debian package created: dist/${PACKAGE_NAME}"
echo "📦 Install with: sudo dpkg -i dist/${PACKAGE_NAME}"
echo "🔧 Fix dependencies: sudo apt-get install -f"
