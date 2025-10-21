#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::{Manager, State};

struct BackendProcess(Mutex<Option<Child>>);

fn spawn_backend() -> anyhow::Result<Child> {
    let mut command = Command::new("python3");
    command
        .args(["-m", "metadata_cleaner_core.cli", "serve"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let child = command.spawn()?;
    Ok(child)
}

fn kill_backend(child: &mut Child) {
    let _ = child.kill();
}

#[tauri::command]
async fn ensure_backend(state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut guard = state
        .0
        .lock()
        .map_err(|_| "failed to lock backend process".to_string())?;

    if guard.is_none() {
        let child = spawn_backend().map_err(|err| err.to_string())?;
        *guard = Some(child);
    }

    Ok(())
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::default().build())
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let state = app.state::<BackendProcess>();
            if let Ok(mut guard) = state.0.lock() {
                if guard.is_none() {
                    if let Ok(child) = spawn_backend() {
                        *guard = Some(child);
                    }
                }
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![ensure_backend])
        .build(tauri::generate_context!())
        .expect("error while building Metadata Cleaner Tauri application");

    app.run(|app_handle, event| {
        use tauri::RunEvent;
        if let RunEvent::Exit = event {
            let state = app_handle.state::<BackendProcess>();
            if let Ok(mut guard) = state.0.lock() {
                if let Some(child) = guard.as_mut() {
                    kill_backend(child);
                }
                *guard = None;
            }
        }
    });
}
