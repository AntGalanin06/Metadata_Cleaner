"""Data models shared across the metadata cleaning engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class CleanStatus(Enum):
    """Status of a cleaning job."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class FileType(Enum):
    """Supported file types."""

    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    VIDEO = "video"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


class OutputMode(Enum):
    """Output strategy for processed files."""

    REPLACE = "replace"
    CREATE_COPY = "create_copy"
    BACKUP_AND_OVERWRITE = "backup_and_overwrite"


@dataclass
class FileJob:
    """Description of a file being processed."""

    file_path: Path
    file_type: FileType | None = None
    output_path: Path | None = None
    backup_enabled: bool = False
    clean_fields: dict[str, bool] | None = None


@dataclass
class CleanResult:
    """Result returned by handlers after processing."""

    job: FileJob
    status: CleanStatus
    message: str
    cleaned_fields: dict[str, Any] | None = field(default_factory=dict)
    processing_time: float | None = None
    error: Optional[Exception] = None


@dataclass
class CleaningOptions:
    """Options configured via CLI or API for processing."""

    clean_author: bool = True
    clean_created_date: bool = True
    clean_modified_date: bool = True
    clean_comments: bool = True
    clean_gps_data: bool = True
    clean_camera_info: bool = True
    clean_title: bool = True
    clean_subject: bool = True
    clean_keywords: bool = True
    create_backup: bool = True
