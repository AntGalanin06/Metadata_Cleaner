#!/bin/bash
# Metadata Cleaner Linux Installer with multilingual license

set -e

APP_NAME="Metadata Cleaner"
APP_DIR="MetadataCleaner"
INSTALL_DIR="/opt/metadata-cleaner"
DESKTOP_FILE="/usr/share/applications/metadata-cleaner.desktop"
BIN_LINK="/usr/local/bin/metadata-cleaner"

# Function to detect Linux distribution
detect_distro() {
    if [[ -f "/etc/os-release" ]]; then
        source /etc/os-release
        echo "$ID"
    elif [[ -f "/etc/lsb-release" ]]; then
        source /etc/lsb-release
        echo "$DISTRIB_ID" | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

# Function to check system dependencies
check_dependencies() {
    echo "🔍 Checking system dependencies..."
    
    local missing_deps=()
    local distro=$(detect_distro)
    
    # Check for required libraries
    if ! ldconfig -p | grep -q "libgtk-3"; then
        missing_deps+=("libgtk-3-0" "libgtk-3-dev")
    fi
    
    if ! ldconfig -p | grep -q "libglib-2.0"; then
        missing_deps+=("libglib2.0-0")
    fi
    
    if ! ldconfig -p | grep -q "libcairo"; then
        missing_deps+=("libcairo2")
    fi
    
    if ! ldconfig -p | grep -q "libpango"; then
        missing_deps+=("libpango-1.0-0")
    fi
    
    # Check for desktop integration tools
    if ! command -v update-desktop-database >/dev/null 2>&1; then
        missing_deps+=("desktop-file-utils")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo "⚠️  Missing dependencies detected: ${missing_deps[*]}"
        echo "📦 Please install them using your package manager:"
        
        case "$distro" in
            "ubuntu"|"debian")
                echo "   sudo apt update && sudo apt install ${missing_deps[*]}"
                ;;
            "fedora"|"rhel"|"centos")
                echo "   sudo dnf install ${missing_deps[*]}"
                ;;
            "arch"|"manjaro")
                echo "   sudo pacman -S ${missing_deps[*]}"
                ;;
            "opensuse"|"suse")
                echo "   sudo zypper install ${missing_deps[*]}"
                ;;
            *)
                echo "   Use your distribution's package manager to install the above packages."
                ;;
        esac
        
        echo ""
        echo "Do you want to continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            exit 1
        fi
    else
        echo "✅ All required dependencies are available."
    fi
}

# Function to check Ubuntu version compatibility
check_ubuntu_compatibility() {
    if [[ -f "/etc/lsb-release" ]]; then
        source /etc/lsb-release
        if [[ "$DISTRIB_ID" == "Ubuntu" ]]; then
            local version_major=$(echo "$DISTRIB_RELEASE" | cut -d'.' -f1)
            local version_minor=$(echo "$DISTRIB_RELEASE" | cut -d'.' -f2)
            
            # Check if Ubuntu version is 18.04 or newer
            if [[ $version_major -lt 18 ]] || [[ $version_major -eq 18 && $version_minor -lt 4 ]]; then
                echo "⚠️  Ubuntu $DISTRIB_RELEASE detected."
                echo "   Minimum supported version is Ubuntu 18.04."
                echo "   The application might not work correctly on this version."
                echo ""
                echo "Do you want to continue anyway? (y/N)"
                read -r response
                if [[ ! "$response" =~ ^[Yy]$ ]]; then
                    echo "Installation cancelled."
                    exit 1
                fi
            else
                echo "✅ Ubuntu $DISTRIB_RELEASE is supported."
            fi
        fi
    fi
}

# Function to show multilingual license
show_license() {
    local license_file="docs/LICENSE_INSTALLER.txt"
    
    echo "========================================="
    echo "LICENSE AGREEMENT"
    echo "========================================="
    
    if [[ -f "$license_file" ]]; then
        cat "$license_file"
        echo ""
        echo "========================================="
        echo "Do you agree to the license terms? (y/N)"
        
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            exit 1
        fi
    else
        echo "⚠️  License file not found: $license_file"
    fi
}

# Function to check administrator rights
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "❌ Administrator rights required for installation."
        echo "Run: sudo $0"
        exit 1
    fi
}

# Function to install application
install_app() {
    echo "🔧 Installing $APP_NAME..."
    
    # Check for built application (both directory and single file)
    local app_source=""
    if [[ -d "dist/$APP_DIR" ]]; then
        app_source="dist/$APP_DIR"
        echo "✅ Found application directory: $app_source"
    elif [[ -f "dist/MetadataCleaner" ]]; then
        app_source="dist/MetadataCleaner"
        echo "✅ Found application executable: $app_source"
    else
        echo "❌ Application not found."
        echo "Expected either 'dist/$APP_DIR/' directory or 'dist/MetadataCleaner' file."
        echo "Build the application first: python build.py"
        exit 1
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy application files
    if [[ -d "$app_source" ]]; then
        # Directory-based installation
        cp -r "$app_source"/* "$INSTALL_DIR/"
        chmod +x "$INSTALL_DIR/MetadataCleaner"
    else
        # Single file installation
        cp "$app_source" "$INSTALL_DIR/MetadataCleaner"
        chmod +x "$INSTALL_DIR/MetadataCleaner"
        
        # Copy bundled resources if they exist
        if [[ -d "assets" ]]; then
            cp -r "assets" "$INSTALL_DIR/"
        fi
        if [[ -d "bundled_ffmpeg" ]]; then
            cp -r "bundled_ffmpeg" "$INSTALL_DIR/"
        fi
    fi
    
    # Copy icon with fallback
    local icon_installed=false
    if [[ -f "assets/icons/icon.png" ]]; then
        mkdir -p "/usr/share/pixmaps"
        cp "assets/icons/icon.png" "/usr/share/pixmaps/metadata-cleaner.png"
        icon_installed=true
    elif [[ -f "$INSTALL_DIR/assets/icons/icon.png" ]]; then
        mkdir -p "/usr/share/pixmaps"
        cp "$INSTALL_DIR/assets/icons/icon.png" "/usr/share/pixmaps/metadata-cleaner.png"
        icon_installed=true
    fi
    
    if [[ "$icon_installed" == false ]]; then
        echo "⚠️  Application icon not found, using default."
    fi
    
    # Create .desktop file with better validation
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Metadata Cleaner
Name[ru]=Metadata Cleaner
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Exec=$INSTALL_DIR/MetadataCleaner
Icon=metadata-cleaner
Terminal=false
Type=Application
Categories=Utility;Privacy;
StartupWMClass=MetadataCleaner
StartupNotify=true
MimeType=image/jpeg;image/png;image/gif;application/pdf;application/vnd.openxmlformats-officedocument.wordprocessingml.document;
Keywords=metadata;exif;privacy;cleaner;
EOF
    
    # Validate desktop file
    if command -v desktop-file-validate >/dev/null 2>&1; then
        if desktop-file-validate "$DESKTOP_FILE"; then
            echo "✅ Desktop file validation passed."
        else
            echo "⚠️  Desktop file validation failed, but continuing..."
        fi
    fi
    
    # Create symbolic link for terminal launch
    ln -sf "$INSTALL_DIR/MetadataCleaner" "$BIN_LINK"
    
    # Update applications database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications
        echo "✅ Desktop database updated."
    fi
    
    # Update MIME database if available
    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database /usr/share/mime
        echo "✅ MIME database updated."
    fi
    
    echo "✅ Installation completed successfully!"
    echo "📱 Application available in applications menu"
    echo "💻 Terminal launch: metadata-cleaner"
    echo "📁 Installed to: $INSTALL_DIR"
    
    # Show post-installation info
    echo ""
    echo "📋 Post-installation information:"
    echo "   • Configuration: ~/.config/metadata-cleaner/"
    echo "   • Logs: ~/.local/share/metadata-cleaner/"
    echo "   • Uninstall: sudo $0 --uninstall"
}

# Function to uninstall application
uninstall_app() {
    echo "🗑️  Uninstalling $APP_NAME..."
    echo "Are you sure? (y/N)"
    
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
    
    # Remove files
    rm -rf "$INSTALL_DIR"
    rm -f "$DESKTOP_FILE"
    rm -f "$BIN_LINK"
    rm -f "/usr/share/pixmaps/metadata-cleaner.png"
    
    # Update applications database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications
    fi
    
    echo "✅ Uninstallation completed."
}

# Main function
main() {
    echo "🛠️  Metadata Cleaner Linux Installer"
    echo "========================================="
    
    # Check arguments
    if [[ "$1" == "--uninstall" || "$1" == "-u" ]]; then
        check_root
        uninstall_app
        exit 0
    fi
    
    # Show license
    show_license
    
    # Check Ubuntu compatibility
    check_ubuntu_compatibility
    
    # Check system dependencies
    check_dependencies
    
    # Check administrator rights
    check_root
    
    # Install application
    install_app
}

# Run installer
main "$@" 