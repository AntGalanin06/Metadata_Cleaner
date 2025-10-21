"""Command-line helpers for running the Metadata Cleaner backend service."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import typer
import uvicorn

from metadata_cleaner_core.api import create_app

cli = typer.Typer(add_completion=False, help="Metadata Cleaner backend utilities.")


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context placeholder for future resource management."""
    yield


@cli.command()
def serve(host: str = "127.0.0.1", port: int = 8765, reload: bool = False) -> None:
    """Run the FastAPI server."""
    app = create_app()
    app.router.lifespan_context = lifespan  # type: ignore[attr-defined]

    config = uvicorn.Config(app, host=host, port=port, reload=reload, log_level="info")
    server = uvicorn.Server(config)

    async def _run() -> None:
        await server.serve()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:  # pragma: no cover - standard CLI behaviour
        typer.secho("Server interrupted by user", fg=typer.colors.RED)


if __name__ == "__main__":
    cli()
