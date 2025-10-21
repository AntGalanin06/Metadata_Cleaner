# Metadata Cleaner — Cloud & Local Environment Guide

This guide captures the minimal steps required to provision a reproducible environment for the Python 3.14 + Tauri/React rewrite.

## 1. Base system requirements

| Platform | Dependencies |
| --- | --- |
| **Linux (Ubuntu 22.04+)** | `build-essential`, `pkg-config`, `libgtk-3-dev`, `libayatana-appindicator3-dev`, `webkit2gtk-4.1`, `curl`, `git`, `python3.14`, `python3.14-venv`, `nodejs` (18+), `npm`, Rust toolchain (`rustup`) |
| **macOS 13+** | Xcode Command Line Tools, [Homebrew](https://brew.sh/), `python@3.14`, `node@18`, `npm`, `rustup`, `tauri-cli`, `cocoapods` |
| **Windows 11/10** | Visual Studio Build Tools (C++ workload), Windows 10 SDK, [Python 3.14](https://www.python.org/downloads/), Node.js 18 LTS, Rust (MSVC target), PowerShell 7, `winget install tauri-apps.tauri-cli` |

> **Tip:** For cloud runners (GitHub Codespaces, Gitpod, Azure Dev Box) pre-install the Rust and Tauri prerequisites to avoid compiling WebKitGTK from source on every CI run.

## 2. Backend setup (FastAPI + Poetry)

```bash
git clone https://github.com/AntGalanin06/Metadata_Cleaner.git
cd Metadata_Cleaner/backend
pipx install poetry  # or use pre-installed Poetry
poetry env use python3.14
poetry install

# run locally
poetry run uvicorn metadata_cleaner_core.api.app:create_app --factory --reload --port 8765

# run tests
poetry run pytest
```

The backend exposes REST endpoints under `/api` plus WebSocket feeds for job updates (`/ws/jobs/{job_id}`) and profile changes (`/ws/settings/profiles`).

## 3. Desktop shell setup (Vite + React + Tauri)

```bash
cd ../apps/desktop
npm install

# React developer mode (expects backend on :8765)
npm run dev

# Full-stack Tauri preview (starts backend automatically via Rust command)
npm run tauri dev

# Component tests
npm run test
```

Tauri bundles the compiled React app and spawns the FastAPI server during development builds. Make sure `TAURI_DEV_HOST` or the default `http://127.0.0.1:8765` is reachable.

## 4. Continuous Integration outline

Recommended CI jobs:

1. **Backend** — setup Python 3.14, install Poetry deps, run `pytest`, export coverage.
2. **Frontend** — install Node.js 18, run `npm ci`, execute `npm run build` and `npm run test` (Vitest).
3. **Tauri bundle (optional)** — install Rust stable, `tauri-cli`, run `npm run tauri build` for release artefacts on Linux/macOS/Windows runners.

Cache the following directories for faster builds:

- `~/.cache/pypoetry` and `~/.venv` (Linux/macOS) or `%APPDATA%\pypoetry` (Windows)
- `~/.cargo` (Rust crates)
- `apps/desktop/node_modules` or npm cache (`~/.npm`)

## 5. Troubleshooting checklist

- **WebKitGTK build errors (Linux):** ensure `libwebkit2gtk-4.1-dev` is installed or use the official Tauri bundle Docker image.
- **Backend port conflicts:** override with `METADATA_CLEANER_API_PORT=<port>` and update the frontend `API_URL` when running multiple instances.
- **Missing WebSocket updates:** verify proxies/firewalls allow localhost WebSocket connections; Tauri uses `ws://127.0.0.1:8765` by default.

With the steps above the migration branch can be built reproducibly across macOS, Windows, and Linux environments as well as in containerised CI pipelines.
