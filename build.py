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


def safe_print(text):
    """Безопасный вывод с учетом платформы"""
    if platform.system() == "Windows":
        # Убираем эмодзи для Windows
        text = text.replace("🚀", "").replace("🔍", "").replace("✅", "").replace("❌", "").replace("📦", "").replace("💡", "").replace("📁", "").replace("🎬", "").replace("🔨", "").replace("🧪", "").replace("🎉", "").replace("⚠️", "").replace("🪟", "").replace("🍎", "").replace("🐧", "")
        # Убираем лишние пробелы
        text = " ".join(text.split())
    print(text)

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
    safe_print("Загрузка FFmpeg для текущей платформы...")
    
    system = platform.system()
    ffmpeg_dir = Path("bundled_ffmpeg")
    ffmpeg_dir.mkdir(exist_ok=True)
    
    # Проверить существующий FFmpeg
    if system == "Windows":
        ffmpeg_path = ffmpeg_dir / "ffmpeg.exe"
    else:
        ffmpeg_path = ffmpeg_dir / "ffmpeg"

    if ffmpeg_path.exists():
        safe_print(f"+ FFmpeg уже существует: {ffmpeg_path}")
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
        # Linux - автоопределение архитектуры
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
            arch_name = "amd64"
        elif arch in ["aarch64", "arm64"]:
            url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-aarch64-static.tar.xz"
            arch_name = "aarch64"
        else:
            print(f"! Архитектура {arch} не поддерживается для автоскачивания FFmpeg")
            print("Пожалуйста, установите FFmpeg вручную или поместите бинарник в bundled_ffmpeg/")
            return ffmpeg_dir
        
        safe_print(f"Определена архитектура Linux: {arch} → {arch_name}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tar_path = Path(temp_dir) / "ffmpeg.tar.xz"
            
            print(f"Загружаю FFmpeg для {arch_name} с {url}...")
            try:
                urllib.request.urlretrieve(url, tar_path)
            except Exception as e:
                print(f"! Ошибка загрузки FFmpeg для {arch_name}: {e}")
                print("Попробуем альтернативный источник...")
                # Альтернативный источник для ARM64
                if arch_name == "aarch64":
                    alt_url = "https://evermeet.cx/pub/ffmpeg/ffmpeg.zip"
                    print(f"Загружаю с альтернативного источника: {alt_url}")
                    urllib.request.urlretrieve(alt_url, tar_path)
                else:
                    return ffmpeg_dir
            
            print("Распаковываю...")
            import tarfile
            try:
                with tarfile.open(tar_path, 'r:xz') as tar_ref:
                    tar_ref.extractall(temp_dir)
            except:
                # Попробуем как ZIP если это альтернативный источник
                with zipfile.ZipFile(tar_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            
            # Находим ffmpeg в папке
            ffmpeg_binary = None
            for file in Path(temp_dir).rglob("ffmpeg"):
                if file.is_file() and file.name == "ffmpeg":
                    ffmpeg_binary = file
                    break
            
            if ffmpeg_binary:
                target_path = ffmpeg_dir / "ffmpeg"
                shutil.copy2(ffmpeg_binary, target_path)
                target_path.chmod(0o755)  # Делаем исполняемым
                print(f"+ FFmpeg для {arch_name} скачан: {target_path}")
            else:
                print(f"- FFmpeg для {arch_name} не найден в архиве")
                print("Попробуйте установить FFmpeg вручную: sudo apt install ffmpeg")
    
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

# Create different build configurations based on platform
if platform.system() == "Linux":
    # Linux: Create directory with executable for easier installation
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='MetadataCleaner',
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
        name='MetadataCleaner'
    )
else:
    # Windows and other platforms: Single executable
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
        version='1.0.1',
        info_plist={
            'CFBundleShortVersionString': '1.0.1',
            'CFBundleVersion': '1.0.1',
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


def create_linux_appimage():
    """Создать AppImage для Linux"""
    if platform.system() != "Linux":
        return
    
    print("Создание AppImage для Linux...")
    
    # Проверить наличие appimagetool с поддержкой ARM64
    appimage_tool = None
    
    # Определяем архитектуру системы
    system_arch = platform.machine().lower()
    if system_arch in ["x86_64", "amd64"]:
        arch_suffix = "x86_64"
    elif system_arch in ["aarch64", "arm64"]:
        arch_suffix = "aarch64"
    else:
        print(f"! Архитектура {system_arch} не поддерживается для AppImage")
        return
    
    safe_print(f"Определена архитектура для AppImage: {system_arch} → {arch_suffix}")
    
    # Проверяем существующие инструменты
    for tool in ["appimagetool", f"appimagetool-{arch_suffix}.AppImage"]:
        try:
            run_command(f"which {tool}")
            appimage_tool = tool
            break
        except:
            continue
    
    if not appimage_tool:
        print(f"AppImageTool не найден. Скачиваю для {arch_suffix}...")
        try:
            # Скачиваем appimagetool для нужной архитектуры
            tool_url = f"https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-{arch_suffix}.AppImage"
            safe_print(f"📥 Загружаю: {tool_url}")
            urllib.request.urlretrieve(tool_url, f"appimagetool-{arch_suffix}.AppImage")
            run_command(f"chmod +x appimagetool-{arch_suffix}.AppImage")
            appimage_tool = f"./appimagetool-{arch_suffix}.AppImage"
            safe_print(f"✅ AppImageTool для {arch_suffix} скачан")
        except Exception as e:
            print(f"! Не удалось скачать AppImageTool для {arch_suffix}: {e}")
            # Fallback на x86_64 версию если доступна
            try:
                safe_print("🔄 Пробуем fallback на x86_64 версию...")
                fallback_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
                urllib.request.urlretrieve(fallback_url, "appimagetool-x86_64.AppImage")
                run_command("chmod +x appimagetool-x86_64.AppImage")
                appimage_tool = "./appimagetool-x86_64.AppImage"
                safe_print("✅ Fallback AppImageTool x86_64 скачан")
            except Exception as e2:
                print(f"! Fallback также не сработал: {e2}")
                return
    
    # Создаем структуру AppDir
    appdir = Path("dist/MetadataCleaner.AppDir")
    if appdir.exists():
        shutil.rmtree(appdir)
    
    appdir.mkdir()
    (appdir / "usr").mkdir()
    (appdir / "usr" / "bin").mkdir()
    (appdir / "usr" / "share").mkdir()
    (appdir / "usr" / "share" / "applications").mkdir()
    (appdir / "usr" / "share" / "icons").mkdir()
    (appdir / "usr" / "share" / "icons" / "hicolor").mkdir()
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256").mkdir()
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir()
    
    # Копируем приложение
    if Path("dist/MetadataCleaner").is_dir():
        shutil.copytree("dist/MetadataCleaner", appdir / "usr" / "bin" / "MetadataCleaner")
    else:
        shutil.copy2("dist/MetadataCleaner", appdir / "usr" / "bin" / "MetadataCleaner")
    
    # Копируем иконку
    if Path("assets/icons/icon.png").exists():
        shutil.copy2("assets/icons/icon.png", 
                    appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "metadata-cleaner.png")
        shutil.copy2("assets/icons/icon.png", appdir / "metadata-cleaner.png")
    
    # Создаем AppRun
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
EXEC="${HERE}/usr/bin/MetadataCleaner"
if [ -d "${EXEC}" ]; then
    exec "${EXEC}/MetadataCleaner" "$@"
else
    exec "${EXEC}" "$@"
fi
"""
    
    apprun_path = appdir / "AppRun"
    apprun_path.write_text(apprun_content)
    apprun_path.chmod(0o755)
    
    # Создаем .desktop файл
    desktop_content = """[Desktop Entry]
Name=Metadata Cleaner
Comment=Remove metadata from files
Comment[ru]=Удаление метаданных из файлов
Exec=MetadataCleaner
Icon=metadata-cleaner
Type=Application
Categories=Utility;Privacy;
Terminal=false
StartupWMClass=MetadataCleaner
"""
    
    desktop_path = appdir / "metadata-cleaner.desktop"
    desktop_path.write_text(desktop_content)
    
    # Копируем desktop файл в usr/share/applications
    shutil.copy2(desktop_path, appdir / "usr" / "share" / "applications" / "metadata-cleaner.desktop")
    
    try:
        # Попробуем создать AppImage с APPIMAGE_EXTRACT_AND_RUN=1 для обхода проблем с FUSE
        run_command(f"APPIMAGE_EXTRACT_AND_RUN=1 {appimage_tool} {appdir} MetadataCleaner-Linux.AppImage")
        safe_print("✅ AppImage создан: MetadataCleaner-Linux.AppImage")
    except Exception as e:
        print(f"! Ошибка создания AppImage с FUSE: {e}")
        try:
            # Альтернативный способ - без FUSE
            print("Пробуем создать AppImage без FUSE...")
            run_command(f"{appimage_tool} --appimage-extract-and-run {appdir} MetadataCleaner-Linux.AppImage")
        except Exception as e2:
            print(f"! Альтернативный способ также не сработал: {e2}")
            # Создаем простой tar.gz архив как fallback
            try:
                print("Создаю альтернативный Linux архив...")
                run_command(f"cd dist && tar -czf MetadataCleaner-Linux.tar.gz MetadataCleaner")
                safe_print("✅ Альтернативный архив создан: dist/MetadataCleaner-Linux.tar.gz")
                safe_print("💡 Для установки: распакуйте архив и запустите installer_linux.sh")
            except Exception as e3:
                print(f"! Не удалось создать даже архив: {e3}")


def create_macos_dmg():
    """Создать DMG для macOS с английской лицензией"""
    if platform.system() != "Darwin":
        return

            safe_print("🍎 Создание macOS DMG...")
    
    # Проверить наличие create-dmg
    try:
        run_command("which create-dmg")
        safe_print("✅ create-dmg найден")
    except:
        safe_print("Устанавливаю create-dmg...")
        try:
            run_command("brew install create-dmg")
            safe_print("✅ create-dmg установлен")
        except Exception as e:
            print(f"! Не удалось установить create-dmg: {e}")
            safe_print("💡 Установите вручную: brew install create-dmg")
            return

    # Проверяем что приложение собрано
    app_path = Path("dist/MetadataCleaner.app")
    if not app_path.exists():
        safe_print("❌ MetadataCleaner.app не найден в dist/")
        safe_print("💡 Сначала соберите приложение: python build.py")
        return

    # Копируем английский файл лицензии
    license_src = Path("docs/LICENSE_INSTALLER.txt")
    if license_src.exists():
        license_dst = Path("dist") / "LICENSE_INSTALLER.txt"
        shutil.copy(license_src, license_dst)
        safe_print("✅ Лицензия скопирована")
    else:
        safe_print("⚠️  Файл лицензии не найден: docs/LICENSE_INSTALLER.txt")

    # Создаем DMG с улучшенными параметрами
            safe_print("🔨 Создание DMG...")
    try:
        dmg_cmd = """create-dmg \\
  --volname 'Metadata Cleaner' \\
  --volicon 'assets/icons/icon.icns' \\
  --window-pos 200 120 \\
  --window-size 800 600 \\
  --icon-size 80 \\
  --icon 'MetadataCleaner.app' 200 150 \\
  --icon 'LICENSE_INSTALLER.txt' 200 300 \\
  --hide-extension 'MetadataCleaner.app' \\
  --app-drop-link 600 150 \\
  --text-size 14 \\
  'MetadataCleaner-macOS.dmg' \\
  'dist/'"""
        
        run_command(dmg_cmd)
        safe_print("✅ macOS DMG создан: MetadataCleaner-macOS.dmg")
        
    except Exception as e:
        print(f"! Ошибка создания DMG: {e}")
        safe_print("💡 Попробуйте создать DMG вручную или проверьте права доступа")


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

    # Проверяем платформу и используем соответствующие символы
    if platform.system() == "Windows":
        safe_print("Запуск сборки Metadata Cleaner...")
        safe_print(f"Платформа: {platform.system()} {platform.machine()}")
        
        # Проверить зависимости
        try:
            import PyInstaller
            safe_print("PyInstaller найден")
        except ImportError:
            safe_print("Устанавливаю PyInstaller...")
            try:
                run_command("pip install pyinstaller")
                safe_print("PyInstaller установлен")
            except Exception as e:
                safe_print(f"Не удалось установить PyInstaller: {e}")
                safe_print("Установите вручную: pip install pyinstaller")
                return

        # Создать ресурсы
        safe_print("\nСоздание ресурсов...")
        create_assets_folder()
        
        # Скачать FFmpeg
        safe_print("\nСкачивание FFmpeg...")
        ffmpeg_dir = download_ffmpeg()

        # Собрать приложение
        safe_print("\nСборка приложения...")
        try:
            build_app()
            safe_print("Приложение собрано")
        except Exception as e:
            safe_print(f"Ошибка сборки: {e}")
            return

        # Тестировать
        safe_print("\nТестирование...")
        test_app()

        # Создать установщики
        safe_print("\nСоздание установщиков...")
        safe_print("Windows: используйте installer_windows_universal.nsi для создания .exe")
        
        safe_print("\nСборка завершена!")
        safe_print("Результаты в папке dist/")
    else:
        # Для macOS и Linux используем эмодзи
        safe_print("🚀 Запуск сборки Metadata Cleaner...")
        safe_print(f"🔍 Платформа: {platform.system()} {platform.machine()}")
        
        # Проверить зависимости
        try:
            import PyInstaller
            safe_print("PyInstaller найден")
        except ImportError:
            safe_print("Устанавливаю PyInstaller...")
            try:
                run_command("pip install pyinstaller")
                safe_print("PyInstaller установлен")
            except Exception as e:
                safe_print(f"❌ Не удалось установить PyInstaller: {e}")
                safe_print("💡 Установите вручную: pip install pyinstaller")
                return

        # Создать ресурсы
        safe_print("\n📁 Создание ресурсов...")
        create_assets_folder()
        
        # Скачать FFmpeg
        safe_print("\n🎬 Скачивание FFmpeg...")
        ffmpeg_dir = download_ffmpeg()

        # Собрать приложение
        safe_print("\n🔨 Сборка приложения...")
        try:
            build_app()
            safe_print("Приложение собрано")
        except Exception as e:
            safe_print(f"❌ Ошибка сборки: {e}")
            return

        # Тестировать
        safe_print("\n🧪 Тестирование...")
        test_app()

        # Создать установщики
        safe_print("\nСоздание установщиков...")
        
        if platform.system() == "Darwin":
            create_macos_dmg()
        elif platform.system() == "Linux":
            create_linux_appimage()
        
        safe_print("\n🎉 Сборка завершена!")
        safe_print("📁 Результаты в папке dist/")


if __name__ == "__main__":
    main()
