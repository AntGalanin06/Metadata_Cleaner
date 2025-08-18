#!/bin/bash
# Modern AppImage builder for Metadata Cleaner with multi-architecture support
# Version: 2.0.0

set -euo pipefail

# Configuration
readonly APP_NAME="MetadataCleaner"
readonly APP_VERSION="1.0.1"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly DIST_DIR="${PROJECT_ROOT}/dist"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

cleanup() {
    local appdir="${DIST_DIR}/${APP_NAME}.AppDir"
    [[ -d "$appdir" ]] && rm -rf "$appdir"
}

# Auto-detect architecture
detect_architecture() {
    local system_arch
    system_arch=$(uname -m)
    
    case "$system_arch" in
        "x86_64"|"amd64")
            echo "x64"
            ;;
        "aarch64"|"arm64")
            echo "arm64"
            ;;
        *)
            log_error "Unsupported architecture: $system_arch"
            log_error "Supported: x86_64, aarch64/arm64"
            exit 1
            ;;
    esac
}

# Download AppImageTool
download_appimagetool() {
    local arch="$1"
    local tool_arch
    
    case "$arch" in
        "x64") tool_arch="x86_64" ;;
        "arm64") tool_arch="aarch64" ;;
    esac
    
    local tool_name="appimagetool-${tool_arch}.AppImage"
    local tool_path="${PROJECT_ROOT}/${tool_name}"
    
    if [[ -f "$tool_path" ]]; then
        log_info "AppImageTool already exists: $tool_path"
        echo "$tool_path"
        return
    fi
    
    log_info "Downloading AppImageTool for $tool_arch..."
    local url="https://github.com/AppImage/AppImageKit/releases/download/continuous/${tool_name}"
    
    if ! curl -L "$url" -o "$tool_path"; then
        log_error "Failed to download AppImageTool"
        exit 1
    fi
    
    chmod +x "$tool_path"
    log_success "AppImageTool downloaded: $tool_path"
    echo "$tool_path"
}

# Create AppDir structure
create_appdir() {
    local arch="$1"
    local appdir="${DIST_DIR}/${APP_NAME}.AppDir"
    
    log_info "Creating AppDir structure..."
    
    # Remove existing AppDir
    [[ -d "$appdir" ]] && rm -rf "$appdir"
    
    # Create directory structure
    mkdir -p "$appdir"/{usr/{bin,lib,share/{applications,icons/hicolor/256x256/apps}}}
    
    # Copy application files
    local app_source="${DIST_DIR}/${APP_NAME}"
    if [[ ! -d "$app_source" ]]; then
        log_error "Built application not found: $app_source"
        log_error "Run 'python build.py' first"
        exit 1
    fi
    
    # Handle PyInstaller directory or single executable
    if [[ -d "$app_source" ]] && [[ -f "$app_source/${APP_NAME}" ]]; then
        # PyInstaller created a directory with executable inside
        log_info "Found PyInstaller directory structure"
        cp -r "$app_source"/* "$appdir/usr/bin/"
        chmod +x "$appdir/usr/bin/${APP_NAME}"
    elif [[ -f "$app_source" ]]; then
        # Single executable file
        log_info "Found single executable file"
        cp "$app_source" "$appdir/usr/bin/${APP_NAME}"
        chmod +x "$appdir/usr/bin/${APP_NAME}"
    else
        log_error "Could not determine application structure in: $app_source"
        ls -la "$app_source" 2>/dev/null || echo "Directory does not exist"
        exit 1
    fi
    
    # Copy icon
    local icon_source="${PROJECT_ROOT}/assets/icons/icon.png"
    if [[ -f "$icon_source" ]]; then
        cp "$icon_source" "$appdir/usr/share/icons/hicolor/256x256/apps/metadata-cleaner.png"
        cp "$icon_source" "$appdir/metadata-cleaner.png"
    else
        log_warning "Icon not found: $icon_source"
    fi
    
    # Create AppRun script
    cat > "$appdir/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH:-}"

# Find and run the executable
EXEC_PATH="${HERE}/usr/bin/MetadataCleaner"

if [[ -x "$EXEC_PATH" ]]; then
    cd "${HERE}/usr/bin" && exec "./MetadataCleaner" "$@"
else
    echo "Error: MetadataCleaner executable not found or not executable"
    echo "Available files in ${HERE}/usr/bin/:"
    ls -la "${HERE}/usr/bin/"
    exit 1
fi
EOF
    chmod +x "$appdir/AppRun"
    
    # Create desktop file
    cat > "$appdir/metadata-cleaner.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Metadata Cleaner
GenericName=Privacy Tool
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Icon=metadata-cleaner
Exec=MetadataCleaner
Categories=Utility;Security;
Keywords=metadata;exif;privacy;cleaner;security;
MimeType=image/jpeg;image/png;image/gif;image/heic;image/heif;application/pdf;application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/vnd.openxmlformats-officedocument.presentationml.presentation;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;video/mp4;video/quicktime;
Terminal=false
StartupNotify=true
StartupWMClass=MetadataCleaner
X-AppImage-Version=${APP_VERSION}
X-AppImage-Arch=${arch}
EOF
    
    # Copy desktop file to applications
    cp "$appdir/metadata-cleaner.desktop" "$appdir/usr/share/applications/"
    
    log_success "AppDir created: $appdir"
    echo "$appdir"
}

# Build AppImage
build_appimage() {
    local arch="$1"
    local appdir="$2"
    local appimagetool="$3"
    
    log_info "Building AppImage for $arch architecture..."
    
    local output="${DIST_DIR}/${APP_NAME}-Linux-${arch}.AppImage"
    
    # Remove any existing output file
    [[ -f "$output" ]] && rm -f "$output"
    
    log_info "AppImageTool: $appimagetool"
    log_info "AppDir: $appdir"
    log_info "Output: $output"
    
    # Try building with FUSE (with detailed error output)
    log_info "Trying AppImage build with FUSE..."
    if APPIMAGE_EXTRACT_AND_RUN=1 "$appimagetool" --no-appstream "$appdir" "$output"; then
        log_success "AppImage created successfully with FUSE"
    else
        log_warning "FUSE method failed, trying without FUSE..."
        if "$appimagetool" --appimage-extract-and-run --no-appstream "$appdir" "$output"; then
            log_success "AppImage created successfully without FUSE"
        else
        log_warning "AppImageTool failed, creating portable archive instead..."
        
        # Create portable fallback
        cd "${DIST_DIR}"
        tar czf "${APP_NAME}-Linux-Portable-${arch}.tar.gz" "${APP_NAME}/"
        cd - > /dev/null
        
        log_success "Portable archive created: ${DIST_DIR}/${APP_NAME}-Linux-Portable-${arch}.tar.gz"
        log_info "Usage: Extract archive and run ./${APP_NAME}"
        return 1
    fi
    
    # Make executable and verify
    chmod +x "$output"
    
    if [[ -f "$output" ]]; then
        local size
        size=$(du -h "$output" | cut -f1)
        log_success "AppImage created: $output ($size)"
        log_info "Distribution: Share this single file with Linux users"
        log_info "Usage: ./${APP_NAME}-Linux-${arch}.AppImage"
        return 0
    else
        log_error "Failed to create AppImage"
        return 1
    fi
}

# Main function
main() {
    log_info "Starting AppImage build for Metadata Cleaner v${APP_VERSION}"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Detect architecture
    local arch
    arch=$(detect_architecture)
    log_info "Detected architecture: $(uname -m) → AppImage: $arch"
    
    # Download AppImageTool
    local appimagetool
    appimagetool=$(download_appimagetool "$arch")
    
    # Create AppDir
    local appdir
    appdir=$(create_appdir "$arch")
    
    # Build AppImage
    if build_appimage "$arch" "$appdir" "$appimagetool"; then
        log_success "AppImage build completed successfully"
    else
        log_warning "AppImage build completed with fallback"
    fi
    
    # Don't cleanup on failure - keep files for debugging
    if [[ $? -eq 0 ]]; then
        cleanup
    else
        log_warning "Keeping AppDir for debugging: $appdir"
    fi
    
    log_success "Build process finished"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi