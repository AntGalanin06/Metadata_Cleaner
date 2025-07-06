#!/bin/bash
# Metadata Cleaner Linux Installer with multilingual license

set -e

APP_NAME="Metadata Cleaner"
APP_DIR="MetadataCleaner"
INSTALL_DIR="/opt/metadata-cleaner"
DESKTOP_FILE="/usr/share/applications/metadata-cleaner.desktop"
BIN_LINK="/usr/local/bin/metadata-cleaner"

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
    
    # Check for built application
    if [[ ! -d "dist/$APP_DIR" ]]; then
        echo "❌ Directory dist/$APP_DIR not found."
        echo "Build the application first: python build.py"
        exit 1
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy application files
    cp -r "dist/$APP_DIR"/* "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/MetadataCleaner"
    
    # Copy icon
    if [[ -f "assets/icons/icon.png" ]]; then
        mkdir -p "/usr/share/pixmaps"
        cp "assets/icons/icon.png" "/usr/share/pixmaps/metadata-cleaner.png"
    fi
    
    # Create .desktop file
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
EOF
    
    # Create symbolic link for terminal launch
    ln -sf "$INSTALL_DIR/MetadataCleaner" "$BIN_LINK"
    
    # Update applications database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications
    fi
    
    echo "✅ Installation completed successfully!"
    echo "📱 Application available in applications menu"
    echo "💻 Terminal launch: metadata-cleaner"
    echo "📁 Installed to: $INSTALL_DIR"
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
    
    # Check administrator rights
    check_root
    
    # Install application
    install_app
}

# Run installer
main "$@" 