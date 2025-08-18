#!/bin/bash
# Modern RPM package builder for Metadata Cleaner
# Version: 2.0.0

set -euo pipefail

# Configuration
readonly APP_NAME="metadata-cleaner"
readonly APP_DISPLAY_NAME="Metadata Cleaner"
readonly APP_VERSION="1.0.1"
readonly RELEASE="1"
readonly MAINTAINER="AntGalanin06 <contact@example.com>"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly DIST_DIR="${PROJECT_ROOT}/dist"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Auto-detect architecture
detect_architecture() {
    local system_arch
    system_arch=$(uname -m)
    
    case "$system_arch" in
        "x86_64"|"amd64")
            echo "x86_64"
            ;;
        "aarch64"|"arm64")
            echo "aarch64"
            ;;
        "i386"|"i686")
            echo "i686"
            ;;
        *)
            log_error "Unsupported architecture: $system_arch"
            log_error "Supported: x86_64, aarch64/arm64, i386"
            exit 1
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v rpmbuild >/dev/null 2>&1; then
        missing_deps+=("rpm-build")
    fi
    
    if ! command -v tar >/dev/null 2>&1; then
        missing_deps+=("tar")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Install with:"
        log_error "  RHEL/CentOS/Fedora: sudo dnf install ${missing_deps[*]}"
        log_error "  openSUSE: sudo zypper install ${missing_deps[*]}"
        exit 1
    fi
}

# Create RPM build structure
create_rpm_structure() {
    local arch="$1"
    local rpmbuild_dir="${PROJECT_ROOT}/rpmbuild"
    
    log_info "Creating RPM build structure..."
    
    # Remove existing rpmbuild directory
    [[ -d "$rpmbuild_dir" ]] && rm -rf "$rpmbuild_dir"
    
    # Create RPM directory structure
    mkdir -p "$rpmbuild_dir"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    
    echo "$rpmbuild_dir"
}

# Create source archive
create_source_archive() {
    local rpmbuild_dir="$1"
    
    log_info "Creating source archive..."
    
    # Check if built application exists
    local app_source="${DIST_DIR}/MetadataCleaner"
    if [[ ! -d "$app_source" ]] && [[ ! -f "$app_source" ]]; then
        log_error "Built application not found: $app_source"
        log_error "Available files in dist/:"
        ls -la "${DIST_DIR}/" || echo "dist directory not found"
        log_error "Run 'python build.py' first"
        exit 1
    fi
    
    # Create temporary directory for archive
    local temp_dir
    temp_dir=$(mktemp -d)
    local archive_dir="${temp_dir}/${APP_NAME}-${APP_VERSION}"
    
    mkdir -p "$archive_dir"
    
    # Copy application files - handle both directory and single file
    if [[ -d "$app_source" ]]; then
        # Directory structure from PyInstaller
        cp -r "$app_source"/* "$archive_dir/"
    elif [[ -f "$app_source" ]]; then
        # Single file
        cp "$app_source" "$archive_dir/"
    fi
    
    # Copy assets
    if [[ -d "${PROJECT_ROOT}/assets" ]]; then
        cp -r "${PROJECT_ROOT}/assets" "$archive_dir/"
    fi
    
    # Copy documentation
    for doc in LICENSE README.md; do
        if [[ -f "${PROJECT_ROOT}/$doc" ]]; then
            cp "${PROJECT_ROOT}/$doc" "$archive_dir/"
        fi
    done
    
    # Create archive
    local archive_file="${rpmbuild_dir}/SOURCES/${APP_NAME}-${APP_VERSION}.tar.gz"
    tar -C "$temp_dir" -czf "$archive_file" "${APP_NAME}-${APP_VERSION}"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Source archive created: $archive_file"
    echo "$archive_file"
}

# Create RPM spec file
create_spec_file() {
    local rpmbuild_dir="$1"
    local arch="$2"
    
    log_info "Creating RPM spec file..."
    
    local spec_file="${rpmbuild_dir}/SPECS/${APP_NAME}.spec"
    
    cat > "$spec_file" << EOF
%global _missing_build_ids_terminate_build 0
%global _build_id_links none

Name:           ${APP_NAME}
Version:        ${APP_VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        Privacy tool for removing metadata from files
License:        MIT
URL:            https://github.com/AntGalanin06/Metadata_Cleaner
Source0:        %{name}-%{version}.tar.gz
BuildArch:      ${arch}

# Runtime dependencies
Requires:       gtk3
Requires:       glib2
Requires:       cairo
Requires:       pango
Requires:       gdk-pixbuf2
Recommends:     ffmpeg

# Build dependencies
BuildRequires:  systemd-rpm-macros

%description
Metadata Cleaner is a modern desktop application that removes metadata from
various file types including images (JPG, PNG, GIF, HEIC), documents (DOCX,
PPTX, XLSX), PDF files, and videos (MP4, MOV).

Key features:
- 100%% local processing - no data transmission
- Automatic backup creation for safety
- Selective metadata cleaning
- Modern Material Design interface
- Support for multiple file formats

All file processing happens locally on your device for maximum privacy and
security. The application creates automatic backups of original files before
cleaning to ensure data safety.

%prep
%autosetup -n %{name}-%{version}

%build
# Nothing to build - pre-compiled application

%install
# Create directory structure
mkdir -p %{buildroot}/opt/metadata-cleaner
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/pixmaps
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_docdir}/%{name}

# Install application files - handle PyInstaller structure
if [ -f "MetadataCleaner" ]; then
    # Single executable file
    cp "MetadataCleaner" %{buildroot}/opt/metadata-cleaner/
    chmod +x %{buildroot}/opt/metadata-cleaner/MetadataCleaner
elif [ -d "MetadataCleaner" ]; then
    # Directory structure from PyInstaller
    cp -r MetadataCleaner/* %{buildroot}/opt/metadata-cleaner/
    # Find and make executable
    find %{buildroot}/opt/metadata-cleaner -name "MetadataCleaner" -type f -exec chmod +x {} \;
else
    # Fallback - copy everything
    cp -r * %{buildroot}/opt/metadata-cleaner/
    find %{buildroot}/opt/metadata-cleaner -name "MetadataCleaner" -type f -exec chmod +x {} \;
fi

# Install icon
if [ -f assets/icons/icon.png ]; then
    cp assets/icons/icon.png %{buildroot}%{_datadir}/pixmaps/metadata-cleaner.png
fi

# Install documentation
for doc in LICENSE README.md; do
    if [ -f "\$doc" ]; then
        cp "\$doc" %{buildroot}%{_docdir}/%{name}/
    fi
done

# Create desktop file
cat > %{buildroot}%{_datadir}/applications/metadata-cleaner.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=Metadata Cleaner
GenericName=Privacy Tool
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Icon=metadata-cleaner
Exec=/opt/metadata-cleaner/MetadataCleaner %%F
Path=/opt/metadata-cleaner
Categories=Utility;Privacy;Security;
Keywords=metadata;exif;privacy;cleaner;security;
MimeType=image/jpeg;image/png;image/gif;image/heic;image/heif;application/pdf;application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/vnd.openxmlformats-officedocument.presentationml.presentation;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;video/mp4;video/quicktime;
Terminal=false
StartupNotify=true
StartupWMClass=MetadataCleaner
NoDisplay=false
DESKTOP_EOF

# Create launcher script
cat > %{buildroot}%{_bindir}/metadata-cleaner << 'LAUNCHER_EOF'
#!/bin/bash
# Metadata Cleaner launcher script

# Set up environment
export PATH="/opt/metadata-cleaner:\$PATH"

# Find the MetadataCleaner executable
EXEC_PATH=""
if [ -x "/opt/metadata-cleaner/MetadataCleaner" ]; then
    EXEC_PATH="/opt/metadata-cleaner/MetadataCleaner"
else
    # Search for the executable
    EXEC_PATH=\$(find /opt/metadata-cleaner -name "MetadataCleaner" -type f -executable 2>/dev/null | head -1)
fi

if [ -n "\$EXEC_PATH" ] && [ -x "\$EXEC_PATH" ]; then
    # Change to the directory containing the executable for proper library loading
    cd "\$(dirname "\$EXEC_PATH")" && exec "./\$(basename "\$EXEC_PATH")" "\$@"
else
    echo "Error: Could not find executable MetadataCleaner"
    echo "Available files in /opt/metadata-cleaner/:"
    ls -la /opt/metadata-cleaner/
    exit 1
fi
LAUNCHER_EOF

chmod +x %{buildroot}%{_bindir}/metadata-cleaner

%files
/opt/metadata-cleaner/
%{_datadir}/applications/metadata-cleaner.desktop
%{_datadir}/pixmaps/metadata-cleaner.png
%{_bindir}/metadata-cleaner
%doc %{_docdir}/%{name}/

%post
# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database %{_datadir}/applications 2>/dev/null || true
fi

# Update MIME database
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database %{_datadir}/mime 2>/dev/null || true
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t %{_datadir}/pixmaps 2>/dev/null || true
fi

echo "Metadata Cleaner installed successfully!"
echo "Launch from applications menu or run: metadata-cleaner"

%postun
if [ \$1 -eq 0 ]; then
    # Complete removal
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database %{_datadir}/applications 2>/dev/null || true
    fi
    
    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database %{_datadir}/mime 2>/dev/null || true
    fi
    
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t %{_datadir}/pixmaps 2>/dev/null || true
    fi
fi

%changelog
* $(date +"%a %b %d %Y") ${MAINTAINER} - ${APP_VERSION}-${RELEASE}
- Initial RPM release
- Privacy-focused metadata removal tool
- Support for images, documents, PDFs, and videos
- Modern Material Design interface
- Local processing for maximum security
EOF
    
    log_success "RPM spec file created: $spec_file"
    echo "$spec_file"
}

# Build RPM package
build_rpm() {
    local rpmbuild_dir="$1"
    local arch="$2"
    
    log_info "Building RPM package..."
    
    # Build package
    if ! rpmbuild --define "_topdir $rpmbuild_dir" -ba "${rpmbuild_dir}/SPECS/${APP_NAME}.spec"; then
        log_error "RPM build failed"
        exit 1
    fi
    
    # Find the generated RPM
    local rpm_file
    rpm_file=$(find "${rpmbuild_dir}/RPMS" -name "*.rpm" -type f | head -1)
    
    if [[ -n "$rpm_file" && -f "$rpm_file" ]]; then
        local final_name="${DIST_DIR}/MetadataCleaner-Linux-${arch}.rpm"
        mv "$rpm_file" "$final_name"
        
        # Get package info
        local size
        size=$(du -h "$final_name" | cut -f1)
        
        log_success "RPM package created: $final_name ($size)"
        log_info "Installation:"
        log_info "  RHEL/CentOS/Fedora: sudo dnf install $final_name"
        log_info "  openSUSE: sudo zypper install $final_name"
        log_info "  Generic: sudo rpm -ivh $final_name"
        log_info "Removal:"
        log_info "  sudo rpm -e metadata-cleaner"
        
        # Verify package
        log_info "Package verification:"
        rpm -qip "$final_name" | head -15
        
        return 0
    else
        log_error "RPM file not found after build"
        return 1
    fi
}

# Build RPM using alien (DEB -> RPM conversion)
build_rpm_with_alien() {
    local arch="$1"
    
    log_info "Building RPM package using alien (DEB conversion)..."
    
    # Check if alien is available
    if ! command -v alien >/dev/null 2>&1; then
        log_error "alien not found, trying to install..."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update && sudo apt-get install -y alien fakeroot
        else
            log_error "Cannot install alien - unsupported package manager"
            return 1
        fi
    fi
    
    # Look for existing DEB file
    local deb_arch
    case "$arch" in
        "x86_64") deb_arch="amd64" ;;
        "aarch64") deb_arch="arm64" ;;
        "i686") deb_arch="i386" ;;
        *) deb_arch="$arch" ;;
    esac
    
    local deb_file="${DIST_DIR}/MetadataCleaner-Linux-${deb_arch}.deb"
    if [[ ! -f "$deb_file" ]]; then
        log_error "DEB file not found for alien conversion: $deb_file"
        log_error "Need to build DEB package first"
        return 1
    fi
    
    log_info "Converting DEB to RPM: $deb_file"
    
    # Convert DEB to RPM
    cd "$DIST_DIR"
    if alien --to-rpm --scripts "$deb_file"; then
        # Find the generated RPM file
        local alien_rpm
        alien_rpm=$(find . -name "metadata-cleaner-*.rpm" -type f | head -1)
        
        if [[ -n "$alien_rpm" && -f "$alien_rpm" ]]; then
            # Rename to match our convention
            local final_name="MetadataCleaner-Linux-${arch}.rpm"
            mv "$alien_rpm" "$final_name"
            
            # Get package info
            local size
            size=$(du -h "$final_name" | cut -f1)
            
            log_success "RPM package created via alien: $final_name ($size)"
            log_info "Installation:"
            log_info "  RHEL/CentOS/Fedora: sudo dnf install $final_name"
            log_info "  openSUSE: sudo zypper install $final_name"
            log_info "  Generic: sudo rpm -ivh $final_name"
            log_info "Note: Package converted from DEB using alien"
            
            return 0
        else
            log_error "Alien conversion failed - no RPM file generated"
            return 1
        fi
    else
        log_error "Alien conversion failed"
        return 1
    fi
}

# Main function
main() {
    log_info "Starting RPM package build for Metadata Cleaner v${APP_VERSION}"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check dependencies
    check_dependencies
    
    # Detect architecture
    local arch
    arch=$(detect_architecture)
    log_info "Detected architecture: $(uname -m) → RPM: $arch"
    
    # Create RPM build structure
    local rpmbuild_dir
    rpmbuild_dir=$(create_rpm_structure "$arch")
    
    # Create source archive
    create_source_archive "$rpmbuild_dir"
    
    # Create spec file
    create_spec_file "$rpmbuild_dir" "$arch"
    
    # Build package
    if build_rpm "$rpmbuild_dir" "$arch"; then
        log_success "RPM package build completed successfully"
    else
        log_warning "Native RPM build failed, trying alien fallback..."
        if build_rpm_with_alien "$arch"; then
            log_success "RPM package created via alien fallback"
        else
            log_error "Both native RPM and alien fallback failed"
            exit 1
        fi
    fi
    
    # Cleanup
    [[ -d "$rpmbuild_dir" ]] && rm -rf "$rpmbuild_dir"
    
    log_success "Build process finished"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi