"""Async event broker for broadcasting settings-related events."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any


class SettingsEventBroker:
    """Simple pub/sub broker used to notify WebSocket clients."""

    def __init__(self, *, max_queue_size: int = 32) -> None:
        self._max_queue_size = max_queue_size
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """Register a new subscriber queue."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self._max_queue_size)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove a queue from the subscriber list."""
        async with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish an event to all subscribers."""
        async with self._lock:
            subscribers = list(self._subscribers)

        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest events if a client is too slow to keep up.
                with contextlib.suppress(asyncio.QueueEmpty):
                    while queue.full():
                        queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(event)

