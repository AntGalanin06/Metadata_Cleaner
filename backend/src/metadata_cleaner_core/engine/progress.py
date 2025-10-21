"""Utilities for tracking detailed job progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from metadata_cleaner_core.engine.models import CleanStatus


class StepStatus(str, Enum):
    """State of a progress step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class StepDefinition:
    """Declarative description of a progress step."""

    key: str
    label: str
    weight: float


DEFAULT_STEP_DEFINITIONS: tuple[StepDefinition, ...] = (
    StepDefinition(key="queued", label="Добавлено в очередь", weight=0.05),
    StepDefinition(key="loading", label="Загрузка файла", weight=0.15),
    StepDefinition(key="backup", label="Резервное копирование", weight=0.35),
    StepDefinition(key="cleaning", label="Очистка метаданных", weight=0.85),
    StepDefinition(key="saving", label="Сохранение результата", weight=1.0),
)


@dataclass(slots=True)
class StepState:
    """Runtime state of a progress step."""

    key: str
    label: str
    weight: float
    status: StepStatus = StepStatus.PENDING
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status.value,
            "detail": self.detail,
            "percent": round(self.weight * 100, 2),
        }


@dataclass(slots=True)
class FileProgressState:
    """Progress state for a single file."""

    path: Path
    index: int
    total: int
    steps: list[StepState]
    status: CleanStatus = CleanStatus.PENDING
    current_step: str | None = None
    percent: float = 0.0

    def set_status(self, status: CleanStatus) -> None:
        self.status = status

    def set_step_status(
        self, key: str, status: StepStatus, *, detail: str | None = None
    ) -> None:
        step = self._get_step(key)
        step.status = status
        if detail is not None:
            step.detail = detail
        if status == StepStatus.RUNNING:
            self.current_step = key
        elif self.current_step == key and status in {
            StepStatus.COMPLETED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
        }:
            self.current_step = None
        self._recalculate_percent()

    def _get_step(self, key: str) -> StepState:
        for step in self.steps:
            if step.key == key:
                return step
        msg = f"Unknown step: {key}"
        raise KeyError(msg)

    def _recalculate_percent(self) -> None:
        completed = 0.0
        previous_weight = 0.0
        for step in self.steps:
            if step.status == StepStatus.COMPLETED or step.status == StepStatus.SKIPPED:
                completed = max(completed, step.weight)
                previous_weight = step.weight
            elif step.status == StepStatus.RUNNING:
                completed = max(
                    completed,
                    previous_weight
                    + max(step.weight - previous_weight, 0.0) * 0.5,
                )
                break
            elif step.status == StepStatus.FAILED:
                completed = max(completed, step.weight)
                break
        self.percent = min(max(completed, 0.0), 1.0)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "index": self.index,
            "total": self.total,
            "status": self.status.value,
            "current_step": self.current_step,
            "percent": round(self.percent * 100, 2),
            "steps": [step.as_dict() for step in self.steps],
        }


@dataclass(slots=True)
class JobProgressState:
    """Aggregated progress information for a job."""

    files: list[FileProgressState] = field(default_factory=list)
    overall_percent: float = 0.0

    @classmethod
    def from_paths(
        cls,
        paths: Iterable[Path],
        *,
        step_definitions: Iterable[StepDefinition],
    ) -> "JobProgressState":
        step_defs = list(step_definitions)
        path_list = list(paths)
        total = len(path_list)
        files = [
            FileProgressState(
                path=path,
                index=index + 1,
                total=total,
                steps=[
                    StepState(key=step.key, label=step.label, weight=step.weight)
                    for step in step_defs
                ],
            )
            for index, path in enumerate(path_list)
        ]
        return cls(files=files)

    def ensure_indices(self) -> None:
        total = len(self.files)
        for idx, file_state in enumerate(self.files, start=1):
            file_state.index = idx
            file_state.total = total

    def recalculate(self) -> None:
        if not self.files:
            self.overall_percent = 0.0
            return
        total = len(self.files)
        accumulated = sum(file_state.percent for file_state in self.files)
        self.overall_percent = min(max(accumulated / total, 0.0), 1.0)

    def get_file_state(self, index: int) -> FileProgressState:
        return self.files[index]

    def as_dict(self) -> dict[str, Any]:
        self.recalculate()
        return {
            "overall_percent": round(self.overall_percent * 100, 2),
            "files": [file_state.as_dict() for file_state in self.files],
        }

