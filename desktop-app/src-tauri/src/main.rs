mod install;

use tauri::State;
use std::sync::{Arc, Mutex};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct InstallProgress {
    pub step: String,
    pub status: String,
    pub progress: f32,
    pub message: String,
}

#[derive(Default)]
pub struct AppState {
    pub install_progress: Arc<Mutex<Option<InstallProgress>>>,
}

// ── Tauri Commands ────────────────────────────────────────────────

#[tauri::command]
async fn start_install(
    window: tauri::Window,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let window_clone = window.clone();
    let state_clone = state.install_progress.clone();

    // Spawn install in background thread
    std::thread::spawn(move || {
        let steps = vec![
            ("ollama", "downloading", 0.0, "Downloading Ollama..."),
            ("ollama", "complete", 100.0, "Ollama installed"),
            ("start_ollama", "running", 50.0, "Starting Ollama service..."),
            ("start_ollama", "complete", 100.0, "Ollama service running"),
            ("bitnet", "downloading", 0.0, "Downloading BitNet model..."),
            ("bitnet", "downloading", 30.0, "Downloading model weights..."),
            ("bitnet", "downloading", 70.0, "Verifying model integrity..."),
            ("bitnet", "complete", 100.0, "BitNet model ready"),
            ("hermes", "installing", 0.0, "Installing Hermes..."),
            ("hermes", "complete", 100.0, "Hermes installed"),
            ("paperclip", "installing", 0.0, "Installing Paperclip..."),
            ("paperclip", "complete", 100.0, "Paperclip installed"),
            ("watch_once", "installing", 0.0, "Setting up Watch Once..."),
            ("watch_once", "complete", 100.0, "Watch Once ready"),
            ("solomon", "installing", 0.0, "Installing Solomon OS..."),
            ("solomon", "complete", 100.0, "Solomon OS installed"),
            ("agents", "installing", 0.0, "Installing your AI team..."),
            ("agents", "installing", 25.0, "Installing Lead Scout..."),
            ("agents", "installing", 43.0, "Installing Client Acquisition..."),
            ("agents", "installing", 57.0, "Installing Agent Builder..."),
            ("agents", "installing", 71.0, "Installing Onboarding Agent..."),
            ("agents", "installing", 86.0, "Installing Billing Agent..."),
            ("agents", "complete", 100.0, "AI team installed"),
            ("start_services", "running", 20.0, "Starting Solomon OS..."),
            ("start_services", "running", 40.0, "Starting Paperclip..."),
            ("start_services", "running", 60.0, "Starting BitNet LLM..."),
            ("start_services", "running", 80.0, "Starting Telegram bot..."),
            ("complete", "done", 100.0, "JackConnect is ready!"),
        ];

        for (step, status, progress, message) in steps {
            let progress_data = InstallProgress {
                step: step.to_string(),
                status: status.to_string(),
                progress,
                message: message.to_string(),
            };

            // Emit to frontend
            let _ = window_clone.emit("install-progress", &progress_data);

            // Sleep to simulate real work
            std::thread::sleep(std::time::Duration::from_millis(200));
        }
    });

    Ok("Installation started".to_string())
}

#[tauri::command]
fn get_agents() -> Vec<install::AgentInfo> {
    install::get_dashboard_data()
}

#[tauri::command]
fn get_total_savings() -> (f32, i32, i32) {
    install::get_total_savings()
}

#[tauri::command]
fn get_install_progress(state: State<'_, AppState>) -> Option<InstallProgress> {
    state.install_progress.lock().unwrap().clone()
}

fn main() {
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            start_install,
            get_agents,
            get_total_savings,
            get_install_progress,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}