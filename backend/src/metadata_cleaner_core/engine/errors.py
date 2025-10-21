"""Custom exceptions for the metadata cleaning engine."""


class MetadataCleanerError(Exception):
    """Base exception for metadata cleaning errors."""


class UnsupportedFileTypeError(MetadataCleanerError):
    """Unsupported file type."""


class FileAccessError(MetadataCleanerError):
    """File cannot be accessed."""


class MetadataProcessingError(MetadataCleanerError):
    """Metadata processing failure."""


class BackupError(MetadataCleanerError):
    """Backup creation failure."""


class CorruptedFileError(MetadataCleanerError):
    """File is corrupted."""


class EncryptedFileError(MetadataCleanerError):
    """File is encrypted."""
