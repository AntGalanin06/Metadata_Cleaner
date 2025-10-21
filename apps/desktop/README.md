# Metadata Cleaner Desktop (Tauri + React)

This workspace hosts the forthcoming Tauri + React desktop shell for Metadata Cleaner.

## Getting started

```bash
npm install
npm run dev  # launches Vite dev server (Tauri shell starts via `npm run tauri dev`)
```

## Structure
- `src/` — React application.
- `src-tauri/` — Tauri (Rust) sidecar responsible for window management and backend process orchestration.

## Pending work
- Wire up IPC between React and the Python backend.
- Implement core screens: file queue, progress, results, settings.
- Add localization (i18next) and theming (Material UI / Tailwind).
