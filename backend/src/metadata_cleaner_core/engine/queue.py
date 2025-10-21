"""Simple async job queue for metadata cleaning."""

from __future__ import annotations

import asyncio
import contextlib
import csv
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from metadata_cleaner_core.engine.dispatcher import MetadataDispatcher
from metadata_cleaner_core.engine.models import (
    CleanResult,
    CleaningOptions,
    CleanStatus,
    FileJob,
    OutputMode,
)
from metadata_cleaner_core.engine.progress import (
    DEFAULT_STEP_DEFINITIONS,
    JobProgressState,
    StepStatus,
)


@dataclass(slots=True)
class Job:
    job_id: str
    paths: list[Path]
    options: CleaningOptions
    results: list[CleanResult] = field(default_factory=list)
    status: CleanStatus = CleanStatus.PENDING
    progress: JobProgressState | None = None
    log_path: Path | None = None
    csv_log_path: Path | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None


class JobQueue:
    """In-memory FIFO queue for background cleaning jobs."""

    def __init__(self, dispatcher: MetadataDispatcher) -> None:
        self._dispatcher = dispatcher
        self._jobs: Dict[str, Job] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._lock = asyncio.Lock()
        self._listeners: Dict[str, List[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._settings_service = dispatcher.settings_service

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None

    # Internal helpers -------------------------------------------------

    def _initialize_job_state(self, job: Job) -> None:
        job.progress = JobProgressState.from_paths(
            job.paths, step_definitions=DEFAULT_STEP_DEFINITIONS
        )
        job.progress.ensure_indices()
        try:
            log_dir = self._settings_service.get_logging_directory()
        except Exception:
            log_dir = Path.cwd() / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
        job.log_path = log_dir / f"{job.job_id}.jsonl"
        job.csv_log_path = job.log_path.with_suffix(".csv")
        try:
            job.log_path.write_text("", encoding="utf-8")
        except OSError:
            job.log_path = None
            job.csv_log_path = None
        self._log_event(
            job,
            "job_queued",
            level="debug",
            paths=[str(path) for path in job.paths],
        )

    def _should_log(self, level: str) -> bool:
        priorities = {"debug": 10, "info": 20, "warning": 30, "error": 40}
        configured = self._settings_service.get_logging_level()
        return priorities.get(level, 20) >= priorities.get(configured, 20)

    def _log_event(self, job: Job, event: str, *, level: str = "info", **data: Any) -> None:
        if not job.log_path or not self._should_log(level):
            return
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "job_id": job.job_id,
            **data,
        }
        try:
            with open(job.log_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _generate_csv_log(self, job: Job) -> None:
        if not job.log_path or not job.csv_log_path:
            return
        try:
            with open(job.log_path, "r", encoding="utf-8") as source:
                entries = [
                    json.loads(line)
                    for line in source
                    if line.strip()
                ]
        except (OSError, json.JSONDecodeError):
            return

        if not entries:
            return

        fieldnames: list[str] = sorted({key for entry in entries for key in entry.keys()})
        try:
            with open(job.csv_log_path, "w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(target, fieldnames=fieldnames)
                writer.writeheader()
                for entry in entries:
                    writer.writerow(entry)
        except OSError:
            job.csv_log_path = None

    async def _worker(self) -> None:
        while True:
            job_id = await self._queue.get()
            job = self._jobs.get(job_id)
            if job is None:
                self._queue.task_done()
                continue
            if job.progress is None:
                self._initialize_job_state(job)
            job.status = CleanStatus.PROCESSING
            self._log_event(job, "job_started", level="info")
            await self._emit(job_id)

            backup_mode = self._dispatcher.settings_service.get_output_mode()
            for index, path in enumerate(job.paths):
                file_state = job.progress.get_file_state(index) if job.progress else None
                if file_state:
                    file_state.set_status(CleanStatus.PROCESSING)
                    file_state.set_step_status("queued", StepStatus.COMPLETED)
                    file_state.set_step_status("loading", StepStatus.RUNNING)
                self._log_event(
                    job,
                    "file_started",
                    level="info",
                    path=str(path),
                    index=index + 1,
                )
                await self._emit(job_id)

                backup_required = (
                    job.options.create_backup
                    or backup_mode == OutputMode.BACKUP_AND_OVERWRITE
                )

                try:
                    if file_state:
                        file_state.set_step_status("loading", StepStatus.COMPLETED)
                        if backup_required:
                            file_state.set_step_status("backup", StepStatus.RUNNING)
                        else:
                            file_state.set_step_status(
                                "backup",
                                StepStatus.SKIPPED,
                                detail="Отключено настройками",
                            )
                    await self._emit(job_id)

                    if file_state:
                        file_state.set_step_status("cleaning", StepStatus.RUNNING)
                    await self._emit(job_id)

                    result = self._dispatcher.process_file_with_options(path, job.options)

                    if file_state:
                        if backup_required:
                            file_state.set_step_status("backup", StepStatus.COMPLETED)
                        if result.status == CleanStatus.SUCCESS:
                            file_state.set_step_status("cleaning", StepStatus.COMPLETED)
                            file_state.set_step_status("saving", StepStatus.RUNNING)
                            file_state.set_step_status("saving", StepStatus.COMPLETED)
                            file_state.set_status(CleanStatus.SUCCESS)
                        else:
                            file_state.set_step_status(
                                "cleaning",
                                StepStatus.FAILED,
                                detail=result.message,
                            )
                            file_state.set_status(CleanStatus.ERROR)
                    job.results.append(result)
                    self._log_event(
                        job,
                        "file_completed",
                        level="info",
                        path=str(path),
                        status=result.status.value,
                        message=result.message,
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    result = CleanResult(
                        job=FileJob(file_path=path),
                        status=CleanStatus.ERROR,
                        message=str(exc),
                        error=exc,
                    )
                    job.results.append(result)
                    if file_state:
                        failing_step = file_state.current_step or "loading"
                        file_state.set_step_status(
                            failing_step,
                            StepStatus.FAILED,
                            detail=str(exc),
                        )
                        file_state.set_status(CleanStatus.ERROR)
                    self._log_event(
                        job,
                        "file_failed",
                        level="error",
                        path=str(path),
                        error=str(exc),
                    )
                finally:
                    if job.progress:
                        job.progress.recalculate()
                    await self._emit(job_id)

            if any(result.status == CleanStatus.ERROR for result in job.results):
                job.status = CleanStatus.ERROR
                level = "error"
            else:
                job.status = CleanStatus.SUCCESS
                level = "info"
            job.completed_at = datetime.now(timezone.utc)
            self._log_event(
                job,
                "job_completed",
                level=level,
                status=job.status.value,
                duration=(
                    job.completed_at - job.created_at
                ).total_seconds()
                if job.completed_at
                else None,
            )
            self._generate_csv_log(job)
            await self._emit(job_id)
            self._queue.task_done()

    async def enqueue(self, paths: list[Path], options: CleaningOptions) -> str:
        job_id = uuid.uuid4().hex
        job = Job(job_id=job_id, paths=paths, options=options)
        self._initialize_job_state(job)
        async with self._lock:
            self._jobs[job_id] = job
        await self._queue.put(job_id)
        await self._emit(job_id)
        return job_id

    async def get(self, job_id: str) -> Optional[Job]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_jobs(self) -> list[Job]:
        async with self._lock:
            return list(self._jobs.values())

    async def subscribe(self, job_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            self._listeners[job_id].append(queue)
        await queue.put(self._serialize_job(job))
        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            listeners = self._listeners.get(job_id)
            if listeners and queue in listeners:
                listeners.remove(queue)
                if not listeners:
                    self._listeners.pop(job_id, None)

    async def _emit(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            listeners = list(self._listeners.get(job_id, []))
        if not listeners:
            return
        payload = self._serialize_job(job)
        for queue in listeners:
            await queue.put(payload)

    @staticmethod
    def _serialize_job(job: Job) -> dict[str, Any]:
        progress_payload = job.progress.as_dict() if job.progress else None
        log_formats: list[str] = []
        if job.log_path and job.log_path.exists():
            log_formats.append("json")
        if job.csv_log_path and job.csv_log_path.exists():
            log_formats.append("csv")
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "total": len(job.paths),
            "processed": len(job.results),
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "progress": progress_payload,
            "log": {
                "ready": bool(job.completed_at and log_formats),
                "formats": log_formats,
            },
            "results": [
                {
                    "path": str(result.job.file_path),
                    "status": result.status.value,
                    "message": result.message,
                    "cleaned_fields": result.cleaned_fields or {},
                    "processing_time": result.processing_time,
                    "error": str(result.error) if result.error else None,
                }
                for result in job.results
            ],
        }
