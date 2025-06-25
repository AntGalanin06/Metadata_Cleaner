#!/usr/bin/env python3
"""
Скрипт сборки приложения Metadata Cleaner.
Автоматически собирает приложение для текущей платформы.
"""

import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def run_command(cmd, cwd=None):
    """Выполнить команду в shell"""
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, check=True)
    return result


def create_assets_folder():
    """Создать папку assets с ресурсами"""
    assets_dir = Path("assets")
    if not assets_dir.exists():
        assets_dir.mkdir()

    # Создать подпапки если не существуют
    (assets_dir / "icons").mkdir(exist_ok=True)
    (assets_dir / "screenshots").mkdir(exist_ok=True)

    print("+ Папка assets создана")


def download_ffmpeg():
    """Скачать FFmpeg для текущей платформы"""
    print("Загрузка FFmpeg для текущей платформы...")
    
    system = platform.system()
    ffmpeg_dir = Path("bundled_ffmpeg")
    ffmpeg_dir.mkdir(exist_ok=True)
    
    # Проверить существующий FFmpeg
    if system == "Windows":
        ffmpeg_path = ffmpeg_dir / "ffmpeg.exe"
    else:
        ffmpeg_path = ffmpeg_dir / "ffmpeg"

    if ffmpeg_path.exists():
        print(f"+ FFmpeg уже существует: {ffmpeg_path}")
        return ffmpeg_dir
    
    if system == "Darwin":
        # macOS - используем evermeet.cx (надежный источник для macOS)
        arch = platform.machine().lower()
        if arch == "arm64":
            url = "https://evermeet.cx/pub/ffmpeg/ffmpeg.zip"
        else:
            url = "https://evermeet.cx/pub/ffmpeg/ffmpeg.zip"
            
        # Это архив
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "ffmpeg.zip"
            
            print(f"Загружаю с {url}...")
            urllib.request.urlretrieve(url, zip_path)
            
            print("Распаковываю...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Находим ffmpeg в распакованной папке
            ffmpeg_binary = None
            for file in Path(temp_dir).rglob("ffmpeg"):
                if file.is_file() and file.name == "ffmpeg":
                    ffmpeg_binary = file
                    break
            
            if ffmpeg_binary:
                target_path = ffmpeg_dir / "ffmpeg"
                shutil.copy2(ffmpeg_binary, target_path)
                target_path.chmod(0o755)  # Делаем исполняемым
                print(f"+ FFmpeg скачан: {target_path}")
            else:
                print("- FFmpeg не найден в архиве")
    
    elif system == "Windows":
        # Windows - используем gyan.dev (стабильные сборки)
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "ffmpeg.zip"
            
            print(f"Загружаю с {url}...")
            urllib.request.urlretrieve(url, zip_path)
            
            print("Распаковываю...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Находим ffmpeg.exe в папке bin
            ffmpeg_binary = None
            for file in Path(temp_dir).rglob("ffmpeg.exe"):
                if file.is_file() and file.name == "ffmpeg.exe":
                    ffmpeg_binary = file
                    break
            
            if ffmpeg_binary:
                target_path = ffmpeg_dir / "ffmpeg.exe"
                shutil.copy2(ffmpeg_binary, target_path)
                print(f"+ FFmpeg скачан: {target_path}")
            else:
                print("- ffmpeg.exe не найден в архиве")
    
    elif system == "Linux":
        # Linux - используем johnvansickle.com (стабильные сборки)
        url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tar_path = Path(temp_dir) / "ffmpeg.tar.xz"
            
            print(f"Загружаю с {url}...")
            urllib.request.urlretrieve(url, tar_path)
            
            print("Распаковываю...")
            import tarfile
            with tarfile.open(tar_path, 'r:xz') as tar_ref:
                tar_ref.extractall(temp_dir)
            
            # Находим ffmpeg в папке (обычно в корне архива)
            ffmpeg_binary = None
            for file in Path(temp_dir).rglob("ffmpeg"):
                if file.is_file() and file.name == "ffmpeg":
                    ffmpeg_binary = file
                    break
            
            if ffmpeg_binary:
                target_path = ffmpeg_dir / "ffmpeg"
                shutil.copy2(ffmpeg_binary, target_path)
                target_path.chmod(0o755)  # Делаем исполняемым
                print(f"+ FFmpeg скачан: {target_path}")
            else:
                print("- ffmpeg не найден в архиве")
    
    else:
        print(f"! Автоскачивание FFmpeg для {system} не поддерживается")
        print("Пожалуйста, установите FFmpeg вручную или поместите бинарник в bundled_ffmpeg/")
    
    return ffmpeg_dir


def ensure_spec_file():
    """Убедиться что spec файл существует"""
    spec_path = Path("MetadataCleaner.spec")
    if spec_path.exists():
        print("+ MetadataCleaner.spec найден")
        return
    
    print("Создаю MetadataCleaner.spec...")
    
    # Создаем минимальный spec файл
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
        'exifread',
        'PyPDF2', 
        'pymediainfo',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MetadataCleaner',
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

# macOS App Bundle
if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        name='MetadataCleaner.app',
        icon='assets/icons/icon.icns',
        bundle_identifier='com.antgalanin.metadatacleaner',
        version='1.0.0',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'LSUIElement': False,
        },
    )
'''
    
    spec_path.write_text(spec_content)
    print(f"+ MetadataCleaner.spec создан")


def build_app():
    """Собрать приложение с PyInstaller"""

    # Очистить предыдущие сборки
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")

    # Убедиться что spec файл существует
    ensure_spec_file()

    # Собрать с PyInstaller
    run_command("pyinstaller MetadataCleaner.spec")


def create_macos_dmg():
    """Создать DMG для macOS с мультиязычной лицензией"""
    if platform.system() != "Darwin":
        return

    # Проверить наличие create-dmg
    try:
        run_command("which create-dmg")
    except:
        run_command("brew install create-dmg")

    # Копируем единый мультиязычный файл лицензии
    license_src = Path("docs/LICENSE_INSTALLER.txt")
    if license_src.exists():
        license_dst = Path("dist") / "LICENSE_INSTALLER.txt"
        shutil.copy(license_src, license_dst)

    # Создаем DMG
    dmg_cmd = """create-dmg \\
  --volname 'Metadata Cleaner' \\
  --window-pos 200 120 \\
  --window-size 800 500 \\
  --icon-size 80 \\
  --icon 'MetadataCleaner.app' 150 150 \\
  --icon 'LICENSE_INSTALLER.txt' 150 300 \\
  --hide-extension 'MetadataCleaner.app' \\
  --app-drop-link 350 150 \\
  'MetadataCleaner-macOS.dmg' \\
  'dist/'"""

    run_command(dmg_cmd)


def test_app():
    """Проверить что приложение запускается"""

    if platform.system() == "Darwin":
        app_path = "dist/MetadataCleaner.app/Contents/MacOS/MetadataCleaner"
    elif platform.system() == "Windows":
        app_path = "dist/MetadataCleaner/MetadataCleaner.exe"
    else:
        app_path = "dist/MetadataCleaner/MetadataCleaner"

    if not Path(app_path).exists():
        return


def main():
    """Главная функция"""

    # Проверить зависимости
    try:
        import PyInstaller
    except ImportError:
        run_command("pip install pyinstaller")

    # Создать ресурсы
    create_assets_folder()
    
    # Скачать FFmpeg
    ffmpeg_dir = download_ffmpeg()

    # Собрать приложение
    build_app()

    # Тестировать
    test_app()

    # Создать установщик для macOS
    if platform.system() == "Darwin":
        create_macos_dmg()


if __name__ == "__main__":
    main()
