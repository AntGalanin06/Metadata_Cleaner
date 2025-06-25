"""Модели данных для обработки файлов."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class CleanStatus(Enum):
    """Статус очистки файла."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class FileType(Enum):
    """Типы поддерживаемых файлов."""

    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    VIDEO = "video"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


class OutputMode(Enum):
    """Режим вывода файлов."""

    REPLACE = "replace"
    CREATE_COPY = "create_copy"
    BACKUP_AND_OVERWRITE = "backup_and_overwrite"


@dataclass
class FileTypeMetadata:
    """Метаданные для конкретного типа файла."""

    file_type: FileType
    supported_fields: set[str]
    default_clean_fields: dict[str, bool]
    description: str = ""

    @classmethod
    def get_image_metadata(cls) -> FileTypeMetadata:
        return cls(
            file_type=FileType.IMAGE,
            supported_fields={
                "exif_author",
                "exif_artist",
                "exif_copyright",
                "exif_datetime",
                "exif_datetime_original",
                "exif_datetime_digitized",
                "exif_software",
                "exif_camera_make",
                "exif_camera_model",
                "exif_lens_model",
                "gps_latitude",
                "gps_longitude",
                "gps_altitude",
                "gps_timestamp",
                "iptc_byline",
                "iptc_caption",
                "iptc_keywords",
                "iptc_title",
                "iptc_copyright",
                "iptc_city",
                "iptc_country",
                "xmp_creator",
                "xmp_title",
                "xmp_description",
                "xmp_subject",
                "xmp_rights",
                "xmp_create_date",
                "xmp_modify_date",
            },
            default_clean_fields={
                "exif_author": True,
                "exif_artist": True,
                "exif_copyright": False,
                "exif_datetime": True,
                "exif_datetime_original": True,
                "exif_camera_make": True,
                "exif_camera_model": True,
                "gps_latitude": True,
                "gps_longitude": True,
                "gps_altitude": True,
                "iptc_byline": True,
                "iptc_caption": False,
                "iptc_keywords": False,
                "xmp_creator": True,
                "xmp_create_date": True,
            },
            description="Изображения (JPEG, PNG, TIFF, RAW)",
        )

    @classmethod
    def get_document_metadata(cls) -> FileTypeMetadata:
        return cls(
            file_type=FileType.DOCUMENT,
            supported_fields={
                "core_creator",
                "core_last_modified_by",
                "core_created",
                "core_modified",
                "core_title",
                "core_subject",
                "core_description",
                "core_keywords",
                "core_category",
                "core_comments",
                "app_application",
                "app_app_version",
                "app_company",
                "custom_properties",
                "revision_number",
                "total_editing_time",
            },
            default_clean_fields={
                "core_creator": True,
                "core_last_modified_by": True,
                "core_created": True,
                "core_modified": True,
                "core_title": False,
                "core_subject": False,
                "core_comments": True,
                "app_application": True,
                "app_company": True,
                "revision_number": True,
            },
            description="Документы Word (DOCX, DOC)",
        )

    @classmethod
    def get_pdf_metadata(cls) -> FileTypeMetadata:
        return cls(
            file_type=FileType.PDF,
            supported_fields={
                "title",
                "author",
                "subject",
                "keywords",
                "creator",
                "producer",
                "creation_date",
                "modification_date",
                "trapped",
                "custom_properties",
            },
            default_clean_fields={
                "author": True,
                "creator": True,
                "producer": True,
                "creation_date": True,
                "modification_date": True,
                "title": False,
                "subject": False,
                "keywords": False,
            },
            description="PDF документы",
        )

    @classmethod
    def get_video_metadata(cls) -> FileTypeMetadata:
        return cls(
            file_type=FileType.VIDEO,
            supported_fields={
                "title",
                "author", 
                "comment",
                "description",
                "creation_time",
                "location",
                "gps_coords",
                "encoder",
                "major_brand",
                "compatible_brands",
            },
            default_clean_fields={
                "author": True,
                "creation_time": True,
                "comment": True,
                "gps_coords": True,
                "title": False,
                "description": False,
            },
            description="Видеофайлы (MP4, MOV)",
        )

    @classmethod
    def get_spreadsheet_metadata(cls) -> FileTypeMetadata:
        return cls(
            file_type=FileType.SPREADSHEET,
            supported_fields={
                "core_creator",
                "core_last_modified_by",
                "core_created",
                "core_modified",
                "core_title",
                "core_subject",
                "core_description",
                "core_keywords",
                "core_category",
                "core_comments",
                "app_application",
                "app_app_version",
                "app_company",
                "custom_properties",
                "revision_number",
                "calculation_properties",
            },
            default_clean_fields={
                "core_creator": True,
                "core_last_modified_by": True,
                "core_created": True,
                "core_modified": True,
                "core_title": False,
                "core_subject": False,
                "core_comments": True,
                "app_application": True,
                "app_company": True,
                "revision_number": True,
            },
            description="Электронные таблицы (XLSX, XLS)",
        )


@dataclass
class AppSettings:
    """Настройки приложения."""

    output_mode: OutputMode = OutputMode.CREATE_COPY
    file_type_settings: dict[FileType, dict[str, bool]] = field(default_factory=dict)
    theme: str = "system"
    language: str = "ru"

    def __post_init__(self):
        if not self.file_type_settings:
            self.file_type_settings = {
                FileType.IMAGE: FileTypeMetadata.get_image_metadata().default_clean_fields,
                FileType.DOCUMENT: FileTypeMetadata.get_document_metadata().default_clean_fields,
                FileType.PDF: FileTypeMetadata.get_pdf_metadata().default_clean_fields,
            }


@dataclass
class CleaningOptions:
    """Опции очистки метаданных."""

    clean_author: bool = True
    clean_created_date: bool = True
    clean_modified_date: bool = True
    clean_comments: bool = True
    clean_gps_data: bool = True
    clean_camera_info: bool = True
    clean_title: bool = False
    clean_subject: bool = False
    clean_keywords: bool = False
    create_backup: bool = True


@dataclass
class FileJob:
    """Задача на очистку файла."""

    file_path: Path
    file_type: FileType = FileType.UNKNOWN
    output_path: Path | None = None
    backup_enabled: bool = True
    clean_fields: dict[str, bool] | None = None

    def __post_init__(self):
        if self.clean_fields is None:
            self.clean_fields = {
                "creator": True,
                "author": True,
                "title": False,
                "subject": False,
                "keywords": False,
                "comments": True,
                "created": True,
                "modified": True,
                "revision": True,
                "gps": True,
                "camera": True,
            }


@dataclass
class CleanResult:
    """Результат очистки файла."""

    job: FileJob
    status: CleanStatus
    message: str = ""
    cleaned_fields: dict[str, Any] | None = None
    error: Exception | None = None
    processing_time: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.status == CleanStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        return self.status == CleanStatus.ERROR
