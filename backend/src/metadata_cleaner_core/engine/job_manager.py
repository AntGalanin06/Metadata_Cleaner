"""Job management helpers."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from metadata_cleaner_core.engine.queue import JobQueue, Job

if TYPE_CHECKING:
    from asyncio import Queue as _EventQueue


class JobManager:
    """Thin wrapper around JobQueue with lifecycle hooks."""

    def __init__(self, queue: JobQueue) -> None:
        self._queue = queue
        self._started = False

    async def ensure_started(self) -> None:
        if not self._started:
            await self._queue.start()
            self._started = True

    async def enqueue(self, *args, **kwargs) -> str:
        await self.ensure_started()
        return await self._queue.enqueue(*args, **kwargs)

    async def get(self, job_id: str) -> Optional[Job]:
        return await self._queue.get(job_id)

    async def list_jobs(self) -> list[Job]:
        return await self._queue.list_jobs()

    async def subscribe(self, job_id: str) -> "_EventQueue":
        await self.ensure_started()
        return await self._queue.subscribe(job_id)

    async def unsubscribe(self, job_id: str, queue: "_EventQueue") -> None:
        await self._queue.unsubscribe(job_id, queue)
