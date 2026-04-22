# JackConnect Desktop App — SPEC.md
**Version:** 2.0 | 2026-04-22
**Product:** Native Windows Desktop App (Tauri)
**Tagline:** "Your AI team, one click away"

---

## Concept & Vision

No Ubuntu, no WSL2, no terminal. Download one .exe, install, done.
JackConnect is a native Windows desktop app that runs Solomon OS locally — Ollama, Hermes, BitNet, Paperclip, and all 7 agents — without requiring any technical knowledge.

The feeling: "I just installed a whole AI team and I have no idea how it works, but I love that it does."

---

## Design Language

**Aesthetic:** Dark, minimal, premium — like a Bloomberg terminal crossed with a modern SaaS dashboard.
**Colors:**
- Background: #09090b (zinc-950)
- Surface: #18181b (zinc-900)
- Border: #27272a (zinc-800)
- Primary: #10b981 (emerald-500) — energy, action, AI
- Text: #fafafa (white)
- Muted: #71717a (zinc-500)

**Typography:** System font (Inter-like) — clean, no fuss.
**Motion:** Fast, purposeful — spinners are fast (300ms), transitions are snappy.
**Icon style:** Simple emoji or single-char glyphs, not elaborate SVGs.

---

## App Architecture (Tauri + React)

```
JackConnect.exe (native Windows app)
├── Tauri Rust backend (system-level operations)
│   ├── Install Ollama (download + configure)
│   ├── Install Hermes
│   ├── Download BitNet b1.58 model
│   ├── Start background services
│   └── Watch Once screen recorder
├── React frontend (user interface)
│   ├── Install wizard (one-click flow)
│   ├── Agent status dashboard
│   ├── Watch Once recorder UI
│   └── Settings / uninstall
└── Local services (no internet required after install)
    ├── Ollama (LLM inference)
    ├── Hermes (agent executor)
    └── Paperclip (orchestration)
```

**Connectivity:** After install, app connects to user's Zo Space dashboard via HTTPS (for reporting, sync, updates).

---

## Install Flow (One Click)

Step 1: User clicks "Install JackConnect"
Step 2: App shows progress log in real-time:
```
Downloading Ollama... [████░░░░░░░] 45%
Installing Ollama... 
Downloading Hermes...
Installing Hermes...
Downloading BitNet model (1.2GB)...
Configuring your AI team...
Connecting to dashboard...
✅ Done!
```
Step 3: Desktop shortcut created automatically
Step 4: App opens dashboard view

---

## Dashboard View (Post-Install)

**Sidebar:**
- 🏠 Overview
- 🤖 Agents
- 🎬 Watch Once
- 📊 Time Saved
- ⚙️ Settings

**Main areas:**
- Agent cards with status (active/idle/error)
- Quick actions: /scout, /brief, /pipeline
- Time saved counter (hours this week)
- Recent tasks completed

---

## Watch Once Feature

- "Learn Mode" button in app — turns on screen recorder
- User does task once manually
- App captures: clicks, keystrokes, app context
- Preview shows: step 1, step 2, step 3...
- User approves → skill created → runs on schedule

---

## System Tray (Always Running)

JackConnect runs in the system tray after install:
- Green dot = all agents running
- Yellow dot = something needs attention
- Right-click menu:
  - Open Dashboard
  - Start Watch Once
  - Pause All
  - Settings
  - Quit

---

## Build Output

- `JackConnect_x.x.x_x64-setup.exe` — NSIS installer
- ~100-150MB (Ollama + Hermes + BitNet bundled)
- Runs on Windows 10/11, no admin required (app itself)

---

## Files in This Project

```
desktop-app/
├── SPEC.md                    ← This file
├── package.json               ← npm deps
├── index.html                 ← Entry point
├── src/
│   ├── main.tsx               ← React entry
│   ├── App.tsx                ← Main UI
│   └── styles/               ← Tailwind (CDN)
├── src-tauri/
│   ├── tauri.conf.json        ← Tauri config
│   ├── Cargo.toml             ← Rust deps
│   └── src/
│       ├── main.rs            ← Rust commands
│       └── install.rs         ← Installation logic
└── README.md                  ← Install instructions
```

---

## Status

✅ SPEC written
🔧 Frontend scaffolded (React + Tailwind CDN)
🔧 Tauri config done
⬜ Rust install logic (real implementation)
⬜ Icon assets
⬜ Build + test

*Last updated: April 22, 2026*