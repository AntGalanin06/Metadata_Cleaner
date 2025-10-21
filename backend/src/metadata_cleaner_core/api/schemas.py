"""Pydantic schemas for the Metadata Cleaner API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from metadata_cleaner_core.engine.models import CleanStatus, CleaningOptions


class CleaningOptionsModel(BaseModel):
    clean_author: bool = Field(default=True, description="Remove authorship information")
    clean_created_date: bool = Field(default=True, description="Remove creation date")
    clean_modified_date: bool = Field(default=True, description="Remove modification date")
    clean_comments: bool = Field(default=True, description="Remove user comments")
    clean_gps_data: bool = Field(default=True, description="Remove GPS metadata")
    clean_camera_info: bool = Field(default=True, description="Remove camera metadata")
    clean_title: bool = Field(default=True, description="Remove title metadata")
    clean_subject: bool = Field(default=True, description="Remove subject metadata")
    clean_keywords: bool = Field(default=True, description="Remove keyword metadata")
    create_backup: bool = Field(default=True, description="Create backup copy before cleaning")

    def to_dataclass(self) -> CleaningOptions:
        return CleaningOptions(**self.model_dump())


class ProcessRequest(BaseModel):
    paths: list[str] = Field(min_length=1, description="Absolute file paths to process")
    options: CleaningOptionsModel | None = None


class FileProcessResult(BaseModel):
    path: str
    status: CleanStatus
    message: str
    cleaned_fields: dict[str, Any] = Field(default_factory=dict)
    processing_time: float | None = None
    error: str | None = None


class ProcessResponse(BaseModel):
    job_id: str | None = None
    status: CleanStatus = Field(default=CleanStatus.SUCCESS)
    results: list[FileProcessResult] = Field(default_factory=list)
    progress: "JobProgressModel | None" = None
    log: "JobLogInfoModel | None" = None
    created_at: str | None = None
    completed_at: str | None = None


class MetadataFieldModel(BaseModel):
    key: str
    category: str
    name_key: str
    description_key: str
    result_fields: list[str]
    default_remove: bool
    priority: int


class MetadataCatalogueItem(BaseModel):
    file_type: str
    fields: list[MetadataFieldModel]


class MetadataCatalogueResponse(BaseModel):
    items: list[MetadataCatalogueItem]
    categories: list[str]


class SettingsPayload(BaseModel):
    data: dict[str, Any]


class SettingsResponse(BaseModel):
    settings: dict[str, Any]


class SettingsSchemaResponse(BaseModel):
    defaults: dict[str, Any]
    file_type_defaults: dict[str, dict[str, bool]]
    theme_options: list[str]
    language_options: list[str]
    output_modes: list[str]


class ProfileModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    file_type_settings: dict[str, dict[str, bool]]
    created_at: str
    updated_at: str


class ProfileListResponse(BaseModel):
    profiles: list[ProfileModel]
    active_id: str


class ProfileCreatePayload(BaseModel):
    name: str
    description: str | None = None
    file_type_settings: dict[str, dict[str, bool]] | None = None


class ProfileUpdatePayload(BaseModel):
    name: str | None = None
    description: str | None = None
    file_type_settings: dict[str, dict[str, bool]] | None = None


class JobProgressStepModel(BaseModel):
    key: str
    label: str
    status: str
    percent: float
    detail: str | None = None


class JobProgressFileModel(BaseModel):
    path: str
    index: int
    total: int
    status: CleanStatus
    current_step: str | None = None
    percent: float
    steps: list[JobProgressStepModel]


class JobProgressModel(BaseModel):
    overall_percent: float
    files: list[JobProgressFileModel]


class JobLogInfoModel(BaseModel):
    ready: bool
    formats: list[str]


ProcessResponse.model_rebuild()
