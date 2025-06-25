"""Сервис для управления настройками приложения."""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

from metadata_cleaner.cleaner.models import OutputMode


class SettingsService:
    """Сервис для управления настройками приложения"""

    def __init__(self):
        self._settings_file = self._get_settings_file_path()
        self._settings = self._load_default_settings()
        self._ensure_settings_directory()
        self.load_settings()

    def _get_settings_file_path(self) -> Path:
        """Получить путь к файлу настроек в зависимости от ОС"""
        system = platform.system()

        if system == "Darwin":  # macOS
            settings_dir = (
                Path.home() / "Library" / "Preferences" / "com.metadata-cleaner"
            )
            return settings_dir / "settings.json"
        elif system == "Windows":
            settings_dir = Path.home() / "AppData" / "Roaming" / "MetadataCleaner"
            return settings_dir / "settings.json"
        else:  # Linux и другие Unix-системы
            settings_dir = Path.home() / ".config" / "metadata-cleaner"
            return settings_dir / "settings.json"

    def _ensure_settings_directory(self):
        """Создать директорию для настроек если она не существует"""
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_default_settings(self) -> dict[str, Any]:
        """Загрузить настройки по умолчанию"""
        return {
            # Основные настройки
            "theme": "system",
            "language": "ru",
            "output_mode": "create_copy",
            # Настройки интерфейса
            "window_width": 1200,
            "window_height": 800,
            "window_maximized": False,
            # Настройки обработки
            "max_threads": 4,
            "show_detailed_logs": False,
            "auto_close_after_completion": False,
            "show_notifications": True,
            # Детальные настройки метаданных по типам файлов
            "file_type_settings": {
                "image": {
                    # EXIF данные
                    "exif_author": True,        # Автор фотографии
                    "exif_copyright": True,     # Авторские права
                    "exif_datetime": True,      # Дата и время съемки
                    "exif_camera": True,        # Модель камеры и настройки
                    "exif_software": True,      # ПО для обработки
                    # GPS данные
                    "gps_coords": True,         # GPS координаты
                    "gps_altitude": True,       # Высота над уровнем моря
                    # Персональные данные
                    "camera_owner": True,       # Владелец камеры
                    "camera_serial": True,      # Серийный номер камеры
                    "user_comments": True,      # Комментарии пользователя
                },
                "document": {
                    # Авторские данные
                    "author": True,             # Автор документа
                    "last_modified_by": True,   # Последний редактор
                    "company": True,            # Компания
                    # Временные данные
                    "created": True,            # Дата создания
                    "modified": True,           # Дата изменения
                    "last_printed": True,       # Дата последней печати
                    # Документооборот
                    "revision": True,           # Номер ревизии
                    "version": True,            # Версия документа
                    "content_status": True,     # Статус контента
                    "category": True,           # Категория
                    "language": True,           # Язык документа
                    "identifier": True,         # Уникальный идентификатор
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Заголовок
                    "subject": False,           # Тема
                    "keywords": False,          # Ключевые слова
                    "comments": False,          # Комментарии к содержанию
                },
                "pdf": {
                    # Авторские данные
                    "author": True,             # Автор PDF
                    "creator": True,            # Создатель (программа)
                    "producer": True,           # Производитель PDF
                    # Временные данные
                    "created": True,            # Дата создания
                    "modified": True,           # Дата изменения
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Заголовок документа
                    "subject": False,           # Тема документа
                    "keywords": False,          # Ключевые слова
                },
                "video": {
                    # Авторские данные
                    "author": True,             # Автор/создатель видео
                    "encoder": True,            # Энкодер/программа записи
                    # Временные данные
                    "creation_time": True,      # Дата и время создания
                    # GPS и локация
                    "gps_coords": True,         # GPS координаты
                    "location": True,           # Информация о местоположении
                    # Техническая информация
                    "major_brand": True,        # Основной бренд контейнера
                    "compatible_brands": True,  # Совместимые форматы
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Название видео
                    "comment": False,           # Комментарии/описание
                    "description": False,       # Подробное описание
                },
            },
            # Настройки резервного копирования
            "backup_settings": {
                "backup_location": "same_directory",  # 'same_directory' или путь
                "backup_suffix": "_backup",
                "max_backup_files": 5,
                "auto_cleanup_backups": True,
            },
            # Настройки безопасности
            "security_settings": {
                "secure_delete": False,  # Безопасное удаление временных файлов
                "verify_file_integrity": True,  # Проверка целостности после обработки
                "create_processing_log": True,  # Создавать лог обработки
            },
        }

    def load_settings(self):
        """Загрузить настройки из файла"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, encoding="utf-8") as f:
                    saved_settings = json.load(f)

                # Объединяем с настройками по умолчанию (для новых ключей)
                self._merge_settings(self._settings, saved_settings)

        except (json.JSONDecodeError, OSError):
            pass

    def _merge_settings(self, default: dict, saved: dict):
        """Рекурсивно объединить настройки, сохраняя новые ключи из default"""
        for key, value in saved.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value

    def save_settings(self):
        """Сохранить настройки в файл"""
        try:
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # Геттеры для основных настроек
    def get_theme(self) -> str:
        return self._settings.get("theme", "system")

    def get_theme_mode(self):
        """Получить объект ThemeMode для Flet"""
        import flet as ft

        theme = self.get_theme()
        if theme == "light":
            return ft.ThemeMode.LIGHT
        elif theme == "dark":
            return ft.ThemeMode.DARK
        else:
            return ft.ThemeMode.SYSTEM

    def get_language(self) -> str:
        return self._settings.get("language", "ru")

    def get_output_mode(self) -> OutputMode:
        mode_str = self._settings.get("output_mode", "create_copy")

        # Преобразуем старые и новые значения в правильные enum значения
        if mode_str in ["overwrite", "replace"]:
            return OutputMode.REPLACE
        elif mode_str == "create_copy":
            return OutputMode.CREATE_COPY
        elif mode_str == "backup_and_overwrite":
            return OutputMode.BACKUP_AND_OVERWRITE
        else:
            return OutputMode.CREATE_COPY  # По умолчанию

    def get_max_threads(self) -> int:
        return self._settings.get("max_threads", 4)

    def get_show_notifications(self) -> bool:
        return self._settings.get("show_notifications", True)

    # Геттеры для настроек метаданных
    def get_file_type_settings(self, file_type: str) -> dict[str, bool]:
        """Получить настройки метаданных для типа файла"""
        return self._settings.get("file_type_settings", {}).get(file_type, {})

    def should_remove_metadata(self, file_type: str, metadata_type: str) -> bool:
        """Проверить, нужно ли удалять определенный тип метаданных"""
        file_settings = self.get_file_type_settings(file_type)
        return file_settings.get(metadata_type, True)

    def get_metadata_to_clean(self, file_type: str) -> dict[str, bool]:
        """Получить настройки очистки метаданных для типа файла"""
        return self.get_file_type_settings(file_type)

    # Геттеры для настроек окна
    def get_window_size(self) -> tuple[int, int]:
        width = self._settings.get("window_width", 1200)
        height = self._settings.get("window_height", 800)
        return width, height

    def get_window_maximized(self) -> bool:
        return self._settings.get("window_maximized", False)

    # Сеттеры для основных настроек
    def update_theme(self, theme: str):
        """Обновить тему"""
        self._settings["theme"] = theme
        self.save_settings()

    def set_theme(self, theme: str):
        """Установить тему (алиас для update_theme)"""
        self.update_theme(theme)

    def update_language(self, language: str):
        self._settings["language"] = language
        self.save_settings()

    def update_output_mode(self, mode: OutputMode):
        self._settings["output_mode"] = mode.value
        self.save_settings()

    def update_max_threads(self, threads: int):
        self._settings["max_threads"] = max(1, min(16, threads))
        self.save_settings()

    # Сеттеры для настроек метаданных
    def update_file_type_settings(self, file_type: str, settings: dict[str, bool]):
        """Обновить настройки метаданных для типа файла"""
        if "file_type_settings" not in self._settings:
            self._settings["file_type_settings"] = {}

        self._settings["file_type_settings"][file_type] = settings
        self.save_settings()

    def update_metadata_setting(
        self, file_type: str, metadata_type: str, enabled: bool
    ):
        """Обновить настройку конкретного типа метаданных"""
        if "file_type_settings" not in self._settings:
            self._settings["file_type_settings"] = {}

        if file_type not in self._settings["file_type_settings"]:
            self._settings["file_type_settings"][file_type] = {}

        self._settings["file_type_settings"][file_type][metadata_type] = enabled
        self.save_settings()

    # Сеттеры для настроек окна
    def update_window_size(self, width: int, height: int):
        self._settings["window_width"] = width
        self._settings["window_height"] = height
        self.save_settings()

    def update_window_maximized(self, maximized: bool):
        self._settings["window_maximized"] = maximized
        self.save_settings()

    # Массовое обновление настроек
    def update_settings(self, new_settings: dict[str, Any]):
        """Массовое обновление настроек"""
        # Обновляем простые значения напрямую
        for key in ["theme", "language", "output_mode"]:
            if key in new_settings:
                self._settings[key] = new_settings[key]

        # Для вложенных настроек используем слияние
        if "file_type_settings" in new_settings:
            if "file_type_settings" not in self._settings:
                self._settings["file_type_settings"] = {}
            self._merge_settings(
                self._settings["file_type_settings"], new_settings["file_type_settings"]
            )

        self.save_settings()

    def get_all_settings(self) -> dict[str, Any]:
        """Получить все настройки"""
        return self._settings.copy()

    def reset_to_defaults(self):
        """Сбросить все настройки к значениям по умолчанию"""
        self._settings = self._load_default_settings()
        self.save_settings()

    def export_settings(self, file_path: Path):
        """Экспортировать настройки в файл"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except OSError as e:
            msg = f"Ошибка экспорта настроек: {e}"
            raise Exception(msg)

    def import_settings(self, file_path: Path):
        """Импортировать настройки из файла"""
        try:
            with open(file_path, encoding="utf-8") as f:
                imported_settings = json.load(f)

            # Проверяем и объединяем с текущими настройками
            self._merge_settings(self._settings, imported_settings)
            self.save_settings()

        except (json.JSONDecodeError, OSError) as e:
            msg = f"Ошибка импорта настроек: {e}"
            raise Exception(msg)

    def get_settings_file_path(self) -> Path:
        """Получить путь к файлу настроек"""
        return self._settings_file
