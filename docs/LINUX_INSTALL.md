# Linux Installation Guide for Metadata Cleaner

## System Requirements

- **Supported distributions**: Ubuntu 18.04+, Debian 10+, Fedora 28+, CentOS 8+, Arch Linux, openSUSE Leap 15+
- **Architecture**: x86_64 (64-bit)
- **Memory**: 1GB RAM minimum, 2GB recommended
- **Disk space**: 200MB free space

## Prerequisites

### Ubuntu/Debian
```bash
sudo apt update && sudo apt install libgtk-3-0 libglib2.0-0 libcairo2 libpango-1.0-0 desktop-file-utils
```

### Fedora/RHEL/CentOS
```bash
sudo dnf install gtk3 glib2 cairo pango desktop-file-utils
```

### Arch Linux/Manjaro
```bash
sudo pacman -S gtk3 glib2 cairo pango desktop-file-utils
```

### openSUSE
```bash
sudo zypper install libgtk-3-0 libglib-2_0-0 libcairo2 libpango-1_0-0 desktop-file-utils
```

## Installation Methods

### Method 1: Using the Installer Script (Recommended)

1. **Download the application:**
   - Download the latest release from [GitHub Releases](https://github.com/AntGalanin06/Metadata_Cleaner/releases)
   - Extract the archive: `tar -xzf MetadataCleaner-Linux.tar.gz`

2. **Run the installer:**
   ```bash
   cd MetadataCleaner-Linux
   chmod +x installer_linux.sh
   sudo ./installer_linux.sh
   ```

3. **Follow the prompts:**
   - Read and accept the license agreement
   - The installer will check system dependencies
   - Confirm installation when prompted

### Method 2: Manual Installation

1. **Extract the application:**
   ```bash
   sudo mkdir -p /opt/metadata-cleaner
   sudo tar -xzf MetadataCleaner-Linux.tar.gz -C /opt/metadata-cleaner --strip-components=1
   sudo chmod +x /opt/metadata-cleaner/MetadataCleaner
   ```

2. **Create desktop entry:**
   ```bash
   sudo tee /usr/share/applications/metadata-cleaner.desktop > /dev/null <<EOF
   [Desktop Entry]
   Name=Metadata Cleaner
   Comment=Remove metadata from files
   Exec=/opt/metadata-cleaner/MetadataCleaner
   Icon=metadata-cleaner
   Type=Application
   Categories=Utility;Privacy;
   Terminal=false
   EOF
   ```

3. **Create command line link:**
   ```bash
   sudo ln -sf /opt/metadata-cleaner/MetadataCleaner /usr/local/bin/metadata-cleaner
   ```

## Usage

### Graphical Interface
- Launch from Applications menu: **Utilities → Metadata Cleaner**
- Or run from terminal: `metadata-cleaner`

### Command Line
```bash
metadata-cleaner [options] [files...]
```

## Troubleshooting

### Common Issues

1. **"Application not found" after installation**
   - Update desktop database: `sudo update-desktop-database /usr/share/applications`
   - Logout and login again

2. **Permission denied errors**
   - Ensure the installer is run with `sudo`
   - Check file permissions: `ls -la /opt/metadata-cleaner/`

3. **Missing dependencies**
   - Install required packages using your distribution's package manager
   - Run the installer again - it will check dependencies

4. **Application won't start**
   - Check if all dependencies are installed
   - Try running from terminal to see error messages: `/opt/metadata-cleaner/MetadataCleaner`

### Distribution-Specific Notes

- **Ubuntu 18.04**: Some newer features may not be available
- **CentOS 7**: May require additional repository configuration
- **Arch Linux**: AUR package may be available in the future

## Uninstallation

To remove Metadata Cleaner:
```bash
sudo ./installer_linux.sh --uninstall
```

Or manually:
```bash
sudo rm -rf /opt/metadata-cleaner
sudo rm /usr/share/applications/metadata-cleaner.desktop
sudo rm /usr/local/bin/metadata-cleaner
sudo rm /usr/share/pixmaps/metadata-cleaner.png
```

## Support

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/AntGalanin06/Metadata_Cleaner/issues)
- **Documentation**: [README](https://github.com/AntGalanin06/Metadata_Cleaner/blob/main/README.md)

## Building from Source

If you prefer to build from source:

1. **Install dependencies:**
   ```bash
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Clone and build:**
   ```bash
   git clone https://github.com/AntGalanin06/Metadata_Cleaner.git
   cd Metadata_Cleaner
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 build.py
   ```

3. **Install:**
   ```bash
   sudo ./installer_linux.sh
   ```