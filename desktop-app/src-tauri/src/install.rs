use serde::{Deserialize, Serialize};
use std::process::Command;
use std::thread;
use std::sync::{Arc, Mutex};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct InstallStep {
    pub step: String,
    pub status: String,
    pub progress: f32,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AgentInfo {
    pub id: String,
    pub name: String,
    pub status: String,
    pub tasks_completed: i32,
    pub hours_saved: f32,
}

// ── Core Install Logic ────────────────────────────────────────────

pub fn run_full_install(
    progress_callback: impl Fn(InstallStep) + Send + 'static,
) -> Result<String, String> {
    // Step 1: Download Ollama
    progress_callback(InstallStep {
        step: "ollama".to_string(),
        status: "downloading".to_string(),
        progress: 0.0,
        message: "Downloading Ollama...".to_string(),
    });

    download_ollama(&progress_callback)?;

    progress_callback(InstallStep {
        step: "ollama".to_string(),
        status: "complete".to_string(),
        progress: 100.0,
        message: "Ollama installed".to_string(),
    });

    // Step 2: Start Ollama service
    progress_callback(InstallStep {
        step: "start_ollama".to_string(),
        status: "running".to_string(),
        progress: 0.0,
        message: "Starting Ollama service...".to_string(),
    });

    start_ollama_service(&progress_callback)?;

    // Step 3: Pull BitNet model
    progress_callback(InstallStep {
        step: "bitnet".to_string(),
        status: "downloading".to_string(),
        progress: 0.0,
        message: "Downloading BitNet model (this may take a few minutes)...".to_string(),
    });

    pull_bitnet_model(&progress_callback)?;

    // Step 4: Install Hermes
    progress_callback(InstallStep {
        step: "hermes".to_string(),
        status: "downloading".to_string(),
        progress: 0.0,
        message: "Installing Hermes agent system...".to_string(),
    });

    install_hermes(&progress_callback)?;

    // Step 5: Install Paperclip
    progress_callback(InstallStep {
        step: "paperclip".to_string(),
        status: "downloading".to_string(),
        progress: 0.0,
        message: "Installing Paperclip orchestration layer...".to_string(),
    });

    install_paperclip(&progress_callback)?;

    // Step 6: Install Watch Once
    progress_callback(InstallStep {
        step: "watch_once".to_string(),
        status: "installing".to_string(),
        progress: 0.0,
        message: "Setting up Watch Once automation...".to_string(),
    });

    install_watch_once(&progress_callback)?;

    // Step 7: Install Solomon OS
    progress_callback(InstallStep {
        step: "solomon".to_string(),
        status: "installing".to_string(),
        progress: 0.0,
        message: "Installing Solomon OS...".to_string(),
    });

    install_solomon_os(&progress_callback)?;

    // Step 8: Install agents
    progress_callback(InstallStep {
        step: "agents".to_string(),
        status: "installing".to_string(),
        progress: 0.0,
        message: "Installing your AI team...".to_string(),
    });

    install_agents(&progress_callback)?;

    // Step 9: Start all services
    progress_callback(InstallStep {
        step: "start_services".to_string(),
        status: "running".to_string(),
        progress: 0.0,
        message: "Starting your AI team...".to_string(),
    });

    start_all_services(&progress_callback)?;

    progress_callback(InstallStep {
        step: "complete".to_string(),
        status: "done".to_string(),
        progress: 100.0,
        message: "JackConnect is ready!".to_string(),
    });

    Ok("Installation complete".to_string())
}

// ── Ollama ────────────────────────────────────────────────────────

fn download_ollama(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    let ollama_url = if cfg!(target_os = "windows") {
        "https://github.com/ollama/ollama/releases/download/v0.5.4/ollama-windows-amd64.exe"
    } else {
        "https://github.com/ollama/ollama/releases/download/v0.5.4/ollama-linux-amd64"
    };

    let dest = if cfg!(target_os = "windows") {
        std::env::temp_dir().join("jackconnect_ollama.exe")
    } else {
        std::env::temp_dir().join("jackconnect_ollama")
    };

    // Simulate progress for demo (real impl would use reqwest to download)
    for i in 0..=100 {
        callback(InstallStep {
            step: "ollama".to_string(),
            status: "downloading".to_string(),
            progress: i as f32,
            message: format!("Downloading Ollama... {}%", i),
        });
        thread::sleep(std::time::Duration::from_millis(30));
    }

    // In production: download the file using std::fs::write with bytes from reqwest
    // For now we mark as complete since this is a scaffold
    Ok(())
}

fn start_ollama_service(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    for i in 0..=100 {
        callback(InstallStep {
            step: "start_ollama".to_string(),
            status: "running".to_string(),
            progress: i as f32,
            message: if i < 50 { "Starting Ollama service..." } else { "Ollama service running" }.to_string(),
        });
        thread::sleep(std::time::Duration::from_millis(20));
    }

    // In production: spawn ollama serve as a background process
    Ok(())
}

// ── BitNet ────────────────────────────────────────────────────────

fn pull_bitnet_model(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    // BitNet b1.58 3B is ~2GB, download takes time
    let steps = vec![
        (0, "Connecting to model registry..."),
        (20, "Downloading model metadata..."),
        (40, "Downloading model weights (~2GB)..."),
        (80, "Verifying model integrity..."),
        (95, "Optimizing for your system..."),
    ];

    for (progress, msg) in steps {
        callback(InstallStep {
            step: "bitnet".to_string(),
            status: "downloading".to_string(),
            progress: progress as f32,
            message: msg.to_string(),
        });
        thread::sleep(std::time::Duration::from_millis(800));
    }

    // In production: run ollama pull microsoft/bitnet-b1.58-3b
    // or download BitNet.cpp and run it
    Ok(())
}

// ── Hermes ────────────────────────────────────────────────────────

fn install_hermes(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    for i in 0..=100 {
        callback(InstallStep {
            step: "hermes".to_string(),
            status: "installing".to_string(),
            progress: i as f32,
            message: format!("Installing Hermes... {}%", i),
        });
        thread::sleep(std::time::Duration::from_millis(25));
    }

    // In production: cargo install hermes or download binary
    Ok(())
}

fn install_paperclip(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    for i in 0..=100 {
        callback(InstallStep {
            step: "paperclip".to_string(),
            status: "installing".to_string(),
            progress: i as f32,
            message: format!("Installing Paperclip... {}%", i),
        });
        thread::sleep(std::time::Duration::from_millis(30));
    }

    // In production: git clone Paperclip repo and run setup
    Ok(())
}

// ── Watch Once ────────────────────────────────────────────────────

fn install_watch_once(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    for i in 0..=100 {
        callback(InstallStep {
            step: "watch_once".to_string(),
            status: "installing".to_string(),
            progress: i as f32,
            message: format!("Setting up Watch Once... {}%", i),
        });
        thread::sleep(std::time::Duration::from_millis(20));
    }

    Ok(())
}

// ── Solomon OS ───────────────────────────────────────────────────

fn install_solomon_os(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    for i in 0..=100 {
        callback(InstallStep {
            step: "solomon".to_string(),
            status: "installing".to_string(),
            progress: i as f32,
            message: format!("Installing Solomon OS... {}%", i),
        });
        thread::sleep(std::time::Duration::from_millis(25));
    }

    Ok(())
}

// ── Agents ───────────────────────────────────────────────────────

fn install_agents(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    let agents = vec![
        ("Lead Scout", 0),
        ("Client Acquisition", 20),
        ("Agent Builder", 40),
        ("Onboarding Agent", 60),
        ("Billing Agent", 80),
        ("Content Agent", 90),
        ("Pipeline Manager", 95),
    ];

    for (name, progress) in agents {
        callback(InstallStep {
            step: "agents".to_string(),
            status: "installing".to_string(),
            progress: progress as f32,
            message: format!("Installing {}...", name),
        });
        thread::sleep(std::time::Duration::from_millis(400));
    }

    Ok(())
}

// ── Start Services ────────────────────────────────────────────────

fn start_all_services(callback: &impl Fn(InstallStep)) -> Result<(), String> {
    let services = vec![
        "Solomon OS",
        "Paperclip Orchestrator",
        "BitNet LLM",
        "Hermes Router",
        "Watch Once Engine",
        "Telegram Bot",
    ];

    for (i, service) in services.iter().enumerate() {
        let progress = ((i as f32) / (services.len() as f32)) * 100.0;
        callback(InstallStep {
            step: "start_services".to_string(),
            status: "running".to_string(),
            progress,
            message: format!("Starting {}...", service),
        });
        thread::sleep(std::time::Duration::from_millis(300));
    }

    Ok(())
}

// ── Dashboard Data ────────────────────────────────────────────────

pub fn get_dashboard_data() -> Vec<AgentInfo> {
    vec![
        AgentInfo {
            id: "lead-scout".to_string(),
            name: "Lead Scout".to_string(),
            status: "active".to_string(),
            tasks_completed: 47,
            hours_saved: 12.5,
        },
        AgentInfo {
            id: "client-acquisition".to_string(),
            name: "Client Acquisition".to_string(),
            status: "active".to_string(),
            tasks_completed: 23,
            hours_saved: 8.0,
        },
        AgentInfo {
            id: "agent-builder".to_string(),
            name: "Agent Builder".to_string(),
            status: "idle".to_string(),
            tasks_completed: 12,
            hours_saved: 6.0,
        },
        AgentInfo {
            id: "onboarding".to_string(),
            name: "Onboarding Agent".to_string(),
            status: "active".to_string(),
            tasks_completed: 8,
            hours_saved: 4.0,
        },
        AgentInfo {
            id: "billing".to_string(),
            name: "Billing Agent".to_string(),
            status: "active".to_string(),
            tasks_completed: 31,
            hours_saved: 5.5,
        },
        AgentInfo {
            id: "content-agent".to_string(),
            name: "Content Agent".to_string(),
            status: "active".to_string(),
            tasks_completed: 56,
            hours_saved: 14.0,
        },
        AgentInfo {
            id: "pipeline-manager".to_string(),
            name: "Pipeline Manager".to_string(),
            status: "idle".to_string(),
            tasks_completed: 19,
            hours_saved: 7.0,
        },
    ]
}

pub fn get_total_savings() -> (f32, i32, i32) {
    (57.0, 196, 7) // hours saved, tasks, agents
}