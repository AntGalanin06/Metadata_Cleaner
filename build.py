#!/usr/bin/env python3
"""
Modern build script for Metadata Cleaner.
Supports all platforms with enhanced error handling and logging.
Version: 2.0.0
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
APP_NAME = "MetadataCleaner"
APP_VERSION = "1.0.1"
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
ASSETS_DIR = PROJECT_ROOT / "assets"
BUNDLED_FFMPEG_DIR = PROJECT_ROOT / "bundled_ffmpeg"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Custom exception for build errors."""

    pass


class PlatformBuilder:
    """Base class for platform-specific builders."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.system = platform.system()
        self.machine = platform.machine()

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def run_command(
        self, cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = False
    ) -> subprocess.CompletedProcess:
        """Run a command with proper error handling."""
        logger.debug(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=capture_output, text=True, check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Exit code: {e.returncode}")
            if e.stdout:
                logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr}")
            raise BuildError(f"Command failed: {' '.join(cmd)}") from e

    def ensure_directory(self, path: Path) -> None:
        """Ensure directory exists."""
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {path}")

    def check_dependencies(self) -> None:
        """Check required dependencies."""
        try:
            import PyInstaller

            logger.info(f"PyInstaller found: {PyInstaller.__version__}")
        except ImportError:
            logger.info("Installing PyInstaller...")
            self.run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
            logger.info("PyInstaller installed")

    def create_assets_folder(self) -> None:
        """Create assets folder structure."""
        logger.info("Creating assets folder structure...")

        self.ensure_directory(ASSETS_DIR / "icons")
        self.ensure_directory(ASSETS_DIR / "screenshots")

        logger.info("Assets folder structure created")

    def download_ffmpeg(self) -> Path:
        """Download FFmpeg for the current platform."""
        logger.info(f"Downloading FFmpeg for {self.system} {self.machine}...")

        self.ensure_directory(BUNDLED_FFMPEG_DIR)

        # Check if FFmpeg already exists
        ffmpeg_binary = self._get_ffmpeg_binary_name()
        ffmpeg_path = BUNDLED_FFMPEG_DIR / ffmpeg_binary

        if ffmpeg_path.exists():
            logger.info(f"FFmpeg already exists: {ffmpeg_path}")
            return BUNDLED_FFMPEG_DIR

        # Download based on platform
        if self.system == "Windows":
            return self._download_ffmpeg_windows()
        elif self.system == "Darwin":
            return self._download_ffmpeg_macos()
        elif self.system == "Linux":
            return self._download_ffmpeg_linux()
        else:
            logger.warning(f"FFmpeg auto-download not supported for {self.system}")
            return BUNDLED_FFMPEG_DIR

    def _get_ffmpeg_binary_name(self) -> str:
        """Get the expected FFmpeg binary name for the platform."""
        return "ffmpeg.exe" if self.system == "Windows" else "ffmpeg"

    def _download_ffmpeg_windows(self) -> Path:
        """Download FFmpeg for Windows."""
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "ffmpeg.zip"

            logger.info(f"Downloading from {url}...")
            urllib.request.urlretrieve(url, zip_path)

            logger.info("Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find ffmpeg.exe
            for ffmpeg_file in Path(temp_dir).rglob("ffmpeg.exe"):
                if ffmpeg_file.is_file():
                    target_path = BUNDLED_FFMPEG_DIR / "ffmpeg.exe"
                    shutil.copy2(ffmpeg_file, target_path)
                    logger.info(f"FFmpeg downloaded: {target_path}")
                    return BUNDLED_FFMPEG_DIR

            raise BuildError("ffmpeg.exe not found in downloaded archive")

    def _download_ffmpeg_macos(self) -> Path:
        """Download FFmpeg for macOS."""
        url = "https://evermeet.cx/pub/ffmpeg/ffmpeg.zip"

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "ffmpeg.zip"

            logger.info(f"Downloading from {url}...")
            urllib.request.urlretrieve(url, zip_path)

            logger.info("Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find ffmpeg binary
            for ffmpeg_file in Path(temp_dir).rglob("ffmpeg"):
                if ffmpeg_file.is_file() and ffmpeg_file.name == "ffmpeg":
                    target_path = BUNDLED_FFMPEG_DIR / "ffmpeg"
                    shutil.copy2(ffmpeg_file, target_path)
                    target_path.chmod(0o755)
                    logger.info(f"FFmpeg downloaded: {target_path}")
                    return BUNDLED_FFMPEG_DIR

            raise BuildError("ffmpeg not found in downloaded archive")

    def _download_ffmpeg_linux(self) -> Path:
        """Download FFmpeg for Linux."""
        arch = self.machine.lower()

        if arch in ["x86_64", "amd64"]:
            url = (
                "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
            )
            arch_name = "amd64"
        elif arch in ["aarch64", "arm64"]:
            url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-aarch64-static.tar.xz"
            arch_name = "aarch64"
        else:
            logger.warning(
                f"Architecture {arch} not supported for FFmpeg auto-download"
            )
            logger.info(
                "Please install FFmpeg manually or place binary in bundled_ffmpeg/"
            )
            return BUNDLED_FFMPEG_DIR

        logger.info(f"Detected Linux architecture: {arch} → {arch_name}")

        with tempfile.TemporaryDirectory() as temp_dir:
            tar_path = Path(temp_dir) / "ffmpeg.tar.xz"

            logger.info(f"Downloading FFmpeg for {arch_name} from {url}...")
            try:
                urllib.request.urlretrieve(url, tar_path)
            except Exception as e:
                logger.error(f"Failed to download FFmpeg for {arch_name}: {e}")
                return BUNDLED_FFMPEG_DIR

            logger.info("Extracting...")
            import tarfile

            with tarfile.open(tar_path, "r:xz") as tar_ref:
                tar_ref.extractall(temp_dir)

            # Find ffmpeg binary
            for ffmpeg_file in Path(temp_dir).rglob("ffmpeg"):
                if ffmpeg_file.is_file() and ffmpeg_file.name == "ffmpeg":
                    target_path = BUNDLED_FFMPEG_DIR / "ffmpeg"
                    shutil.copy2(ffmpeg_file, target_path)
                    target_path.chmod(0o755)
                    logger.info(f"FFmpeg for {arch_name} downloaded: {target_path}")
                    return BUNDLED_FFMPEG_DIR

            logger.warning(f"FFmpeg for {arch_name} not found in archive")
            return BUNDLED_FFMPEG_DIR

    def create_spec_file(self) -> None:
        """Create PyInstaller spec file."""
        spec_path = PROJECT_ROOT / f"{APP_NAME}.spec"

        if spec_path.exists():
            logger.info("PyInstaller spec file already exists")
            return

        logger.info("Creating PyInstaller spec file...")

        spec_content = self._generate_spec_content()
        spec_path.write_text(spec_content)

        logger.info(f"PyInstaller spec file created: {spec_path}")

    def _generate_spec_content(self) -> str:
        """Generate PyInstaller spec file content."""
        return f"""# -*- mode: python ; coding: utf-8 -*-
# Auto-generated PyInstaller spec file for {APP_NAME}

import platform

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('bundled_ffmpeg', 'bundled_ffmpeg'),
    ],
    hiddenimports=[
        'flet.core',
        'flet.fastapi',
        'exifread',
        'PyPDF2',
        'pymediainfo',
        'piexif',
        'pillow_heif',
        'hachoir',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific build configurations
if platform.system() == "Linux":
    # Linux: Create directory with executable for packaging
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='{APP_NAME}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='{APP_NAME}'
    )
elif platform.system() == "Darwin":
    # macOS: Single executable and app bundle
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='{APP_NAME}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/icons/icon.icns',
    )
    
    # Create app bundle
    app = BUNDLE(
        exe,
        name='{APP_NAME}.app',
        icon='assets/icons/icon.icns',
        bundle_identifier='com.antgalanin.metadatacleaner',
        version='{APP_VERSION}',
        info_plist={{
            'CFBundleShortVersionString': '{APP_VERSION}',
            'CFBundleVersion': '{APP_VERSION}',
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'LSUIElement': False,
            'NSHighResolutionCapable': True,
            'CFBundleDocumentTypes': [
                {{
                    'CFBundleTypeName': 'Images',
                    'CFBundleTypeRole': 'Editor',
                    'LSItemContentTypes': ['public.image'],
                }},
                {{
                    'CFBundleTypeName': 'PDF Documents',
                    'CFBundleTypeRole': 'Editor',
                    'LSItemContentTypes': ['com.adobe.pdf'],
                }},
                {{
                    'CFBundleTypeName': 'Office Documents',
                    'CFBundleTypeRole': 'Editor',
                    'LSItemContentTypes': [
                        'org.openxmlformats.wordprocessingml.document',
                        'org.openxmlformats.presentationml.presentation',
                        'org.openxmlformats.spreadsheetml.sheet',
                    ],
                }},
            ],
        }},
    )
else:
    # Windows: Single executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='{APP_NAME}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/icons/icon.ico',
    )
"""

    def build_application(self) -> None:
        """Build the application with PyInstaller."""
        logger.info("Building application with PyInstaller...")

        # Clean previous builds
        for path in [DIST_DIR, PROJECT_ROOT / "build"]:
            if path.exists():
                shutil.rmtree(path)
                logger.debug(f"Cleaned: {path}")

        # Create spec file
        self.create_spec_file()

        # Build with PyInstaller
        spec_file = PROJECT_ROOT / f"{APP_NAME}.spec"
        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file)]

        if self.verbose:
            cmd.append("--log-level=DEBUG")
        else:
            cmd.append("--log-level=INFO")

        self.run_command(cmd, cwd=PROJECT_ROOT)

        # Verify build
        self._verify_build()

        logger.info("Application build completed successfully")

    def _verify_build(self) -> None:
        """Verify that the build was successful."""
        if self.system == "Darwin":
            app_path = DIST_DIR / f"{APP_NAME}.app"
            if not app_path.exists():
                raise BuildError(f"macOS app bundle not created: {app_path}")
            logger.info(f"macOS app bundle created: {app_path}")
        else:
            app_path = DIST_DIR / APP_NAME
            if not app_path.exists():
                raise BuildError(f"Application directory not created: {app_path}")

            # Check for executable
            exe_name = f"{APP_NAME}.exe" if self.system == "Windows" else APP_NAME
            exe_path = app_path / exe_name
            if not exe_path.exists():
                raise BuildError(f"Application executable not found: {exe_path}")

            logger.info(f"Application built successfully: {app_path}")

    def run_tests(self) -> None:
        """Run basic tests to verify the build."""
        logger.info("Running build verification tests...")

        # Test that the application can be imported
        try:
            # Add project root to path temporarily
            sys.path.insert(0, str(PROJECT_ROOT))
            import metadata_cleaner

            logger.info(f"Package import successful: {metadata_cleaner.__version__}")
        except ImportError as e:
            logger.warning(f"Package import failed: {e}")
        finally:
            if str(PROJECT_ROOT) in sys.path:
                sys.path.remove(str(PROJECT_ROOT))

        # Platform-specific executable tests
        if self.system == "Darwin":
            app_path = DIST_DIR / f"{APP_NAME}.app"
            exe_path = app_path / "Contents" / "MacOS" / APP_NAME
        else:
            app_path = DIST_DIR / APP_NAME
            exe_name = f"{APP_NAME}.exe" if self.system == "Windows" else APP_NAME
            exe_path = app_path / exe_name

        if exe_path.exists():
            # Test executable exists and has reasonable size
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            logger.info(f"Executable size: {size_mb:.1f} MB")

            if size_mb < 10:
                logger.warning("Executable seems unusually small")
            elif size_mb > 500:
                logger.warning("Executable seems unusually large")

        logger.info("Build verification completed")

    def build(self, skip_ffmpeg: bool = False) -> None:
        """Main build process."""
        logger.info(f"Starting build for {self.system} {self.machine}")

        # Check dependencies
        self.check_dependencies()

        # Create assets
        self.create_assets_folder()

        # Download FFmpeg
        if not skip_ffmpeg:
            self.download_ffmpeg()

        # Build application
        self.build_application()

        # Run tests
        self.run_tests()

        logger.info("Build process completed successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build script for Metadata Cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                    # Standard build
  python build.py --verbose          # Verbose output
  python build.py --skip-ffmpeg      # Skip FFmpeg download
  python build.py --clean            # Clean and build
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--skip-ffmpeg", action="store_true", help="Skip FFmpeg download"
    )

    parser.add_argument(
        "--clean", action="store_true", help="Clean previous builds first"
    )

    args = parser.parse_args()

    try:
        # Clean if requested
        if args.clean:
            logger.info("Cleaning previous builds...")
            for path in [DIST_DIR, PROJECT_ROOT / "build"]:
                if path.exists():
                    shutil.rmtree(path)
                    logger.info(f"Cleaned: {path}")

        # Create builder and run
        builder = PlatformBuilder(verbose=args.verbose)
        builder.build(skip_ffmpeg=args.skip_ffmpeg)

    except BuildError as e:
        logger.error(f"Build failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
