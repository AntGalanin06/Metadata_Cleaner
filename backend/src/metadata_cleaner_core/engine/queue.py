"""Simple async job queue for metadata cleaning."""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from metadata_cleaner_core.engine.dispatcher import MetadataDispatcher
from metadata_cleaner_core.engine.models import CleanResult, CleaningOptions, CleanStatus


@dataclass(slots=True)
class Job:
    job_id: str
    paths: list[Path]
    options: CleaningOptions
    results: list[CleanResult] = field(default_factory=list)
    status: CleanStatus = CleanStatus.PENDING


class JobQueue:
    """In-memory FIFO queue for background cleaning jobs."""

    def __init__(self, dispatcher: MetadataDispatcher) -> None:
        self._dispatcher = dispatcher
        self._jobs: Dict[str, Job] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._lock = asyncio.Lock()
        self._listeners: Dict[str, List[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None

    async def _worker(self) -> None:
        while True:
            job_id = await self._queue.get()
            job = self._jobs.get(job_id)
            if job is None:
                continue
            job.status = CleanStatus.PROCESSING
            await self._emit(job_id)
            for path in job.paths:
                result = self._dispatcher.process_file_with_options(path, job.options)
                job.results.append(result)
                await self._emit(job_id)
            if any(result.status == CleanStatus.ERROR for result in job.results):
                job.status = CleanStatus.ERROR
            else:
                job.status = CleanStatus.SUCCESS
            await self._emit(job_id)
            self._queue.task_done()

    async def enqueue(self, paths: list[Path], options: CleaningOptions) -> str:
        job_id = uuid.uuid4().hex
        job = Job(job_id=job_id, paths=paths, options=options)
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
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "total": len(job.paths),
            "processed": len(job.results),
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
