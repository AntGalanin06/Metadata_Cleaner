"""Конфигурация pytest и общие фикстуры для тестов."""

import pytest
import tempfile
import shutil
import time
import logging
from pathlib import Path
from unittest.mock import Mock
from typing import Generator, Dict, Any

from metadata_cleaner.services.settings_service import SettingsService
from metadata_cleaner.cleaner.models import OutputMode
from metadata_cleaner.cleaner.dispatcher import MetadataDispatcher


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Создает временную директорию для тестов."""
    max_cleanup_attempts = 3
    cleanup_retry_delay = 0.1

    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        # Очистка временной директории с обработкой заблокированных файлов
        for attempt in range(max_cleanup_attempts):
            try:
                shutil.rmtree(temp_path)
                break
            except (PermissionError, OSError):
                if attempt < max_cleanup_attempts - 1:
                    time.sleep(cleanup_retry_delay)
                    continue


@pytest.fixture
def test_files_dir() -> Path:
    """Путь к директории с тестовыми файлами."""
    return Path(__file__).parent / "test_files"


@pytest.fixture
def mock_settings() -> Mock:
    """Создает мок настроек приложения."""
    settings = Mock(spec=SettingsService)
    settings.get_output_mode.return_value = OutputMode.CREATE_COPY
    settings.get_metadata_to_clean.return_value = {
        "author": True,
        "gps_coords": True,
        "exif_camera": True,
        "created": True,
        "modified": True,
        "title": False,
        "subject": False,
        "keywords": False,
        "comments": False,
    }
    # settings.get_ffmpeg_path.return_value = None  # Removed - method doesn't exist
    settings.get_language.return_value = "en"
    settings.get_theme.return_value = "auto"
    settings.get_theme_mode.return_value = "system"
    settings.get_window_size.return_value = (1200, 800)
    settings.get_window_maximized.return_value = False
    settings.get_show_notifications.return_value = True
    settings.get_auto_close_after_completion.return_value = False
    settings.get_file_type_settings.return_value = {"exif_author": True}
    return settings


@pytest.fixture
def dispatcher(mock_settings: Mock) -> MetadataDispatcher:
    """Создает экземпляр диспетчера с мок настройками."""
    return MetadataDispatcher(mock_settings)


@pytest.fixture
def sample_files(test_files_dir: Path, temp_dir: Path) -> Dict[str, Path]:
    """Копирует образцы файлов во временную директорию."""
    files = {}

    # Определяем файлы для копирования
    file_mapping = {
        "image_jpg": "test_image.jpg",
        "image_jpeg": "test_image.jpeg",
        "image_png": "test_image.png",
        "image_gif": "test_image.gif",
        "document_docx": "test_document.docx",
        "document_xlsx": "test_spreadsheet.xlsx",
        "document_pptx": "test_presentation.pptx",
        "pdf": "test_document.pdf",
        "video_mp4": "test_video.mp4",
        "video_mov": "test_video.mov",
    }

    for key, filename in file_mapping.items():
        source = test_files_dir / filename
        if source.exists():
            dest = temp_dir / filename
            shutil.copy2(source, dest)
            files[key] = dest

    return files


@pytest.fixture
def test_metadata() -> Dict[str, Any]:
    """Тестовые метаданные для проверки."""
    return {
        "author": "Test Author",
        "creator": "Test Creator",
        "title": "Test Title",
        "subject": "Test Subject",
        "keywords": "test, metadata, cleaner",
        "comments": "Test comments",
        "created": "2023-01-01T10:00:00",
        "modified": "2023-01-02T15:30:00",
        "gps": {"latitude": 55.7558, "longitude": 37.6176, "altitude": 156},
        "camera": {
            "make": "Test Camera",
            "model": "Test Model",
            "software": "Test Software",
        },
    }


@pytest.fixture
def non_existent_file(temp_dir: Path) -> Path:
    """Путь к несуществующему файлу."""
    return temp_dir / "non_existent.jpg"


@pytest.fixture
def unsupported_file(temp_dir: Path) -> Path:
    """Создает неподдерживаемый тестовый файл."""
    unsupported = temp_dir / "test.txt"
    unsupported.write_text("This is a test text file", encoding="utf-8")
    return unsupported


@pytest.fixture(autouse=True)
def cleanup_logs():
    """Автоматическая очистка логов после тестов."""
    yield
    # Очистка логгеров если необходимо
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


# Маркеры для группировки тестов
def pytest_configure(config):
    """Конфигурация pytest с пользовательскими маркерами."""
    config.addinivalue_line("markers", "unit: Модульные тесты отдельных компонентов")
    config.addinivalue_line("markers", "integration: Интеграционные тесты компонентов")
    config.addinivalue_line("markers", "slow: Медленные тесты (обработка файлов)")
    config.addinivalue_line(
        "markers", "requires_files: Тесты, требующие тестовые файлы"
    )
    config.addinivalue_line("markers", "video: Тесты видео (требуют ffmpeg)")


# Пропуск тестов при отсутствии тестовых файлов
def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов."""
    test_files_dir = Path(__file__).parent / "test_files"

    for item in items:
        # Помечаем тесты, требующие файлы
        if "requires_files" in item.keywords:
            if not test_files_dir.exists():
                item.add_marker(pytest.mark.skip(reason="Тестовые файлы не найдены"))

        # Помечаем медленные тесты
        if "slow" in item.keywords:
            if not config.getoption("--runslow"):
                item.add_marker(
                    pytest.mark.skip(
                        reason="Используйте --runslow для запуска медленных тестов"
                    )
                )


def pytest_addoption(parser):
    """Добавляет опции командной строки для pytest."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="Запуск медленных тестов"
    )
    parser.addoption(
        "--runvideo",
        action="store_true",
        default=False,
        help="Запуск тестов видео (требует ffmpeg)",
    )
