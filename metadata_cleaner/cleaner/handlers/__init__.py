"""Обработчики для различных типов файлов."""

from abc import ABC, abstractmethod

from metadata_cleaner.cleaner.models import CleanResult, FileJob


class BaseHandler(ABC):
    """Базовый класс для всех обработчиков файлов."""

    @abstractmethod
    def clean(self, job: FileJob) -> CleanResult:
        """Очистить метаданные файла."""

    def _create_backup(self, job: FileJob) -> bool:
        """Создать резервную копию файла."""
        if not job.backup_enabled:
            return True

        # Не создаем бэкап, если пишем в новый файл
        if job.output_path and job.output_path != job.file_path:
            return True

        try:
            backup_path = job.file_path.with_suffix(job.file_path.suffix + ".bak")
            backup_path.write_bytes(job.file_path.read_bytes())
            return True
        except Exception:
            return False
