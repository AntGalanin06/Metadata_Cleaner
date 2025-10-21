"""Settings management service for the rewritten backend."""

from __future__ import annotations

import copy
import json
import os
import platform
from pathlib import Path
from typing import Any

from metadata_cleaner_core.engine.models import OutputMode
from metadata_cleaner_core.engine.metadata_registry import MetadataRegistry


class SettingsService:
    """Persisted settings shared between CLI, API, and desktop shell."""

    def __init__(self) -> None:
        self._settings_file = self._get_settings_file_path()
        self._settings = self._load_default_settings()
        self._ensure_settings_directory()
        self.load_settings()

    def _get_settings_file_path(self) -> Path:
        """Return the system-specific settings path."""
        override_dir = os.environ.get("METADATA_CLEANER_CONFIG_DIR")
        if override_dir:
            return Path(override_dir).expanduser() / "settings.json"

        system = platform.system()

        if system == "Darwin":
            settings_dir = (
                Path.home() / "Library" / "Preferences" / "com.metadata-cleaner"
            )
        elif system == "Windows":
            settings_dir = Path.home() / "AppData" / "Roaming" / "MetadataCleaner"
        else:
            settings_dir = Path.home() / ".config" / "metadata-cleaner"

        return settings_dir / "settings.json"

    def _ensure_settings_directory(self) -> None:
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_default_file_type_settings(self) -> dict[str, dict[str, bool]]:
        settings: dict[str, dict[str, bool]] = {}
        for file_type in MetadataRegistry.get_supported_file_types():
            settings[file_type] = MetadataRegistry.get_default_settings_for_file_type(
                file_type
            )
        return settings

    def _load_default_settings(self) -> dict[str, Any]:
        return {
            "theme": "system",
            "language": "en",
            "output_mode": "create_copy",
            "window_width": 1200,
            "window_height": 800,
            "window_maximized": False,
            "auto_close_after_completion": False,
            "show_notifications": True,
            "file_type_settings": self._get_default_file_type_settings(),
            "backup_settings": {
                "backup_location": "same_directory",
                "backup_suffix": "_backup",
                "max_backup_files": 5,
                "auto_cleanup_backups": True,
            },
            "security_settings": {
                "secure_delete": False,
                "verify_file_integrity": True,
                "create_processing_log": True,
            },
        }

    def load_settings(self) -> None:
        try:
            if self._settings_file.exists():
                with open(self._settings_file, encoding="utf-8") as file:
                    saved_settings = json.load(file)
                self._merge_settings(self._settings, saved_settings)
        except (json.JSONDecodeError, OSError):
            # Ignore errors and continue with defaults.
            pass

    def _merge_settings(self, default: dict, saved: dict) -> None:
        for key, value in saved.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value

    def save_settings(self) -> None:
        try:
            with open(self._settings_file, "w", encoding="utf-8") as file:
                json.dump(self._settings, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # General getters
    def get_theme(self) -> str:
        return self._settings.get("theme", "system")

    def get_language(self) -> str:
        return self._settings.get("language", "en")

    def get_output_mode(self) -> OutputMode:
        mode_str = self._settings.get("output_mode", "create_copy")

        if mode_str in {"overwrite", "replace"}:
            return OutputMode.REPLACE
        if mode_str == "create_copy":
            return OutputMode.CREATE_COPY
        if mode_str == "backup_and_overwrite":
            return OutputMode.BACKUP_AND_OVERWRITE
        return OutputMode.CREATE_COPY

    def get_show_notifications(self) -> bool:
        return self._settings.get("show_notifications", True)

    def get_auto_close_after_completion(self) -> bool:
        return self._settings.get("auto_close_after_completion", False)

    def get_file_type_settings(self, file_type: str) -> dict[str, bool]:
        return self._settings.get("file_type_settings", {}).get(file_type, {})

    def should_remove_metadata(self, file_type: str, metadata_type: str) -> bool:
        file_settings = self.get_file_type_settings(file_type)
        return file_settings.get(metadata_type, True)

    def get_metadata_to_clean(self, file_type: str) -> dict[str, bool]:
        return self.get_file_type_settings(file_type)

    def get_window_size(self) -> tuple[int, int]:
        width = self._settings.get("window_width", 1200)
        height = self._settings.get("window_height", 800)
        return width, height

    def get_window_maximized(self) -> bool:
        return self._settings.get("window_maximized", False)

    # Setters
    def update_theme(self, theme: str) -> None:
        self._settings["theme"] = theme
        self.save_settings()

    def update_language(self, language: str) -> None:
        self._settings["language"] = language
        self.save_settings()

    def update_output_mode(self, mode: OutputMode) -> None:
        self._settings["output_mode"] = mode.value
        self.save_settings()

    def get_all_settings(self) -> dict[str, Any]:
        """Return a deep copy of all settings."""
        return copy.deepcopy(self._settings)

    def update_settings(self, data: dict[str, Any]) -> None:
        """Merge provided settings into current configuration."""
        self._merge_settings(self._settings, data)
        self.save_settings()

    def get_settings_schema(self) -> dict[str, Any]:
        """Вернуть схему настроек по умолчанию для фронтенда."""
        defaults = self._load_default_settings()
        return {
            "defaults": defaults,
            "file_type_defaults": copy.deepcopy(defaults["file_type_settings"]),
            "theme_options": ["system", "light", "dark"],
            "language_options": ["en", "ru"],
            "output_modes": [mode.value for mode in OutputMode],
        }
