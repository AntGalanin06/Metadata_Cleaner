"""Регистр метаданных и единая система соответствия между frontend и backend."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MetadataCategory(Enum):
    """Категории метаданных."""

    AUTHOR = "author"  # Авторские данные
    DATETIME = "datetime"  # Временные данные
    LOCATION = "location"  # Геолокация
    CAMERA = "camera"  # Данные камеры/устройства
    TECHNICAL = "technical"  # Техническая информация
    CONTENT = "content"  # Контентные метаданные


@dataclass
class MetadataField:
    """Описание поля метаданных."""

    # Уникальный ключ для настроек
    key: str
    # Категория метаданных
    category: MetadataCategory
    # Ключи перевода
    name_key: str
    description_key: str
    # Поля в результатах обработки (что возвращают handlers)
    result_fields: list[str]
    # По умолчанию удалять или нет
    default_remove: bool = True
    # Приоритет для сортировки (меньше = выше)
    priority: int = 100


class MetadataRegistry:
    """Регистр метаданных для всех типов файлов."""

    # Метаданные для изображений
    IMAGE_FIELDS = [
        # Авторские данные
        MetadataField(
            key="exif_author",
            category=MetadataCategory.AUTHOR,
            name_key="exif_author",
            description_key="exif_author_desc",
            result_fields=[
                "artist",
                "author",
                "camera_owner",
                "png_author",
                "png_Author",
                "gif_author",
            ],
            default_remove=True,
            priority=10,
        ),
        MetadataField(
            key="exif_copyright",
            category=MetadataCategory.AUTHOR,
            name_key="exif_copyright",
            description_key="exif_copyright_desc",
            result_fields=[
                "copyright",
                "png_Copyright",
                "png_copyright",
                "heic_copyright",
            ],
            default_remove=False,
            priority=11,
        ),
        # Временные данные
        MetadataField(
            key="exif_datetime",
            category=MetadataCategory.DATETIME,
            name_key="exif_datetime",
            description_key="exif_datetime_desc",
            result_fields=[
                "date_original",
                "date_digitized",
                "png_Creation Time",
                "heic_creation_time",
            ],
            default_remove=True,
            priority=20,
        ),
        # Данные камеры
        MetadataField(
            key="exif_camera",
            category=MetadataCategory.CAMERA,
            name_key="exif_camera",
            description_key="exif_camera_desc",
            result_fields=["camera_make", "camera_model"],
            default_remove=True,
            priority=30,
        ),
        MetadataField(
            key="exif_software",
            category=MetadataCategory.CAMERA,
            name_key="exif_software",
            description_key="exif_software_desc",
            result_fields=["software", "png_Software", "heic_software"],
            default_remove=True,
            priority=31,
        ),
        MetadataField(
            key="camera_serial",
            category=MetadataCategory.CAMERA,
            name_key="camera_serial",
            description_key="camera_serial_desc",
            result_fields=["body_serial", "lens_serial"],
            default_remove=True,
            priority=32,
        ),
        # GPS данные
        MetadataField(
            key="gps_coords",
            category=MetadataCategory.LOCATION,
            name_key="gps_coords",
            description_key="gps_coords_desc",
            result_fields=["gps_data"],
            default_remove=True,
            priority=40,
        ),
        # Комментарии пользователя
        MetadataField(
            key="user_comments",
            category=MetadataCategory.CONTENT,
            name_key="user_comments",
            description_key="user_comments_desc",
            result_fields=["user_comment", "png_Comment", "gif_comment"],
            default_remove=True,
            priority=50,
        ),
        # Заголовки и описания (PNG и другие форматы)
        MetadataField(
            key="title_metadata",
            category=MetadataCategory.CONTENT,
            name_key="title_metadata",
            description_key="title_metadata_desc",
            result_fields=["png_title", "png_Title", "gif_title", "title"],
            default_remove=False,
            priority=45,
        ),
        # Техническая информация специфичная для форматов
        MetadataField(
            key="format_version",
            category=MetadataCategory.TECHNICAL,
            name_key="format_version",
            description_key="format_version_desc",
            result_fields=["png_version", "gif_version"],
            default_remove=True,
            priority=60,
        ),
        # Информация о преобразовании формата
        MetadataField(
            key="format_conversion",
            category=MetadataCategory.TECHNICAL,
            name_key="format_conversion",
            description_key="format_conversion_desc",
            result_fields=["format_changed"],
            default_remove=False,
            priority=61,
        ),
        # HEIC специфичные поля
        MetadataField(
            key="heic_metadata",
            category=MetadataCategory.TECHNICAL,
            name_key="heic_metadata",
            description_key="heic_metadata_desc",
            result_fields=["heic_title", "heic_author", "heic_description"],
            default_remove=True,
            priority=62,
        ),
        # Описания и дополнительный контент
        MetadataField(
            key="description_metadata",
            category=MetadataCategory.CONTENT,
            name_key="description_metadata",
            description_key="description_metadata_desc",
            result_fields=["png_Description", "heic_description"],
            default_remove=False,
            priority=46,
        ),
        # Источники и атрибуция
        MetadataField(
            key="source_metadata",
            category=MetadataCategory.CONTENT,
            name_key="source_metadata",
            description_key="source_metadata_desc",
            result_fields=["png_Source"],
            default_remove=False,
            priority=47,
        ),
        # Предупреждения и дисклеймеры
        MetadataField(
            key="disclaimer_metadata",
            category=MetadataCategory.CONTENT,
            name_key="disclaimer_metadata",
            description_key="disclaimer_metadata_desc",
            result_fields=["png_Disclaimer", "png_Warning"],
            default_remove=False,
            priority=48,
        ),
        # Текстовые данные формата
        MetadataField(
            key="textual_metadata",
            category=MetadataCategory.TECHNICAL,
            name_key="textual_metadata",
            description_key="textual_metadata_desc",
            result_fields=["png_Textual", "gif_application", "gif_transparency"],
            default_remove=True,
            priority=63,
        ),
    ]

    # Метаданные для документов (DOCX, PPTX)
    DOCUMENT_FIELDS = [
        # Авторские данные
        MetadataField(
            key="author",
            category=MetadataCategory.AUTHOR,
            name_key="author",
            description_key="author_desc",
            result_fields=["author", "creator"],
            default_remove=True,
            priority=10,
        ),
        MetadataField(
            key="last_modified_by",
            category=MetadataCategory.AUTHOR,
            name_key="last_modified_by",
            description_key="last_modified_by_desc",
            result_fields=["last_modified_by", "last_modified_by_alt"],
            default_remove=True,
            priority=11,
        ),
        MetadataField(
            key="company",
            category=MetadataCategory.AUTHOR,
            name_key="company",
            description_key="company_desc",
            result_fields=["company"],
            default_remove=True,
            priority=12,
        ),
        # Временные данные
        MetadataField(
            key="created",
            category=MetadataCategory.DATETIME,
            name_key="created",
            description_key="created_desc",
            result_fields=["created"],
            default_remove=True,
            priority=20,
        ),
        MetadataField(
            key="modified",
            category=MetadataCategory.DATETIME,
            name_key="modified",
            description_key="modified_desc",
            result_fields=["modified"],
            default_remove=True,
            priority=21,
        ),
        MetadataField(
            key="last_printed",
            category=MetadataCategory.DATETIME,
            name_key="last_printed",
            description_key="last_printed_desc",
            result_fields=["last_printed"],
            default_remove=True,
            priority=22,
        ),
        # Технические данные
        MetadataField(
            key="revision",
            category=MetadataCategory.TECHNICAL,
            name_key="revision",
            description_key="revision_desc",
            result_fields=["revision"],
            default_remove=True,
            priority=30,
        ),
        MetadataField(
            key="version",
            category=MetadataCategory.TECHNICAL,
            name_key="version",
            description_key="version_desc",
            result_fields=["version"],
            default_remove=True,
            priority=31,
        ),
        MetadataField(
            key="content_status",
            category=MetadataCategory.TECHNICAL,
            name_key="content_status",
            description_key="content_status_desc",
            result_fields=["content_status"],
            default_remove=True,
            priority=32,
        ),
        MetadataField(
            key="category",
            category=MetadataCategory.TECHNICAL,
            name_key="category",
            description_key="category_desc",
            result_fields=["category"],
            default_remove=True,
            priority=33,
        ),
        MetadataField(
            key="language",
            category=MetadataCategory.TECHNICAL,
            name_key="language",
            description_key="language_desc",
            result_fields=["language"],
            default_remove=True,
            priority=34,
        ),
        MetadataField(
            key="identifier",
            category=MetadataCategory.TECHNICAL,
            name_key="identifier",
            description_key="identifier_desc",
            result_fields=["identifier"],
            default_remove=True,
            priority=35,
        ),
        # Контентные данные (по умолчанию НЕ удаляем)
        MetadataField(
            key="title",
            category=MetadataCategory.CONTENT,
            name_key="title",
            description_key="title_desc",
            result_fields=["title"],
            default_remove=False,
            priority=50,
        ),
        MetadataField(
            key="subject",
            category=MetadataCategory.CONTENT,
            name_key="subject",
            description_key="subject_desc",
            result_fields=["subject"],
            default_remove=False,
            priority=51,
        ),
        MetadataField(
            key="keywords",
            category=MetadataCategory.CONTENT,
            name_key="keywords",
            description_key="keywords_desc",
            result_fields=["keywords"],
            default_remove=False,
            priority=52,
        ),
        MetadataField(
            key="comments",
            category=MetadataCategory.CONTENT,
            name_key="comments",
            description_key="comments_desc",
            result_fields=["comments"],
            default_remove=False,
            priority=53,
        ),
    ]

    # Метаданные для PDF
    PDF_FIELDS = [
        # Авторские данные
        MetadataField(
            key="author",
            category=MetadataCategory.AUTHOR,
            name_key="author",
            description_key="author_desc",
            result_fields=["author"],
            default_remove=True,
            priority=10,
        ),
        MetadataField(
            key="creator",
            category=MetadataCategory.AUTHOR,
            name_key="creator",
            description_key="creator_desc",
            result_fields=["creator"],
            default_remove=True,
            priority=11,
        ),
        MetadataField(
            key="producer",
            category=MetadataCategory.AUTHOR,
            name_key="producer",
            description_key="producer_desc",
            result_fields=["producer"],
            default_remove=True,
            priority=12,
        ),
        # Временные данные
        MetadataField(
            key="created",
            category=MetadataCategory.DATETIME,
            name_key="created",
            description_key="created_desc",
            result_fields=["created"],
            default_remove=True,
            priority=20,
        ),
        MetadataField(
            key="modified",
            category=MetadataCategory.DATETIME,
            name_key="modified",
            description_key="modified_desc",
            result_fields=["modified"],
            default_remove=True,
            priority=21,
        ),
        # Контентные данные (по умолчанию НЕ удаляем)
        MetadataField(
            key="title",
            category=MetadataCategory.CONTENT,
            name_key="title",
            description_key="title_desc",
            result_fields=["title"],
            default_remove=False,
            priority=50,
        ),
        MetadataField(
            key="subject",
            category=MetadataCategory.CONTENT,
            name_key="subject",
            description_key="subject_desc",
            result_fields=["subject"],
            default_remove=False,
            priority=51,
        ),
        MetadataField(
            key="keywords",
            category=MetadataCategory.CONTENT,
            name_key="keywords",
            description_key="keywords_desc",
            result_fields=["keywords"],
            default_remove=False,
            priority=52,
        ),
    ]

    # Метаданные для видео
    VIDEO_FIELDS = [
        # Авторские данные
        MetadataField(
            key="author",
            category=MetadataCategory.AUTHOR,
            name_key="author",
            description_key="author_desc",
            result_fields=["author_info"],
            default_remove=True,
            priority=10,
        ),
        MetadataField(
            key="encoder",
            category=MetadataCategory.TECHNICAL,
            name_key="encoder",
            description_key="encoder_desc",
            result_fields=["author_info"],  # В handlers это часто в author_info
            default_remove=True,
            priority=30,
        ),
        # Временные данные
        MetadataField(
            key="creation_time",
            category=MetadataCategory.DATETIME,
            name_key="creation_time",
            description_key="creation_time_desc",
            result_fields=["creation_info"],
            default_remove=True,
            priority=20,
        ),
        # Геолокация
        MetadataField(
            key="gps_coords",
            category=MetadataCategory.LOCATION,
            name_key="gps_coords",
            description_key="gps_coords_desc",
            result_fields=["gps_info"],
            default_remove=True,
            priority=40,
        ),
        MetadataField(
            key="location",
            category=MetadataCategory.LOCATION,
            name_key="location",
            description_key="location_desc",
            result_fields=["gps_info"],
            default_remove=True,
            priority=41,
        ),
        # Техническая информация
        MetadataField(
            key="major_brand",
            category=MetadataCategory.TECHNICAL,
            name_key="major_brand",
            description_key="major_brand_desc",
            result_fields=["method"],  # Общая техническая информация
            default_remove=True,
            priority=31,
        ),
        MetadataField(
            key="compatible_brands",
            category=MetadataCategory.TECHNICAL,
            name_key="compatible_brands",
            description_key="compatible_brands_desc",
            result_fields=["method"],
            default_remove=True,
            priority=32,
        ),
        # Контентные данные (по умолчанию НЕ удаляем)
        MetadataField(
            key="title",
            category=MetadataCategory.CONTENT,
            name_key="title",
            description_key="title_desc",
            result_fields=["title_info"],
            default_remove=False,
            priority=50,
        ),
        MetadataField(
            key="comment",
            category=MetadataCategory.CONTENT,
            name_key="comment",
            description_key="comment_desc",
            result_fields=["comment_info"],
            default_remove=False,
            priority=51,
        ),
        MetadataField(
            key="description",
            category=MetadataCategory.CONTENT,
            name_key="description",
            description_key="description_desc",
            result_fields=["comment_info"],
            default_remove=False,
            priority=52,
        ),
        # Предупреждения и системная информация
        MetadataField(
            key="processing_warning",
            category=MetadataCategory.TECHNICAL,
            name_key="processing_warning",
            description_key="processing_warning_desc",
            result_fields=["warning"],
            default_remove=False,
            priority=60,
        ),
    ]

    @classmethod
    def get_fields_for_file_type(cls, file_type: str) -> list[MetadataField]:
        """Получить поля метаданных для типа файла."""
        mapping = {
            "image": cls.IMAGE_FIELDS,
            "document": cls.DOCUMENT_FIELDS,
            "pdf": cls.PDF_FIELDS,
            "video": cls.VIDEO_FIELDS,
        }
        return mapping.get(file_type, [])

    @classmethod
    def get_default_settings_for_file_type(cls, file_type: str) -> dict[str, bool]:
        """Получить настройки по умолчанию для типа файла."""
        fields = cls.get_fields_for_file_type(file_type)
        return {field.key: field.default_remove for field in fields}

    @classmethod
    def get_field_by_key(cls, file_type: str, key: str) -> MetadataField | None:
        """Найти поле метаданных по ключу."""
        fields = cls.get_fields_for_file_type(file_type)
        for field in fields:
            if field.key == key:
                return field
        return None

    @classmethod
    def map_result_fields_to_metadata(
        cls, file_type: str, result_fields: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Сопоставить поля результата с метаданными настроек."""
        mapping = {}
        fields = cls.get_fields_for_file_type(file_type)

        for field in fields:
            found_fields = []
            for result_field in field.result_fields:
                if result_field in result_fields:
                    found_fields.append(result_field)

            if found_fields:
                mapping[field.key] = found_fields

        return mapping

    @classmethod
    def get_supported_file_types(cls) -> list[str]:
        """Получить список поддерживаемых типов файлов."""
        return ["image", "document", "pdf", "video"]

    @classmethod
    def get_all_result_fields_for_file_type(cls, file_type: str) -> set[str]:
        """Получить все возможные поля результата для типа файла."""
        fields = cls.get_fields_for_file_type(file_type)
        result_fields = set()
        for field in fields:
            result_fields.update(field.result_fields)
        return result_fields
