"""Обработчик для Office документов (docx, pptx, xlsx)."""

from typing import Any

from docx import Document as DocxDocument
from openpyxl import load_workbook
from pptx import Presentation

from metadata_cleaner.cleaner.errors import BackupError, MetadataProcessingError
from metadata_cleaner.cleaner.models import CleanResult, CleanStatus, FileJob

from . import BaseHandler


class OfficeHandler(BaseHandler):
    """Обработчик для Office документов."""

    def clean(self, job: FileJob) -> CleanResult:
        """Очистка метаданных из офисных документов."""
        try:
            # Создание бэкапа
            if not self._create_backup(job):
                msg = "Не удалось создать резервную копию"
                raise BackupError(msg)

            cleaned_fields = {}
            extension = job.file_path.suffix.lower()

            if extension == ".docx":
                cleaned_fields = self._clean_docx(job)
            elif extension == ".pptx":
                cleaned_fields = self._clean_pptx(job)
            elif extension == ".xlsx":
                cleaned_fields = self._clean_xlsx(job)
            else:
                msg = f"Неизвестный Office формат: {extension}"
                raise MetadataProcessingError(msg)

            return CleanResult(
                job=job,
                status=CleanStatus.SUCCESS,
                message=f"Метаданные успешно очищены из {job.file_path.name}",
                cleaned_fields=cleaned_fields,
            )

        except Exception as e:
            return CleanResult(
                job=job,
                status=CleanStatus.ERROR,
                message=f"Ошибка при обработке {job.file_path.name}: {e!s}",
                error=e,
            )

    def _clean_docx(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из DOCX файла."""
        doc = DocxDocument(str(job.file_path))
        cleaned_fields = {}

        # Доступ к core properties
        props = doc.core_properties

        if job.clean_fields.get("author", True) and props.author:
            cleaned_fields["author"] = props.author
            props.author = ""

        if job.clean_fields.get("creator", True):
            if hasattr(props, "creator") and props.creator:
                cleaned_fields["creator"] = props.creator
                props.creator = ""

        if job.clean_fields.get("title", False) and props.title:
            cleaned_fields["title"] = props.title
            props.title = ""

        if job.clean_fields.get("subject", False) and props.subject:
            cleaned_fields["subject"] = props.subject
            props.subject = ""

        if job.clean_fields.get("keywords", False) and props.keywords:
            cleaned_fields["keywords"] = props.keywords
            props.keywords = ""

        if job.clean_fields.get("comments", True) and props.comments:
            cleaned_fields["comments"] = props.comments
            props.comments = ""

        if job.clean_fields.get("created", True) and props.created:
            cleaned_fields["created"] = str(props.created)
            # Для дат просто сохраняем информацию, но не изменяем

        if job.clean_fields.get("modified", True) and props.modified:
            cleaned_fields["modified"] = str(props.modified)
            # Для дат просто сохраняем информацию, но не изменяем

        if job.clean_fields.get("revision", True) and props.revision:
            cleaned_fields["revision"] = props.revision
            props.revision = 1  # Сбрасываем на 1

        # Дополнительные метаданные
        if props.last_modified_by:
            cleaned_fields["last_modified_by"] = props.last_modified_by
            props.last_modified_by = ""

        if props.category:
            cleaned_fields["category"] = props.category
            props.category = ""

        if props.content_status:
            cleaned_fields["content_status"] = props.content_status
            props.content_status = ""

        if props.identifier:
            cleaned_fields["identifier"] = props.identifier
            props.identifier = ""

        if props.language:
            cleaned_fields["language"] = props.language
            props.language = ""

        if props.version:
            cleaned_fields["version"] = props.version
            props.version = ""

        if props.last_printed:
            cleaned_fields["last_printed"] = str(props.last_printed)
            # last_printed нельзя очистить напрямую

        # Сохранение изменений
        output_path = job.output_path or job.file_path
        doc.save(str(output_path))

        return cleaned_fields

    def _clean_pptx(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из PPTX файла."""
        prs = Presentation(str(job.file_path))
        cleaned_fields = {}

        # Доступ к core properties
        props = prs.core_properties

        if job.clean_fields.get("author", True) and props.author:
            cleaned_fields["author"] = props.author
            props.author = ""

        if job.clean_fields.get("title", False) and props.title:
            cleaned_fields["title"] = props.title
            props.title = ""

        if job.clean_fields.get("subject", False) and props.subject:
            cleaned_fields["subject"] = props.subject
            props.subject = ""

        if job.clean_fields.get("keywords", False) and props.keywords:
            cleaned_fields["keywords"] = props.keywords
            props.keywords = ""

        if job.clean_fields.get("comments", True) and props.comments:
            cleaned_fields["comments"] = props.comments
            props.comments = ""

        if job.clean_fields.get("created", True) and props.created:
            cleaned_fields["created"] = str(props.created)
            # Для дат просто сохраняем информацию, но не изменяем

        if job.clean_fields.get("modified", True) and props.modified:
            cleaned_fields["modified"] = str(props.modified)
            # Для дат просто сохраняем информацию, но не изменяем

        if job.clean_fields.get("revision", True):
            if hasattr(props, "revision") and props.revision:
                cleaned_fields["revision"] = props.revision
                props.revision = 1  # Сбрасываем на 1

        # Дополнительные метаданные
        if props.last_modified_by:
            cleaned_fields["last_modified_by"] = props.last_modified_by
            props.last_modified_by = ""

        if props.category:
            cleaned_fields["category"] = props.category
            props.category = ""

        if props.content_status:
            cleaned_fields["content_status"] = props.content_status
            props.content_status = ""

        if props.identifier:
            cleaned_fields["identifier"] = props.identifier
            props.identifier = ""

        if props.language:
            cleaned_fields["language"] = props.language
            props.language = ""

        if props.version:
            cleaned_fields["version"] = props.version
            props.version = ""

        if props.last_printed:
            cleaned_fields["last_printed"] = str(props.last_printed)
            # last_printed нельзя очистить напрямую

        # Сохранение изменений
        output_path = job.output_path or job.file_path
        prs.save(str(output_path))

        return cleaned_fields

    def _clean_xlsx(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из XLSX файла."""
        wb = load_workbook(str(job.file_path))
        cleaned_fields = {}

        # Доступ к properties через workbook
        props = wb.properties

        if job.clean_fields.get("creator", True) and props.creator:
            cleaned_fields["creator"] = props.creator
            props.creator = ""

        if job.clean_fields.get("title", False) and props.title:
            cleaned_fields["title"] = props.title
            props.title = ""

        if job.clean_fields.get("subject", False) and props.subject:
            cleaned_fields["subject"] = props.subject
            props.subject = ""

        if job.clean_fields.get("keywords", False) and props.keywords:
            cleaned_fields["keywords"] = props.keywords
            props.keywords = ""

        if job.clean_fields.get("comments", True) and props.description:
            cleaned_fields["comments"] = props.description
            props.description = ""

        if job.clean_fields.get("created", True) and props.created:
            cleaned_fields["created"] = str(props.created)
            # Для дат просто сохраняем информацию, но не изменяем

        if job.clean_fields.get("modified", True) and props.modified:
            cleaned_fields["modified"] = str(props.modified)
            # Для дат просто сохраняем информацию, но не изменяем

        # Дополнительные метаданные для Excel
        if props.lastModifiedBy:
            cleaned_fields["last_modified_by"] = props.lastModifiedBy
            props.lastModifiedBy = ""

        if props.last_modified_by:
            cleaned_fields["last_modified_by_alt"] = props.last_modified_by
            props.last_modified_by = ""

        if props.category:
            cleaned_fields["category"] = props.category
            props.category = ""

        if props.contentStatus:
            cleaned_fields["content_status"] = props.contentStatus
            props.contentStatus = ""

        if props.identifier:
            cleaned_fields["identifier"] = props.identifier
            props.identifier = ""

        if props.language:
            cleaned_fields["language"] = props.language
            props.language = ""

        if props.version:
            cleaned_fields["version"] = props.version
            props.version = ""

        if props.lastPrinted:
            cleaned_fields["last_printed"] = str(props.lastPrinted)
            # last_printed нельзя очистить напрямую

        if props.revision:
            cleaned_fields["revision"] = props.revision
            props.revision = ""

        # Сохранение изменений
        output_path = job.output_path or job.file_path
        wb.save(str(output_path))

        return cleaned_fields
