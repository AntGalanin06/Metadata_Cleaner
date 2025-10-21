"""FastAPI application factory for the Metadata Cleaner backend."""

import contextlib
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from metadata_cleaner_core.api.schemas import (
    CleaningOptionsModel,
    FileProcessResult,
    MetadataCatalogueResponse,
    MetadataFieldModel,
    ProcessRequest,
    ProcessResponse,
    SettingsPayload,
    SettingsResponse,
    SettingsSchemaResponse,
)
from metadata_cleaner_core.engine.dispatcher import MetadataDispatcher
from metadata_cleaner_core.engine.models import CleanStatus
from metadata_cleaner_core.engine.queue import JobQueue
from metadata_cleaner_core.engine.job_manager import JobManager
from metadata_cleaner_core.engine.metadata_registry import MetadataRegistry
from metadata_cleaner_core.settings.service import SettingsService
from metadata_cleaner_core.version import get_version


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Metadata Cleaner Core API",
        version=get_version(),
        description=(
            "Backend service powering the rewritten Metadata Cleaner desktop application."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://localhost:1420", "http://127.0.0.1:1420"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings = SettingsService()
    dispatcher = MetadataDispatcher(settings_service=settings)
    job_queue = JobQueue(dispatcher)
    job_manager = JobManager(job_queue)
    api_router = APIRouter(prefix="/api")


    @app.on_event("startup")
    async def _startup() -> None:
        await job_manager.ensure_started()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await job_queue.stop()

    app.state.settings_service = settings
    app.state.dispatcher = dispatcher
    app.state.job_manager = job_manager

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        """Simple health check endpoint."""
        return {"status": "ok"}

    @app.get("/legacy/extensions", tags=["legacy"])
    async def list_supported_extensions() -> dict[str, list[str]]:
        """Return currently supported extensions."""
        return {"extensions": sorted(dispatcher.get_supported_extensions())}

    @api_router.get(
        "/metadata/fields", response_model=MetadataCatalogueResponse, tags=["metadata"]
    )
    async def get_metadata_fields() -> MetadataCatalogueResponse:
        """Return metadata field catalogue grouped by file type."""
        items = []
        for entry in MetadataRegistry.get_catalogue():
            fields = [MetadataFieldModel(**field) for field in entry["fields"]]
            items.append({"file_type": entry["file_type"], "fields": fields})
        return MetadataCatalogueResponse(items=items, categories=MetadataRegistry.get_categories())

    @api_router.get("/settings", response_model=SettingsResponse, tags=["settings"])
    async def read_settings() -> SettingsResponse:
        """Return current settings snapshot."""
        return SettingsResponse(settings=settings.get_all_settings())

    @api_router.put("/settings", response_model=SettingsResponse, tags=["settings"])
    async def update_settings(payload: SettingsPayload) -> SettingsResponse:
        """Merge and persist incoming settings data."""
        settings.update_settings(payload.data)
        return SettingsResponse(settings=settings.get_all_settings())

    @api_router.get(
        "/settings/schema", response_model=SettingsSchemaResponse, tags=["settings"]
    )
    async def read_settings_schema() -> SettingsSchemaResponse:
        """Return default settings schema to drive the UI."""
        schema = settings.get_settings_schema()
        return SettingsSchemaResponse(**schema)

    @api_router.post("/process", response_model=ProcessResponse, tags=["processing"])
    async def process_files(request: ProcessRequest) -> ProcessResponse:
        """Process one or more files synchronously."""
        options_model = request.options or CleaningOptionsModel()
        options = options_model.to_dataclass()

        results: list[FileProcessResult] = []
        for path_str in request.paths:
            path = Path(path_str).expanduser()
            clean_result = dispatcher.process_file_with_options(path, options)
            results.append(
                FileProcessResult(
                    path=str(path),
                    status=clean_result.status,
                    message=clean_result.message,
                    cleaned_fields=clean_result.cleaned_fields or {},
                    processing_time=clean_result.processing_time,
                    error=str(clean_result.error) if clean_result.error else None,
                )
            )

        overall_status = (
            CleanStatus.ERROR
            if any(result.status == CleanStatus.ERROR for result in results)
            else CleanStatus.SUCCESS
        )

        return ProcessResponse(job_id=None, status=overall_status, results=results)


    @api_router.post("/jobs", tags=["processing"])
    async def enqueue_job(request: ProcessRequest) -> dict[str, str]:
        """Enqueue a background cleaning job."""
        options_model = request.options or CleaningOptionsModel()
        options = options_model.to_dataclass()
        paths = [Path(item).expanduser() for item in request.paths]
        job_id = await job_manager.enqueue(paths=paths, options=options)
        return {"job_id": job_id}

    @api_router.get("/jobs/{job_id}", tags=["processing"], response_model=ProcessResponse)
    async def get_job(job_id: str) -> ProcessResponse:
        job = await job_manager.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        results = [
            FileProcessResult(
                path=str(result.job.file_path),
                status=result.status,
                message=result.message,
                cleaned_fields=result.cleaned_fields or {},
                processing_time=result.processing_time,
                error=str(result.error) if result.error else None,
            )
            for result in job.results
        ]
        return ProcessResponse(job_id=job.job_id, status=job.status, results=results)

    @app.websocket("/ws/jobs/{job_id}")
    async def job_updates(websocket: WebSocket, job_id: str) -> None:
        await websocket.accept()
        try:
            queue = await job_manager.subscribe(job_id)
        except KeyError:
            await websocket.send_json({"error": "job_not_found", "job_id": job_id})
            await websocket.close(code=1008)
            return

        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
                if event.get("status") in {"success", "error"}:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            await job_manager.unsubscribe(job_id, queue)
            with contextlib.suppress(RuntimeError):
                await websocket.close()

    app.include_router(api_router)

    return app
