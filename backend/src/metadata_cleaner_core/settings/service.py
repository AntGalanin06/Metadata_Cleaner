"""Settings management service for the rewritten backend."""

from __future__ import annotations

import copy
import json
import os
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from metadata_cleaner_core.engine.models import OutputMode
from metadata_cleaner_core.engine.metadata_registry import MetadataRegistry


class SettingsService:
    """Persisted settings shared between CLI, API, and desktop shell."""

    def __init__(self) -> None:
        self._settings_file = self._get_settings_file_path()
        self._settings = self._load_default_settings()
        self._ensure_settings_directory()
        self.load_settings()
        self._apply_active_profile_settings()

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
        now = datetime.now(timezone.utc).isoformat()
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
            "logging": {
                "level": "info",
                "directory": "logs",
                "format": "jsonl",
            },
            "profiles": {
                "active_id": "default",
                "items": [
                    {
                        "id": "default",
                        "name": "Default",
                        "description": "System default cleaning profile",
                        "file_type_settings": self._get_default_file_type_settings(),
                        "created_at": now,
                        "updated_at": now,
                    }
                ],
            },
        }

    def load_settings(self) -> None:
        try:
            if self._settings_file.exists():
                with open(self._settings_file, encoding="utf-8") as file:
                    saved_settings = json.load(file)
                self._merge_settings(self._settings, saved_settings)
                self._apply_active_profile_settings()
        except (json.JSONDecodeError, OSError):
            # Ignore errors and continue with defaults.
            pass

    def _apply_active_profile_settings(self) -> None:
        active_profile = self.get_active_profile()
        if active_profile:
            self._settings["file_type_settings"] = copy.deepcopy(
                active_profile.get("file_type_settings", {})
            )

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
        profile_settings = (
            self.get_active_profile().get("file_type_settings", {})
            if self.get_active_profile()
            else {}
        )
        if profile_settings.get(file_type):
            return copy.deepcopy(profile_settings[file_type])
        return self._settings.get("file_type_settings", {}).get(file_type, {})

    def get_active_profile(self) -> dict[str, Any] | None:
        profiles_section = self._settings.get("profiles", {})
        active_id = profiles_section.get("active_id", "default")
        for profile in profiles_section.get("items", []):
            if profile.get("id") == active_id:
                return profile
        return None

    def set_active_profile(self, profile_id: str) -> dict[str, Any]:
        profiles_section = self._settings.setdefault(
            "profiles", copy.deepcopy(self._load_default_settings()["profiles"])
        )
        if any(profile["id"] == profile_id for profile in profiles_section.get("items", [])):
            profiles_section["active_id"] = profile_id
            self._settings["file_type_settings"] = copy.deepcopy(
                self.get_profile(profile_id)["file_type_settings"]
            )
            self.save_settings()
            return self.list_profiles()
        raise KeyError(profile_id)

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

    # Profile management -------------------------------------------------

    def list_profiles(self) -> dict[str, Any]:
        profiles = self._settings.setdefault("profiles", self._load_default_settings()["profiles"])
        return {
            "profiles": copy.deepcopy(profiles.get("items", [])),
            "active_id": profiles.get("active_id", "default"),
        }

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        for profile in self.list_profiles()["profiles"]:
            if profile["id"] == profile_id:
                return profile
        raise KeyError(profile_id)

    def create_profile(
        self,
        *,
        name: str,
        description: str | None,
        file_type_settings: dict[str, dict[str, bool]] | None = None,
    ) -> dict[str, Any]:
        profiles_section = self._settings.setdefault(
            "profiles", copy.deepcopy(self._load_default_settings()["profiles"])
        )
        profile_id = uuid.uuid4().hex
        sanitized_settings = self._sanitize_file_type_settings(file_type_settings)
        now = datetime.now(timezone.utc).isoformat()
        profile = {
            "id": profile_id,
            "name": name,
            "description": description,
            "file_type_settings": sanitized_settings,
            "created_at": now,
            "updated_at": now,
        }
        profiles_section.setdefault("items", []).append(profile)
        self.save_settings()
        return copy.deepcopy(profile)

    def update_profile(
        self,
        profile_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        file_type_settings: dict[str, dict[str, bool]] | None = None,
    ) -> dict[str, Any]:
        profiles_section = self._settings.setdefault(
            "profiles", copy.deepcopy(self._load_default_settings()["profiles"])
        )
        for profile in profiles_section.get("items", []):
            if profile["id"] == profile_id:
                if name is not None:
                    profile["name"] = name
                if description is not None:
                    profile["description"] = description
                if file_type_settings is not None:
                    profile["file_type_settings"] = self._sanitize_file_type_settings(
                        file_type_settings
                    )
                    if profiles_section.get("active_id") == profile_id:
                        self._settings["file_type_settings"] = copy.deepcopy(
                            profile["file_type_settings"]
                        )
                profile["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.save_settings()
                return copy.deepcopy(profile)
        raise KeyError(profile_id)

    def delete_profile(self, profile_id: str) -> dict[str, Any]:
        profiles_section = self._settings.setdefault(
            "profiles", copy.deepcopy(self._load_default_settings()["profiles"])
        )
        items = profiles_section.get("items", [])
        if profile_id == "default":
            raise ValueError("cannot delete default profile")
        for index, profile in enumerate(items):
            if profile["id"] == profile_id:
                removed = items.pop(index)
                if profiles_section.get("active_id") == profile_id:
                    fallback = next(
                        (item["id"] for item in items if item["id"] == "default"),
                        None,
                    )
                    if fallback is None and items:
                        fallback = items[0]["id"]
                    profiles_section["active_id"] = fallback or "default"
                    active_profile = self.get_active_profile()
                    if active_profile:
                        self._settings["file_type_settings"] = copy.deepcopy(
                            active_profile.get("file_type_settings", {})
                        )
                    else:
                        self._settings["file_type_settings"] = self._get_default_file_type_settings()
                self.save_settings()
                return copy.deepcopy(removed)
        raise KeyError(profile_id)

    def get_logging_level(self) -> str:
        logging_settings = self._settings.get("logging", {})
        return str(logging_settings.get("level", "info")).lower()

    def update_logging_level(self, level: str) -> None:
        logging_settings = self._settings.setdefault("logging", {})
        logging_settings["level"] = level.lower()
        self.save_settings()

    def get_logging_directory(self) -> Path:
        logging_settings = self._settings.setdefault("logging", {})
        directory = logging_settings.get("directory", "logs")
        path = Path(directory)
        if not path.is_absolute():
            path = self._settings_file.parent / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def update_logging_directory(self, directory: str) -> Path:
        logging_settings = self._settings.setdefault("logging", {})
        logging_settings["directory"] = directory
        resolved = self.get_logging_directory()
        self.save_settings()
        return resolved

    def _sanitize_file_type_settings(
        self, provided: dict[str, dict[str, bool]] | None
    ) -> dict[str, dict[str, bool]]:
        defaults = self._get_default_file_type_settings()
        if not provided:
            return defaults

        sanitized: dict[str, dict[str, bool]] = {}
        for file_type, default_settings in defaults.items():
            overrides = provided.get(file_type, {}) if provided else {}
            sanitized[file_type] = self._sanitize_metadata_flags(
                default_settings.items(), overrides
            )
        return sanitized

    def _sanitize_metadata_flags(
        self,
        default_items: Iterable[tuple[str, bool]],
        overrides: dict[str, bool],
    ) -> dict[str, bool]:
        sanitized: dict[str, bool] = {}
        for key, default_value in default_items:
            sanitized[key] = bool(overrides.get(key, default_value))
        return sanitized
