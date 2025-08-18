"""Кастомные исключения для обработки ошибок очистки метаданных."""


class MetadataCleanerError(Exception):
    """Базовое исключение для всех ошибок очистки метаданных."""


class UnsupportedFileTypeError(MetadataCleanerError):
    """Неподдерживаемый тип файла."""


class FileAccessError(MetadataCleanerError):
    """Ошибка доступа к файлу."""


class MetadataProcessingError(MetadataCleanerError):
    """Ошибка обработки метаданных."""


class BackupError(MetadataCleanerError):
    """Ошибка создания резервной копии."""


class CorruptedFileError(MetadataCleanerError):
    """Поврежденный файл."""


class EncryptedFileError(MetadataCleanerError):
    """Зашифрованный файл."""
