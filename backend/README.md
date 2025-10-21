# Metadata Cleaner Core Backend

This package houses the Python 3.14 backend that powers the rewritten Metadata Cleaner desktop application (Tauri + React).

## Quick start

```bash
poetry install
poetry run metadata-cleaner-core serve
```

By default the API becomes available on `http://127.0.0.1:8765`.

## Structure
- `metadata_cleaner_core/` — core package (metadata processing, settings, API wiring).
- `metadata_cleaner_core/api/` — FastAPI application factory and routes.
- `metadata_cleaner_core/cli.py` — Typer-based entry point used during development and inside the Tauri shell.

## Next steps
- Extract and adapt the existing metadata handlers into this package.
- Add REST/WebSocket endpoints for job management, settings, and logs.
- Implement background task queue and persistence.
- Integrate automated tests for metadata processing and API flows.
