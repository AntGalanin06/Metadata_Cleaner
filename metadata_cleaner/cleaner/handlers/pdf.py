"""Обработчик для PDF документов."""

from typing import Any

from pypdf import PdfReader, PdfWriter

from metadata_cleaner.cleaner.errors import BackupError, EncryptedFileError
from metadata_cleaner.cleaner.models import CleanResult, CleanStatus, FileJob

from . import BaseHandler


class PDFHandler(BaseHandler):
    """Обработчик для PDF файлов."""

    def clean(self, job: FileJob) -> CleanResult:
        """Очистить метаданные из PDF файла."""
        try:
            # Создание бэкапа
            if not self._create_backup(job):
                msg = "Не удалось создать резервную копию"
                raise BackupError(msg)

            cleaned_fields = self._clean_pdf_metadata(job)

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

    def _clean_pdf_metadata(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из PDF файла."""
        reader = PdfReader(str(job.file_path))

        # Проверка на зашифрованность
        if reader.is_encrypted:
            msg = "PDF файл зашифрован"
            raise EncryptedFileError(msg)

        # Чтение текущих метаданных
        cleaned_fields = {}
        if reader.metadata:
            metadata = reader.metadata

            # Сохранение удаляемых полей
            if job.clean_fields.get("title", False) and metadata.title:
                cleaned_fields["title"] = metadata.title

            if job.clean_fields.get("author", True) and metadata.author:
                cleaned_fields["author"] = metadata.author

            if job.clean_fields.get("subject", False) and metadata.subject:
                cleaned_fields["subject"] = metadata.subject

            if job.clean_fields.get("creator", True) and metadata.creator:
                cleaned_fields["creator"] = metadata.creator

            if (
                job.clean_fields.get("keywords", False)
                and hasattr(metadata, "keywords")
                and metadata.keywords
            ):
                cleaned_fields["keywords"] = metadata.keywords

            if job.clean_fields.get("created", True) and metadata.creation_date:
                cleaned_fields["created"] = str(metadata.creation_date)

            if job.clean_fields.get("modified", True) and metadata.modification_date:
                cleaned_fields["modified"] = str(metadata.modification_date)

            # Producer - производитель PDF
            if job.clean_fields.get("producer", True) and hasattr(metadata, "producer") and metadata.producer:
                cleaned_fields["producer"] = metadata.producer

        # Создание writer с копированием страниц
        writer = PdfWriter()

        # Копирование всех страниц
        for page in reader.pages:
            writer.add_page(page)

        # Селективная очистка или полное удаление метаданных
        if not self._should_remove_all_metadata(job.clean_fields):
            # Селективная очистка - создание новых метаданных
            new_metadata = {}

            if reader.metadata:
                if not job.clean_fields.get("title", False) and reader.metadata.title:
                    new_metadata["/Title"] = reader.metadata.title

                if not job.clean_fields.get("author", True) and reader.metadata.author:
                    new_metadata["/Author"] = reader.metadata.author

                if (
                    not job.clean_fields.get("subject", False)
                    and reader.metadata.subject
                ):
                    new_metadata["/Subject"] = reader.metadata.subject

                if (
                    not job.clean_fields.get("creator", True)
                    and reader.metadata.creator
                ):
                    new_metadata["/Creator"] = reader.metadata.creator

                if (
                    not job.clean_fields.get("keywords", False)
                    and hasattr(reader.metadata, "keywords")
                    and reader.metadata.keywords
                ):
                    new_metadata["/Keywords"] = reader.metadata.keywords

                if (
                    not job.clean_fields.get("created", True)
                    and reader.metadata.creation_date
                ):
                    new_metadata["/CreationDate"] = reader.metadata.creation_date

                if (
                    not job.clean_fields.get("modified", True)
                    and reader.metadata.modification_date
                ):
                    new_metadata["/ModDate"] = reader.metadata.modification_date

                # Producer - производитель PDF
                if (
                    not job.clean_fields.get("producer", True)
                    and hasattr(reader.metadata, "producer")
                    and reader.metadata.producer
                ):
                    new_metadata["/Producer"] = reader.metadata.producer

            # Установка новых метаданных
            if new_metadata:
                writer.add_metadata(new_metadata)

        # Сохранение файла
        output_path = job.output_path or job.file_path
        with open(str(output_path), "wb") as output_file:
            writer.write(output_file)

        return cleaned_fields

    def _should_remove_all_metadata(self, clean_fields: dict[str, bool]) -> bool:
        """Проверить, нужно ли удалить все метаданные."""
        metadata_fields = [
            "title",
            "author",
            "subject",
            "creator",
            "producer",
            "keywords",
            "created",
            "modified",
        ]
        return all(clean_fields.get(field, True) for field in metadata_fields)
