#!/bin/bash
# Modern macOS DMG creator for Metadata Cleaner
# Version: 2.0.0

set -euo pipefail

# Configuration
readonly APP_NAME="Metadata Cleaner"
readonly APP_VERSION="1.0.1"
readonly DMG_NAME="MetadataCleaner-macOS"
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

# Check if running on macOS
check_platform() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        log_error "This script must be run on macOS"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    # Check for create-dmg
    if ! command -v create-dmg >/dev/null 2>&1; then
        log_info "create-dmg not found, will attempt to install via Homebrew"
        
        # Check for Homebrew
        if ! command -v brew >/dev/null 2>&1; then
            log_error "Homebrew not found. Please install it first:"
            log_error "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        
        log_info "Installing create-dmg via Homebrew..."
        if ! brew install create-dmg; then
            log_error "Failed to install create-dmg"
            exit 1
        fi
        log_success "create-dmg installed successfully"
    fi
    
    # Check for iconutil (should be available on all macOS systems)
    if ! command -v iconutil >/dev/null 2>&1; then
        missing_deps+=("iconutil")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing system tools: ${missing_deps[*]}"
        log_error "These should be available on all macOS systems"
        exit 1
    fi
}

# Validate app bundle
validate_app() {
    local app_path="${DIST_DIR}/MetadataCleaner.app"
    
    if [[ ! -d "$app_path" ]]; then
        log_error "MetadataCleaner.app not found: $app_path"
        log_error "Run 'python build.py' first to build the application"
        exit 1
    fi
    
    # Check app bundle structure
    local required_paths=(
        "$app_path/Contents/MacOS/MetadataCleaner"
        "$app_path/Contents/Info.plist"
    )
    
    for path in "${required_paths[@]}"; do
        if [[ ! -e "$path" ]]; then
            log_warning "Missing app bundle component: $path"
        fi
    done
    
    # Check if executable is actually executable
    if [[ ! -x "$app_path/Contents/MacOS/MetadataCleaner" ]]; then
        log_warning "Application executable is not marked as executable"
        chmod +x "$app_path/Contents/MacOS/MetadataCleaner"
    fi
    
    log_success "App bundle validation completed"
    echo "$app_path"
}

# Create DMG staging directory
create_staging_dir() {
    local staging_dir="${DIST_DIR}/dmg_staging"
    
    log_info "Creating DMG staging directory..."
    
    # Remove existing staging directory
    [[ -d "$staging_dir" ]] && rm -rf "$staging_dir"
    mkdir -p "$staging_dir"
    
    echo "$staging_dir"
}

# Copy app to staging
copy_app_to_staging() {
    local app_path="$1"
    local staging_dir="$2"
    
    log_info "Copying application to staging directory..."
    
    # Copy the app bundle
    cp -R "$app_path" "$staging_dir/"
    
    # Verify copy
    if [[ ! -d "$staging_dir/MetadataCleaner.app" ]]; then
        log_error "Failed to copy app bundle to staging directory"
        exit 1
    fi
    
    log_success "Application copied to staging directory"
}

# Create documentation files
create_documentation() {
    local staging_dir="$1"
    
    log_info "Creating documentation files..."
    
    # Create README for DMG
    cat > "$staging_dir/README.txt" << EOF
Metadata Cleaner for macOS
==========================

Thank you for downloading Metadata Cleaner!

Installation Instructions:
1. Drag "MetadataCleaner.app" to your Applications folder
2. Double-click to launch from Applications or Launchpad
3. Grant necessary permissions when prompted by macOS

System Requirements:
• macOS 10.15 (Catalina) or later
• Intel or Apple Silicon Mac
• 100 MB free disk space

First Launch:
When you first open Metadata Cleaner, macOS may show a security warning
because the app is not signed with an Apple Developer certificate.

To open the app:
1. Right-click on "MetadataCleaner.app"
2. Select "Open" from the context menu
3. Click "Open" in the security dialog

Features:
• Remove metadata from images (JPG, PNG, GIF, HEIC/HEIF)
• Clean documents (PDF, DOCX, PPTX, XLSX)
• Process videos (MP4, MOV)
• 100% local processing - no internet required
• Automatic backup creation for safety
• Modern, intuitive interface

Privacy & Security:
All file processing happens locally on your Mac. No data is transmitted
over the internet. Your privacy is completely protected.

Support:
• Project Homepage: https://github.com/AntGalanin06/Metadata_Cleaner
• Issues & Bug Reports: https://github.com/AntGalanin06/Metadata_Cleaner/issues
• Documentation: https://github.com/AntGalanin06/Metadata_Cleaner/wiki

Version: ${APP_VERSION}
License: MIT License

Thank you for choosing Metadata Cleaner!
EOF
    
    # Copy license if available
    local license_source="${PROJECT_ROOT}/LICENSE"
    if [[ -f "$license_source" ]]; then
        cp "$license_source" "$staging_dir/License.txt"
        log_success "License file copied"
    else
        log_warning "License file not found: $license_source"
    fi
    
    log_success "Documentation files created"
}

# Create DMG with create-dmg
create_dmg() {
    local staging_dir="$1"
    
    log_info "Creating DMG with create-dmg..."
    
    local dmg_output="${DIST_DIR}/${DMG_NAME}.dmg"
    
    # Remove existing DMG
    [[ -f "$dmg_output" ]] && rm -f "$dmg_output"
    
    # Determine background image
    local background_arg=""
    local background_image="${PROJECT_ROOT}/assets/screenshots/main-light-theme.png"
    if [[ -f "$background_image" ]]; then
        background_arg="--background $background_image"
        log_info "Using background image: $background_image"
    else
        log_info "No background image found, using default"
    fi
    
    # Determine volume icon
    local icon_arg=""
    local volume_icon="${PROJECT_ROOT}/assets/icons/icon.icns"
    if [[ -f "$volume_icon" ]]; then
        icon_arg="--volicon $volume_icon"
        log_info "Using volume icon: $volume_icon"
    else
        log_warning "Volume icon not found: $volume_icon"
    fi
    
    # Create DMG with enhanced settings
    local create_dmg_cmd=(
        create-dmg
        --volname "$APP_NAME"
        --window-pos 200 120
        --window-size 800 600
        --icon-size 80
        --icon "MetadataCleaner.app" 200 190
        --hide-extension "MetadataCleaner.app"
        --app-drop-link 600 190
        --text-size 14
        --format UDZO
        --hdiutil-verbose
    )
    
    # Add optional arguments
    [[ -n "$icon_arg" ]] && create_dmg_cmd+=($icon_arg)
    [[ -n "$background_arg" ]] && create_dmg_cmd+=($background_arg)
    
    # Add documentation files if they exist
    if [[ -f "$staging_dir/README.txt" ]]; then
        create_dmg_cmd+=(--icon "README.txt" 200 320)
    fi
    
    if [[ -f "$staging_dir/License.txt" ]]; then
        create_dmg_cmd+=(--icon "License.txt" 200 450)
    fi
    
    # Add output path and source directory
    create_dmg_cmd+=("$dmg_output" "$staging_dir")
    
    # Execute create-dmg
    if ! "${create_dmg_cmd[@]}"; then
        log_error "Failed to create DMG with create-dmg"
        
        # Fallback: create simple DMG with hdiutil
        log_info "Attempting fallback DMG creation..."
        create_simple_dmg "$staging_dir" "$dmg_output"
        return $?
    fi
    
    # Verify DMG was created
    if [[ -f "$dmg_output" ]]; then
        local size
        size=$(du -h "$dmg_output" | cut -f1)
        log_success "DMG created successfully: $dmg_output ($size)"
        
        # Test DMG mountability
        log_info "Testing DMG mountability..."
        if hdiutil attach "$dmg_output" -readonly -nobrowse -mountpoint "/tmp/dmg_test_$$" >/dev/null 2>&1; then
            hdiutil detach "/tmp/dmg_test_$$" >/dev/null 2>&1
            log_success "DMG mount test passed"
        else
            log_warning "DMG mount test failed, but file was created"
        fi
        
        return 0
    else
        log_error "DMG file was not created"
        return 1
    fi
}

# Fallback DMG creation with hdiutil
create_simple_dmg() {
    local staging_dir="$1"
    local dmg_output="$2"
    
    log_info "Creating simple DMG with hdiutil..."
    
    # Create temporary DMG
    local temp_dmg="${dmg_output}.tmp"
    
    # Calculate required size (with some padding)
    local size_kb
    size_kb=$(du -sk "$staging_dir" | cut -f1)
    local size_mb=$((size_kb / 1024 + 50))  # Add 50MB padding
    
    # Create DMG
    if ! hdiutil create -size "${size_mb}m" -fs HFS+ -volname "$APP_NAME" "$temp_dmg"; then
        log_error "Failed to create temporary DMG"
        return 1
    fi
    
    # Mount DMG
    local mount_point
    mount_point=$(hdiutil attach "$temp_dmg" -readwrite -nobrowse | grep "/Volumes" | cut -d$'\t' -f3)
    
    if [[ -z "$mount_point" ]]; then
        log_error "Failed to mount temporary DMG"
        return 1
    fi
    
    # Copy files to DMG
    cp -R "$staging_dir"/* "$mount_point/"
    
    # Create Applications symlink
    ln -s /Applications "$mount_point/Applications"
    
    # Unmount DMG
    hdiutil detach "$mount_point"
    
    # Convert to compressed DMG
    if ! hdiutil convert "$temp_dmg" -format UDZO -o "$dmg_output"; then
        log_error "Failed to compress DMG"
        rm -f "$temp_dmg"
        return 1
    fi
    
    # Cleanup
    rm -f "$temp_dmg"
    
    log_success "Simple DMG created: $dmg_output"
    return 0
}

# Code signing (optional)
sign_app() {
    local app_path="$1"
    
    # Check if code signing identity is available
    if ! security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
        log_info "No Developer ID certificate found, skipping code signing"
        log_info "For distribution outside Mac App Store, consider:"
        log_info "  1. Join Apple Developer Program"
        log_info "  2. Create Developer ID certificate"
        log_info "  3. Sign app with: codesign --sign \"Developer ID Application: Your Name\" \"$app_path\""
        return
    fi
    
    log_info "Code signing certificates found, attempting to sign..."
    
    # Sign the app (this will use the first available Developer ID certificate)
    if codesign --sign "Developer ID Application" --deep --force "$app_path"; then
        log_success "Application signed successfully"
        
        # Verify signature
        if codesign --verify --deep --strict "$app_path"; then
            log_success "Code signature verified"
        else
            log_warning "Code signature verification failed"
        fi
    else
        log_warning "Code signing failed, but continuing..."
    fi
}

# Main function
main() {
    log_info "Starting macOS DMG creation for Metadata Cleaner v${APP_VERSION}"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Platform check
    check_platform
    
    # Check dependencies
    check_dependencies
    
    # Validate app bundle
    local app_path
    app_path=$(validate_app)
    
    # Optional code signing
    sign_app "$app_path"
    
    # Create staging directory
    local staging_dir
    staging_dir=$(create_staging_dir)
    
    # Copy app to staging
    copy_app_to_staging "$app_path" "$staging_dir"
    
    # Create documentation
    create_documentation "$staging_dir"
    
    # Create DMG
    if create_dmg "$staging_dir"; then
        log_success "macOS DMG creation completed successfully"
        log_info "Distribution:"
        log_info "  1. Share ${DMG_NAME}.dmg with macOS users"
        log_info "  2. Users drag app to Applications folder"
        log_info "  3. Right-click → Open for first launch (if unsigned)"
    else
        log_error "DMG creation failed"
        exit 1
    fi
    
    # Cleanup
    [[ -d "$staging_dir" ]] && rm -rf "$staging_dir"
    
    log_success "Build process finished"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi