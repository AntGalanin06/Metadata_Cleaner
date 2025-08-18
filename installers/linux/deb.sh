#!/bin/bash
# Modern Debian package builder for Metadata Cleaner
# Version: 2.0.0

set -euo pipefail

# Configuration
readonly APP_NAME="metadata-cleaner"
readonly APP_DISPLAY_NAME="Metadata Cleaner"
readonly APP_VERSION="1.0.1"
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
            echo "amd64"
            ;;
        "aarch64"|"arm64")
            echo "arm64"
            ;;
        "i386"|"i686")
            echo "i386"
            ;;
        *)
            log_error "Unsupported architecture: $system_arch"
            log_error "Supported: x86_64 (amd64), aarch64/arm64, i386"
            exit 1
            ;;
    esac
}

# Validate dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v dpkg-deb >/dev/null 2>&1; then
        missing_deps+=("dpkg-deb")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Install with: sudo apt-get install ${missing_deps[*]}"
        exit 1
    fi
}

# Create package structure
create_package_structure() {
    local arch="$1"
    local package_name="${APP_DISPLAY_NAME// /}-Linux-${arch}"
    local package_dir="${DIST_DIR}/${package_name}"
    
    log_info "Creating Debian package structure..."
    
    # Remove existing package directory
    [[ -d "$package_dir" ]] && rm -rf "$package_dir"
    
    # Create directory structure
    mkdir -p "$package_dir"/{DEBIAN,opt/metadata-cleaner,usr/{share/{applications,pixmaps,doc/metadata-cleaner},local/bin}}
    
    # Copy application files - handle both directory and single file
    local app_source="${DIST_DIR}/MetadataCleaner"
    if [[ ! -d "$app_source" ]] && [[ ! -f "$app_source" ]]; then
        log_error "Built application not found: $app_source"
        log_error "Available files in dist/:"
        ls -la "${DIST_DIR}/" || echo "dist directory not found"
        log_error "Run 'python build.py' first"
        exit 1
    fi
    
    if [[ -d "$app_source" ]]; then
        # Directory structure from PyInstaller
        cp -r "$app_source"/* "$package_dir/opt/metadata-cleaner/"
        # Find and make executable
        find "$package_dir/opt/metadata-cleaner" -name "MetadataCleaner" -type f -exec chmod +x {} \;
    elif [[ -f "$app_source" ]]; then
        # Single file
        cp "$app_source" "$package_dir/opt/metadata-cleaner/MetadataCleaner"
        chmod +x "$package_dir/opt/metadata-cleaner/MetadataCleaner"
    fi
    
    # Copy icon
    local icon_source="${PROJECT_ROOT}/assets/icons/icon.png"
    if [[ -f "$icon_source" ]]; then
        cp "$icon_source" "$package_dir/usr/share/pixmaps/metadata-cleaner.png"
    else
        log_warning "Icon not found: $icon_source"
    fi
    
    # Copy documentation
    local license_source="${PROJECT_ROOT}/LICENSE"
    if [[ -f "$license_source" ]]; then
        cp "$license_source" "$package_dir/usr/share/doc/metadata-cleaner/copyright"
    fi
    
    # Create changelog
    cat > "$package_dir/usr/share/doc/metadata-cleaner/changelog.Debian" << EOF
metadata-cleaner (${APP_VERSION}-1) unstable; urgency=medium

  * Initial release of Metadata Cleaner
  * Privacy-focused metadata removal tool
  * Support for images, documents, PDFs, and videos
  * Cross-platform compatibility
  * Local processing for maximum security

 -- ${MAINTAINER}  $(date -R)
EOF
    
    gzip -9 "$package_dir/usr/share/doc/metadata-cleaner/changelog.Debian"
    
    echo "$package_dir"
}

# Create control file
create_control_file() {
    local package_dir="$1"
    local arch="$2"
    
    log_info "Creating control file..."
    
    # Calculate installed size
    local installed_size
    installed_size=$(du -sk "$package_dir" | cut -f1)
    
    cat > "$package_dir/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}-1
Section: utils
Priority: optional
Architecture: ${arch}
Depends: libgtk-3-0, libglib2.0-0, libcairo2, libpango-1.0-0, libgdk-pixbuf2.0-0
Recommends: ffmpeg
Installed-Size: ${installed_size}
Maintainer: ${MAINTAINER}
Homepage: https://github.com/AntGalanin06/Metadata_Cleaner
Description: Privacy tool for removing metadata from files
 Metadata Cleaner is a modern desktop application that removes metadata from
 various file types including images (JPG, PNG, GIF, HEIC), documents (DOCX,
 PPTX, XLSX), PDF files, and videos (MP4, MOV).
 .
 Key features:
  * 100% local processing - no data transmission
  * Automatic backup creation for safety
  * Selective metadata cleaning
  * Modern Material Design interface
  * Support for multiple file formats
 .
 All file processing happens locally on your device for maximum privacy and
 security. The application creates automatic backups of original files before
 cleaning to ensure data safety.
EOF
}

# Create desktop file
create_desktop_file() {
    local package_dir="$1"
    
    log_info "Creating desktop file..."
    
    cat > "$package_dir/usr/share/applications/metadata-cleaner.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Metadata Cleaner
GenericName=Privacy Tool
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Icon=metadata-cleaner
Exec=/opt/metadata-cleaner/MetadataCleaner %F
Path=/opt/metadata-cleaner
Categories=Utility;Privacy;Security;
Keywords=metadata;exif;privacy;cleaner;security;
MimeType=image/jpeg;image/png;image/gif;image/heic;image/heif;application/pdf;application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/vnd.openxmlformats-officedocument.presentationml.presentation;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;video/mp4;video/quicktime;
Terminal=false
StartupNotify=true
StartupWMClass=MetadataCleaner
NoDisplay=false
EOF
}

# Create launcher script
create_launcher() {
    local package_dir="$1"
    
    log_info "Creating launcher script..."
    
    cat > "$package_dir/usr/local/bin/metadata-cleaner" << 'EOF'
#!/bin/bash
# Metadata Cleaner launcher script

# Set up environment
export PATH="/opt/metadata-cleaner:$PATH"

# Handle file arguments
if [[ $# -gt 0 ]]; then
    exec /opt/metadata-cleaner/MetadataCleaner "$@"
else
    exec /opt/metadata-cleaner/MetadataCleaner
fi
EOF
    
    chmod +x "$package_dir/usr/local/bin/metadata-cleaner"
}

# Create maintainer scripts
create_maintainer_scripts() {
    local package_dir="$1"
    
    log_info "Creating maintainer scripts..."
    
    # Post-installation script
    cat > "$package_dir/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    configure)
        # Update desktop database
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database /usr/share/applications 2>/dev/null || true
        fi
        
        # Update MIME database
        if command -v update-mime-database >/dev/null 2>&1; then
            update-mime-database /usr/share/mime 2>/dev/null || true
        fi
        
        # Update icon cache
        if command -v gtk-update-icon-cache >/dev/null 2>&1; then
            gtk-update-icon-cache -f -t /usr/share/pixmaps 2>/dev/null || true
        fi
        
        echo "Metadata Cleaner installed successfully!"
        echo "Launch from applications menu or run: metadata-cleaner"
        ;;
esac

exit 0
EOF
    
    # Pre-removal script
    cat > "$package_dir/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    remove|upgrade|deconfigure)
        # Nothing special needed for removal
        ;;
esac

exit 0
EOF
    
    # Post-removal script
    cat > "$package_dir/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    remove|purge)
        # Update desktop database
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database /usr/share/applications 2>/dev/null || true
        fi
        
        # Update MIME database
        if command -v update-mime-database >/dev/null 2>&1; then
            update-mime-database /usr/share/mime 2>/dev/null || true
        fi
        
        # Update icon cache
        if command -v gtk-update-icon-cache >/dev/null 2>&1; then
            gtk-update-icon-cache -f -t /usr/share/pixmaps 2>/dev/null || true
        fi
        ;;
esac

exit 0
EOF
    
    # Make scripts executable
    chmod 755 "$package_dir/DEBIAN"/{postinst,prerm,postrm}
}

# Build package
build_package() {
    local package_dir="$1"
    local arch="$2"
    
    log_info "Building Debian package..."
    
    # Build package
    if ! dpkg-deb --build "$package_dir"; then
        log_error "Failed to build Debian package"
        exit 1
    fi
    
    # Move and rename package
    local package_file="${package_dir}.deb"
    local final_name="${DIST_DIR}/MetadataCleaner-Linux-${arch}.deb"
    
    if [[ -f "$package_file" ]]; then
        mv "$package_file" "$final_name"
        
        # Get package info
        local size
        size=$(du -h "$final_name" | cut -f1)
        
        log_success "Debian package created: $final_name ($size)"
        log_info "Installation:"
        log_info "  sudo dpkg -i $final_name"
        log_info "  sudo apt-get install -f  # Fix dependencies if needed"
        log_info "Removal:"
        log_info "  sudo apt-get remove metadata-cleaner"
        
        # Verify package
        log_info "Package verification:"
        dpkg-deb --info "$final_name" | head -20
        
        return 0
    else
        log_error "Package file not found after build"
        return 1
    fi
}

# Main function
main() {
    log_info "Starting Debian package build for Metadata Cleaner v${APP_VERSION}"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check dependencies
    check_dependencies
    
    # Detect architecture
    local arch
    arch=$(detect_architecture)
    log_info "Detected architecture: $(uname -m) → Debian: $arch"
    
    # Create package structure
    local package_dir
    package_dir=$(create_package_structure "$arch")
    
    # Create package files
    create_control_file "$package_dir" "$arch"
    create_desktop_file "$package_dir"
    create_launcher "$package_dir"
    create_maintainer_scripts "$package_dir"
    
    # Build package
    if build_package "$package_dir" "$arch"; then
        log_success "Debian package build completed successfully"
    else
        log_error "Debian package build failed"
        exit 1
    fi
    
    # Cleanup
    [[ -d "$package_dir" ]] && rm -rf "$package_dir"
    
    log_success "Build process finished"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi