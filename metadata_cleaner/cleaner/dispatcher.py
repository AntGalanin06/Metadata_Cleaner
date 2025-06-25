"""Диспетчер для определения типа файла и передачи соответствующему обработчику."""

from __future__ import annotations

import mimetypes
import time
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import FileAccessError, UnsupportedFileTypeError
from .handlers.image import ImageHandler
from .handlers.office import OfficeHandler
from .handlers.pdf import PDFHandler
from .handlers.video import VideoHandler
from .models import (
    CleaningOptions,
    CleanResult,
    CleanStatus,
    FileJob,
    FileType,
    OutputMode,
)

if TYPE_CHECKING:
    from metadata_cleaner.services.settings_service import SettingsService


class MetadataDispatcher:
    """Диспетчер для маршрутизации файлов к соответствующим обработчикам."""

    def __init__(self, settings_service: SettingsService):
        self.settings_service = settings_service
        self.handlers = {
            FileType.IMAGE: ImageHandler(),
            FileType.DOCUMENT: OfficeHandler(),
            FileType.PDF: PDFHandler(),
            FileType.VIDEO: VideoHandler(),
        }

    def get_file_type(self, path: Path) -> FileType | None:
        """Определяет тип файла на основе его расширения."""
        ext = path.suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif"]:
            return FileType.IMAGE
        elif ext in [".docx", ".xlsx", ".pptx"]:
            return FileType.DOCUMENT
        elif ext == ".pdf":
            return FileType.PDF
        elif ext in [".mp4", ".mov"]:
            return FileType.VIDEO
        return None

    def process_file(self, path: Path) -> CleanResult:
        """Обрабатывает один файл."""
        file_type = self.get_file_type(path)

        if not file_type:
            return CleanResult(
                job=FileJob(file_path=path),
                status=CleanStatus.ERROR,
                message=f"Unsupported file type: {path.suffix}",
            )

        handler = self.handlers.get(file_type)
        if not handler:
            return CleanResult(
                job=FileJob(file_path=path),
                status=CleanStatus.ERROR,
                message=f"No handler for file type: {file_type}",
            )

        # Определяем путь для сохранения файла
        output_mode = self.settings_service.get_output_mode()
        output_path = None
        backup_enabled = False

        if output_mode == OutputMode.CREATE_COPY:
            output_path = path.with_name(f"{path.stem}_cleaned{path.suffix}")
        elif output_mode == OutputMode.BACKUP_AND_OVERWRITE:
            backup_enabled = True

        file_job = FileJob(
            file_path=path,
            file_type=file_type,
            output_path=output_path,
            backup_enabled=backup_enabled,
            clean_fields=self.settings_service.get_metadata_to_clean(file_type.value),
        )
        return handler.clean(file_job)

    def get_handler_for_file(self, file_path: Path) -> type | None:
        """Получить обработчик для файла на основе расширения."""
        file_type = self.get_file_type(file_path)
        if file_type:
            handler = self.handlers.get(file_type)
            return type(handler) if handler else None
        return None

    def is_supported(self, file_path: Path | str) -> bool:
        """Проверить, поддерживается ли тип файла."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return self.get_handler_for_file(file_path) is not None

    def get_supported_extensions(self) -> set[str]:
        """Получить список поддерживаемых расширений."""
        extensions = set()
        # Добавляем расширения для каждого типа файла
        extensions.update([".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif"])  # IMAGE
        extensions.update([".docx", ".xlsx", ".pptx"])  # DOCUMENT
        extensions.add(".pdf")  # PDF
        extensions.update([".mp4", ".mov"])  # VIDEO
        return extensions

    def _options_to_clean_fields(self, options: CleaningOptions) -> dict[str, bool]:
        """Конвертация CleaningOptions в clean_fields."""
        return {
            "author": options.clean_author,
            "creator": options.clean_author,
            "title": options.clean_title,
            "subject": options.clean_subject,
            "keywords": options.clean_keywords,
            "comments": options.clean_comments,
            "created": options.clean_created_date,
            "modified": options.clean_modified_date,
            "revision": True,
            "gps": options.clean_gps_data,
            "camera": options.clean_camera_info,
        }

    def process_file_with_options(
        self, file_path: str | Path, options: CleaningOptions
    ) -> CleanResult:
        """Обработать файл с использованием CleaningOptions."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        job = FileJob(
            file_path=file_path,
            backup_enabled=options.create_backup,
            clean_fields=self._options_to_clean_fields(options),
        )

        return self.process_file(job.file_path)

    def get_file_info(self, file_path: str | Path) -> dict[str, str]:
        """Получить информацию о файле."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        info = {
            "name": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": str(file_path.stat().st_size) if file_path.exists() else "0",
            "supported": str(self.is_supported(file_path)),
        }

        # Определение MIME-типа
        mime_type, _ = mimetypes.guess_type(str(file_path))
        info["mime_type"] = mime_type or "unknown"

        return info

    def process_file_with_settings(
        self, path: Path, file_type: FileType
    ) -> CleanResult:
        """Обработать файл с использованием настроек из SettingsService."""
        start_time = time.time()

        # Инициализируем file_job заранее
        file_job = FileJob(
            file_path=path,
            file_type=file_type,
            output_path=None,
            backup_enabled=self.settings_service.get_output_mode()
            == OutputMode.BACKUP_AND_OVERWRITE,
            clean_fields=self.settings_service.get_metadata_to_clean(file_type.value),
        )

        try:
            # Проверка доступности файла
            if not path.exists():
                msg = f"Файл не найден: {path}"
                raise FileAccessError(msg)

            if not path.is_file():
                msg = f"Не является файлом: {path}"
                raise FileAccessError(msg)

            # Получение обработчика
            handler = self.handlers.get(file_type)
            if handler is None:
                msg = f"Неподдерживаемый тип файла: {file_type}"
                raise UnsupportedFileTypeError(msg)

            # Выполнение обработки
            result = handler.clean(file_job)

            # Обновление времени обработки
            result.processing_time = time.time() - start_time

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            return CleanResult(
                job=file_job,
                status=CleanStatus.ERROR,
                message=str(e),
                error=e,
                processing_time=processing_time,
            )
