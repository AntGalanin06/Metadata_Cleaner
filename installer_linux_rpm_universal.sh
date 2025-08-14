#!/bin/bash
# RPM package builder for Metadata Cleaner with auto-architecture detection

set -e

APP_NAME="metadata-cleaner"
APP_VERSION="1.0.1"
RELEASE="1"

# Auto-detect architecture
SYSTEM_ARCH=$(uname -m)
case "$SYSTEM_ARCH" in
    "x86_64")
        ARCH="x86_64"
        RPM_ARCH="x86_64"
        ;;
    "aarch64"|"arm64")
        ARCH="aarch64"
        RPM_ARCH="aarch64"
        ;;
    *)
        echo "❌ Unsupported architecture: $SYSTEM_ARCH"
        echo "Supported: x86_64, aarch64/arm64"
        exit 1
        ;;
esac

echo "🔍 Detected architecture: $SYSTEM_ARCH → RPM: $RPM_ARCH"

# Create RPM build structure
echo "📦 Building RPM package..."
mkdir -p "rpmbuild"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create spec file
cat > "rpmbuild/SPECS/${APP_NAME}.spec" << EOF
Name:           ${APP_NAME}
Version:        ${APP_VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        Remove metadata from files
License:        MIT
URL:            https://github.com/AntGalanin06/Metadata_Cleaner
Source0:        %{name}-%{version}.tar.gz
BuildArch:      ${RPM_ARCH}

Requires:       gtk3, glib2, cairo, pango

%description
Metadata Cleaner is a privacy tool that removes metadata from various file types
including images (JPG, PNG, GIF, HEIC), documents (DOCX, PPTX, XLSX),
PDF files, and videos (MP4, MOV).

All processing is done locally on your device for maximum privacy.

%prep
%setup -q

%build
# Nothing to build - pre-compiled application

%install
mkdir -p %{buildroot}/opt/metadata-cleaner
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/pixmaps
mkdir -p %{buildroot}/usr/local/bin

# Copy application files
cp -r * %{buildroot}/opt/metadata-cleaner/
chmod +x %{buildroot}/opt/metadata-cleaner/MetadataCleaner

# Desktop file
cat > %{buildroot}/usr/share/applications/metadata-cleaner.desktop << 'DESKTOP_EOF'
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
DESKTOP_EOF

# Copy icon if available
if [ -f assets/icons/icon.png ]; then
    cp assets/icons/icon.png %{buildroot}/usr/share/pixmaps/metadata-cleaner.png
fi

# Create symbolic link
cat > %{buildroot}/usr/local/bin/metadata-cleaner << 'LINK_EOF'
#!/bin/bash
exec /opt/metadata-cleaner/MetadataCleaner "\$@"
LINK_EOF
chmod +x %{buildroot}/usr/local/bin/metadata-cleaner

%files
/opt/metadata-cleaner/
/usr/share/applications/metadata-cleaner.desktop
/usr/share/pixmaps/metadata-cleaner.png
/usr/local/bin/metadata-cleaner

%post
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

%postun
# Update desktop database after removal
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

%changelog
* $(date +"%a %b %d %Y") AntGalanin06 <contact@example.com> - ${APP_VERSION}-${RELEASE}
- Initial RPM release
- Privacy-focused metadata removal tool
- Support for images, documents, PDFs, and videos
EOF

# Create source archive
if [[ -d "dist/MetadataCleaner" ]]; then
    echo "📦 Creating source archive..."
    cd dist
    # Создаем архив с правильной структурой папок для RPM
    tar czf "../rpmbuild/SOURCES/${APP_NAME}-${APP_VERSION}.tar.gz" --transform "s/MetadataCleaner/${APP_NAME}-${APP_VERSION}/" MetadataCleaner/
    cd ..
    echo "✅ Archive created: rpmbuild/SOURCES/${APP_NAME}-${APP_VERSION}.tar.gz"
    ls -la "rpmbuild/SOURCES/"
    # Проверяем содержимое архива
    echo "🔍 Checking archive contents:"
    tar tzf "rpmbuild/SOURCES/${APP_NAME}-${APP_VERSION}.tar.gz" | head -10
else
    echo "❌ Built application not found in dist/MetadataCleaner"
    echo "Run 'python build.py' first"
    exit 1
fi

# Build RPM
rpmbuild --define "_topdir $(pwd)/rpmbuild" -ba "rpmbuild/SPECS/${APP_NAME}.spec"

# Move result
if [[ -f "rpmbuild/RPMS/${RPM_ARCH}/${APP_NAME}-${APP_VERSION}-${RELEASE}.${RPM_ARCH}.rpm" ]]; then
    mv "rpmbuild/RPMS/${RPM_ARCH}/${APP_NAME}-${APP_VERSION}-${RELEASE}.${RPM_ARCH}.rpm" "dist/MetadataCleaner-Linux-${ARCH}.rpm"
    echo "✅ RPM package created: dist/MetadataCleaner-Linux-${ARCH}.rpm"
    echo "📦 Install with: sudo rpm -ivh dist/MetadataCleaner-Linux-${ARCH}.rpm"
    echo "🔧 Or with DNF: sudo dnf install dist/MetadataCleaner-Linux-${ARCH}.rpm"
else
    echo "❌ RPM build failed"
    exit 1
fi

# Cleanup
rm -rf rpmbuild
