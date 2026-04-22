import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

interface AgentInfo {
  id: string;
  name: string;
  status: string;
  tasks_completed: number;
  hours_saved: number;
}

interface InstallProgress {
  step: string;
  status: string;
  progress: number;
  message: string;
}

type Tab = "dashboard" | "agents" | "tasks" | "audit" | "settings";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [isInstalling, setIsInstalling] = useState(false);
  const [installProgress, setInstallProgress] = useState<InstallProgress | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [watchMode, setWatchMode] = useState(false);

  useEffect(() => {
    loadAgents();
    const unlisten = listen<InstallProgress>("install-progress", (event) => {
      setInstallProgress(event.payload);
    });
    return () => { unlisten.then((fn) => fn()); };
  }, []);

  async function loadAgents() {
    try {
      const data = await invoke<AgentInfo[]>("get_agents");
      setAgents(data);
    } catch (e) {
      // fallback mock data
      setAgents([
        { id: "lead-scout", name: "Lead Scout", status: "active", tasks_completed: 47, hours_saved: 12.5 },
        { id: "client-acquisition", name: "Client Acquisition", status: "active", tasks_completed: 23, hours_saved: 8.0 },
        { id: "agent-builder", name: "Agent Builder", status: "idle", tasks_completed: 12, hours_saved: 6.0 },
        { id: "onboarding", name: "Onboarding Agent", status: "active", tasks_completed: 8, hours_saved: 4.0 },
        { id: "billing", name: "Billing Agent", status: "active", tasks_completed: 31, hours_saved: 5.5 },
        { id: "content-agent", name: "Content Agent", status: "active", tasks_completed: 56, hours_saved: 14.0 },
        { id: "pipeline-manager", name: "Pipeline Manager", status: "idle", tasks_completed: 19, hours_saved: 7.0 },
      ]);
    }
  }

  async function handleInstall() {
    setIsInstalling(true);
    setInstallProgress({ step: "starting", status: "starting", progress: 0, message: "Preparing installation..." });
    try {
      await invoke("start_install");
    } catch (e) {
      console.error(e);
      setIsInstalling(false);
    }
  }

  const totalHours = agents.reduce((sum, a) => sum + a.hours_saved, 0);
  const totalTasks = agents.reduce((sum, a) => sum + a.tasks_completed, 0);

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">JackConnect</span>
        </div>
        <nav className="sidebar-nav">
          <button className={`nav-btn ${tab === "dashboard" ? "active" : ""}`} onClick={() => setTab("dashboard")}>
            📊 Dashboard
          </button>
          <button className={`nav-btn ${tab === "agents" ? "active" : ""}`} onClick={() => setTab("agents")}>
            🤖 Agents
          </button>
          <button className={`nav-btn ${tab === "tasks" ? "active" : ""}`} onClick={() => setTab("tasks")}>
            ✅ Tasks
          </button>
          <button className={`nav-btn ${tab === "audit" ? "active" : ""}`} onClick={() => setTab("audit")}>
            📋 Audit Trail
          </button>
          <button className={`nav-btn ${tab === "settings" ? "active" : ""}`} onClick={() => setTab("settings")}>
            ⚙️ Settings
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot online" /> Solomon OS Active
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main">
        {/* Install Screen */}
        {isInstalling && (
          <div className="install-screen">
            <div className="install-card">
              <h2>⚡ Installing JackConnect</h2>
              <p className="install-subtitle">Setting up your AI team...</p>
              <div className="progress-container">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${installProgress?.progress ?? 0}%` }} />
                </div>
                <div className="progress-steps">
                  {[
                    { key: "ollama", label: "Ollama (local AI)" },
                    { key: "bitnet", label: "BitNet Model" },
                    { key: "hermes", label: "Hermes Agent System" },
                    { key: "paperclip", label: "Paperclip Orchestrator" },
                    { key: "watch_once", label: "Watch Once Engine" },
                    { key: "solomon", label: "Solomon OS" },
                    { key: "agents", label: "Your AI Team" },
                    { key: "start_services", label: "Starting Services" },
                  ].map((step) => {
                    const isDone = (installProgress?.step === "complete" || installProgress?.step > step.key)) ?? false;
                    const isActive = installProgress?.step === step.key;
                    return (
                      <div key={step.key} className={`progress-step ${isDone ? "done" : ""} ${isActive ? "active" : ""}`}>
                        {isDone ? "✓" : isActive ? "●" : "○"} {step.label}
                      </div>
                    );
                  })}
                </div>
                <p className="progress-message">{installProgress?.message ?? "Preparing..."}</p>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Tab */}
        {!isInstalling && tab === "dashboard" && (
          <div className="dashboard">
            <header className="dashboard-header">
              <h1>Welcome back</h1>
              <p className="tagline">The AI OS that gives you back your time for the important things</p>
            </header>

            {/* Hero Stats */}
            <div className="hero-stats">
              <div className="stat-card hero">
                <span className="stat-value">{totalHours.toFixed(1)}</span>
                <span className="stat-label">Hours Saved This Month</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{totalTasks}</span>
                <span className="stat-label">Tasks Automated</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{agents.length}</span>
                <span className="stat-label">Active Agents</span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
              <h3>Quick Actions</h3>
              <div className="action-grid">
                <button className="action-btn primary" onClick={() => setTab("agents")}>
                  🤖 View All Agents
                </button>
                <button className="action-btn" onClick={() => setTab("tasks")}>
                  ✅ New Task
                </button>
                <button className="action-btn" onClick={() => setTab("audit")}>
                  📋 Audit Trail
                </button>
                <button className="action-btn" onClick={() => setTab("settings")}>
                  ⚙️ Settings
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="recent-activity">
              <h3>Recent Activity</h3>
              {agents.filter((a) => a.status === "active").slice(0, 3).map((agent) => (
                <div key={agent.id} className="activity-item">
                  <span className="activity-icon">🤖</span>
                  <div className="activity-details">
                    <strong>{agent.name}</strong> completed {agent.tasks_completed} tasks
                  </div>
                  <span className="activity-time">{agent.hours_saved}h saved</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agents Tab */}
        {!isInstalling && tab === "agents" && (
          <div className="tab-content">
            <h2>Your AI Team</h2>
            <div className="agent-grid">
              {agents.map((agent) => (
                <div key={agent.id} className="agent-card">
                  <div className="agent-header">
                    <span className={`status-dot ${agent.status}`} />
                    <h3>{agent.name}</h3>
                  </div>
                  <div className="agent-stats">
                    <div className="agent-stat">
                      <span className="agent-stat-value">{agent.tasks_completed}</span>
                      <span className="agent-stat-label">Tasks</span>
                    </div>
                    <div className="agent-stat">
                      <span className="agent-stat-value">{agent.hours_saved}h</span>
                      <span className="agent-stat-label">Saved</span>
                    </div>
                  </div>
                  <button className="agent-btn">Manage</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tasks Tab */}
        {!isInstalling && tab === "tasks" && (
          <div className="tab-content">
            <h2>Automated Tasks</h2>
            <div className="task-list">
              <div className="task-item">
                <span className="task-check">✅</span>
                <div className="task-info">
                  <strong>Lead Scout completed</strong> — 3 new prospects identified
                </div>
                <span className="task-time">2m ago</span>
              </div>
              <div className="task-item">
                <span className="task-check">✅</span>
                <div className="task-info">
                  <strong>Content Agent completed</strong> — 5 social posts generated
                </div>
                <span className="task-time">15m ago</span>
              </div>
              <div className="task-item">
                <span className="task-check">✅</span>
                <div className="task-info">
                  <strong>Billing Agent completed</strong> — Renewal alert sent to 2 clients
                </div>
                <span className="task-time">1h ago</span>
              </div>
            </div>
          </div>
        )}

        {/* Audit Tab */}
        {!isInstalling && tab === "audit" && (
          <div className="tab-content">
            <h2>Audit Trail</h2>
            <p>Every action your AI team takes is logged here for compliance and review.</p>
            <div className="audit-list">
              <div className="audit-item">
                <span className="audit-time">Today 2:34 PM</span>
                <span className="audit-agent">Content Agent</span>
                <span className="audit-action">Generated 5 social media posts for Maria's Restaurant</span>
              </div>
              <div className="audit-item">
                <span className="audit-time">Today 1:15 PM</span>
                <span className="audit-agent">Lead Scout</span>
                <span className="audit-action">Identified 3 new leads in plumbing vertical</span>
              </div>
              <div className="audit-item">
                <span className="audit-time">Today 11:00 AM</span>
                <span className="audit-agent">Onboarding Agent</span>
                <span className="audit-action">Completed Jack's demo installation</span>
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {!isInstalling && tab === "settings" && (
          <div className="tab-content">
            <h2>Settings</h2>
            <div className="settings-group">
              <h3>AI Model</h3>
              <select className="settings-select">
                <option>BitNet b1.58 (default, fastest)</option>
                <option>Llama 3.2 1B (balanced)</option>
                <option>Qwen 3 1.7B (most capable)</option>
              </select>
            </div>
            <div className="settings-group">
              <h3>Telegram Bot Token</h3>
              <input type="password" placeholder="Enter your Telegram bot token" className="settings-input" />
            </div>
            <div className="settings-group">
              <h3>Solomon OS API Key</h3>
              <input type="password" placeholder="Enter your API key" className="settings-input" />
            </div>
            <div className="settings-group">
              <h3>Vertical</h3>
              <select className="settings-select">
                <option>Real Estate (JackConnect)</option>
                <option>AI Staffing Agency (JCPaid)</option>
                <option>Restaurant</option>
                <option>Plumbing</option>
                <option>Dentistry</option>
                <option>Custom</option>
              </select>
            </div>
            <button className="action-btn primary" onClick={handleInstall}>
              🚀 Reinstall / Update
            </button>
          </div>
        )}
      </main>
    </div>
  );
}