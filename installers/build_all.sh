#!/bin/bash
# Universal installer builder for all platforms
# Version: 2.0.0

set -euo pipefail

# Configuration
readonly APP_NAME="Metadata Cleaner"
readonly APP_VERSION="1.0.1"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Show help
show_help() {
    cat << EOF
Universal Installer Builder for ${APP_NAME}

USAGE:
    ./build_all.sh [OPTIONS] [PLATFORMS...]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose          Enable verbose output
    --clean               Clean previous builds
    --app-only            Build application only (skip installers)

PLATFORMS:
    linux                 Build Linux packages (AppImage, DEB, RPM)
    macos                 Build macOS DMG (macOS only)
    windows               Build Windows installer (requires NSIS)
    all                   Build for current platform (default)

EXAMPLES:
    ./build_all.sh                    # Build for current platform
    ./build_all.sh linux              # Build Linux packages only
    ./build_all.sh --clean all        # Clean and build everything
    ./build_all.sh --app-only         # Build app only, no installers

REQUIREMENTS:
    - Python 3.11+ with poetry
    - Platform-specific tools (see individual installer scripts)

EOF
}

# Detect current platform
detect_platform() {
    case "$(uname -s)" in
        "Darwin")
            echo "macos"
            ;;
        "Linux")
            echo "linux"
            ;;
        "CYGWIN"*|"MINGW"*|"MSYS"*)
            echo "windows"
            ;;
        *)
            log_error "Unsupported platform: $(uname -s)"
            exit 1
            ;;
    esac
}

# Clean previous builds
clean_builds() {
    log_info "Cleaning previous builds..."
    
    cd "$PROJECT_ROOT"
    
    # Remove build directories
    local dirs_to_clean=("dist" "build" "*.egg-info" "__pycache__" ".pytest_cache")
    
    for dir in "${dirs_to_clean[@]}"; do
        if [[ -d "$dir" ]]; then
            rm -rf "$dir"
            log_info "Removed: $dir"
        fi
    done
    
    # Remove installer artifacts
    find . -name "*.AppImage" -delete 2>/dev/null || true
    find . -name "*.deb" -delete 2>/dev/null || true
    find . -name "*.rpm" -delete 2>/dev/null || true
    find . -name "*.dmg" -delete 2>/dev/null || true
    find . -name "*.exe" -delete 2>/dev/null || true
    
    log_success "Build cleanup completed"
}

# Build application
build_application() {
    log_info "Building ${APP_NAME} application..."
    
    cd "$PROJECT_ROOT"
    
    # Check if build.py exists
    if [[ ! -f "build.py" ]]; then
        log_error "build.py not found in project root"
        exit 1
    fi
    
    # Run build script with Poetry
    if command -v poetry >/dev/null 2>&1; then
        poetry run python build.py
    else
        python build.py
    fi
    
    # Verify build output
    if [[ ! -d "dist" ]]; then
        log_error "Build failed - no dist directory created"
        exit 1
    fi
    
    log_success "Application build completed"
}

# Build Linux packages
build_linux() {
    log_info "Building Linux packages..."
    
    local linux_dir="${SCRIPT_DIR}/linux"
    local installers=("appimage.sh" "deb.sh" "rpm.sh")
    
    for installer in "${installers[@]}"; do
        local installer_path="${linux_dir}/${installer}"
        
        if [[ -x "$installer_path" ]]; then
            log_info "Running ${installer}..."
            if "$installer_path"; then
                log_success "${installer} completed successfully"
            else
                log_warning "${installer} failed, continuing with others"
            fi
        else
            log_warning "Installer not found or not executable: $installer_path"
        fi
    done
    
    log_success "Linux package build completed"
}

# Build macOS DMG
build_macos() {
    local platform
    platform=$(detect_platform)
    
    if [[ "$platform" != "macos" ]]; then
        log_error "macOS DMG can only be built on macOS"
        return 1
    fi
    
    log_info "Building macOS DMG..."
    
    local macos_dir="${SCRIPT_DIR}/macos"
    local installer_path="${macos_dir}/dmg.sh"
    
    if [[ -x "$installer_path" ]]; then
        "$installer_path"
        log_success "macOS DMG build completed"
    else
        log_error "macOS installer not found or not executable: $installer_path"
        return 1
    fi
}

# Build Windows installer
build_windows() {
    log_info "Building Windows installer..."
    
    local windows_dir="${SCRIPT_DIR}/windows"
    
    # Check for PowerShell script first (Windows)
    if command -v powershell >/dev/null 2>&1; then
        local ps_script="${windows_dir}/build.ps1"
        if [[ -f "$ps_script" ]]; then
            log_info "Using PowerShell build script..."
            powershell -ExecutionPolicy Bypass -File "$ps_script"
            log_success "Windows installer build completed"
            return
        fi
    fi
    
    # Fallback to NSIS directly
    if command -v makensis >/dev/null 2>&1; then
        local nsi_script="${windows_dir}/installer.nsi"
        if [[ -f "$nsi_script" ]]; then
            log_info "Using NSIS directly..."
            cd "$windows_dir"
            makensis "$nsi_script"
            log_success "Windows installer build completed"
            return
        fi
    fi
    
    log_error "Neither PowerShell nor NSIS found for Windows build"
    log_info "Install NSIS from https://nsis.sourceforge.io/"
    return 1
}

# Build for platform
build_platform() {
    local platform="$1"
    
    case "$platform" in
        "linux")
            build_linux
            ;;
        "macos")
            build_macos
            ;;
        "windows")
            build_windows
            ;;
        "all")
            local current_platform
            current_platform=$(detect_platform)
            build_platform "$current_platform"
            ;;
        *)
            log_error "Unknown platform: $platform"
            log_error "Supported: linux, macos, windows, all"
            exit 1
            ;;
    esac
}

# Show build summary
show_summary() {
    log_info "Build Summary"
    log_info "============="
    
    cd "$PROJECT_ROOT"
    
    if [[ -d "dist" ]]; then
        log_info "Build outputs in dist/:"
        find dist -type f \( -name "*.AppImage" -o -name "*.deb" -o -name "*.rpm" -o -name "*.dmg" -o -name "*.exe" \) | while read -r file; do
            local size
            size=$(du -h "$file" | cut -f1)
            log_success "  $(basename "$file") ($size)"
        done
    fi
    
    log_info ""
    log_info "Distribution Notes:"
    log_info "  - Test installers before distribution"
    log_info "  - Consider code signing for trusted deployment"
    log_info "  - Provide installation instructions for users"
}

# Main function
main() {
    local platforms=()
    local verbose=false
    local clean=false
    local app_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            --clean)
                clean=true
                shift
                ;;
            --app-only)
                app_only=true
                shift
                ;;
            linux|macos|windows|all)
                platforms+=("$1")
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Default to current platform if no platforms specified
    if [[ ${#platforms[@]} -eq 0 ]]; then
        platforms=("all")
    fi
    
    # Enable verbose output if requested
    if [[ "$verbose" == "true" ]]; then
        set -x
    fi
    
    log_info "Starting ${APP_NAME} v${APP_VERSION} build process"
    log_info "Platforms: ${platforms[*]}"
    
    # Clean if requested
    if [[ "$clean" == "true" ]]; then
        clean_builds
    fi
    
    # Build application
    build_application
    
    # Build installers unless app-only
    if [[ "$app_only" == "false" ]]; then
        for platform in "${platforms[@]}"; do
            log_info "Building for platform: $platform"
            build_platform "$platform"
        done
    fi
    
    # Show summary
    show_summary
    
    log_success "Build process completed successfully!"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi