# Solomon Companion — SPEC.md

**The AI companion that watches once and automates forever.**

Cross-platform desktop app (Mac/Windows/Linux) + mobile (iOS/Android) that:
1. Captures your screen with one hotkey
2. Sends screenshot to local AI (Ollama)
3. AI analyzes what you did and asks: "Want me to automate this?"
4. If yes → skill auto-created → Russell Tuna learns it

**100% free + open source stack:**
- LLM: Ollama (local, free)
- STT: Whisper (faster-whisper, local, free)
- TTS: Piper TTS (local, free)
- Screen capture: native OS tools
- Desktop: Tauri (Rust)
- Mobile: native wrappers

## Stack

| Layer | Tech | Cost |
|------|------|------|
| LLM | Ollama + qwen3:1.7b | Free |
| STT | faster-whisper | Free |
| TTS | Piper TTS (amy voice) | Free |
| Screen capture | MSS (Win), ScreenCaptureKit (Mac), MSS on Linux | Free |
| Desktop | Tauri | Free |
| Backend | Solomon OS | Free |
| Push notifications | Solomon OS (Telegram) | Free |

## Core Features

### 1. Watch Once Capture
- Global hotkey (ctrl+shift+w / cmd+shift+w)
- Captures active window or full screen
- Sends screenshot + transcript to Ollama
- Ollama analyzes action → offers to automate

### 2. Voice Input
- Push-to-talk with Whisper transcription
- No cloud API calls
- Works offline after first run

### 3. Voice Output
- Piper TTS with local voice synthesis
- No ElevenLabs dependency
- Fast local inference

### 4. Automation Engine
- Watch Once engine analyzes captured actions
- Creates Hermes skill on approval
- Russell Tuna executes automation going forward
- Learning loop: every action → potential automation

### 5. Cross-Platform Install
- One-click install for Mac (.dmg), Windows (.exe), Linux (.AppImage)
- Native iOS/Android apps via Capacitor
- Auto-connects to Solomon OS on same network

## Screens

### Setup Screen
- Connect to Solomon OS (enter server URL)
- Test microphone
- Set hotkey
- "You're ready"

### Main Companion
- Minimal floating circle (bottom-right corner)
- Tap to talk / hotkey to capture
- Subtle pulse when listening

### Automation Prompt
- "I noticed you just [action]. Want me to automate this?"
- [Yes → automate] [No] [Tell me more]
- Shows what will be automated

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│  SOLOMON COMPANION (Desktop/Mobile)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │ Screen   │ │ Whisper  │ │  Piper   │             │
│  │ Capture  │ │  (STT)   │ │  (TTS)   │             │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘             │
│       │            │            │                     │
│       └────────────┼────────────┘                     │
│                    │                                 │
│              ┌─────▼─────┐                           │
│              │  Ollama   │                           │
│              │ qwen3:1.7b│                          │
│              └─────┬─────┘                           │
│                    │                                 │
│              ┌─────▼─────┐                           │
│              │ Watch Once │                          │
│              │  Engine   │                            │
│              └─────┬─────┘                           │
└────────────────────┼─────────────────────────────────┘
                     │ (local network or internet)
              ┌─────▼─────┐
              │ Solomon OS │
              │  (Zo)     │
              │ Port 5000 │
              └───────────┘
```

## File Structure

```
solomon-companion/
├── SPEC.md
├── Cargo.toml           # Tauri desktop
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── src/
│       ├── main.rs
│       ├── capture.rs   # Screen capture
│       └── hotkey.rs    # Global hotkey
├── src/                 # Frontend (React/Svelte)
│   ├── main.ts
│   ├── App.svelte
│   └── lib/
│       ├── Whisper.svelte  # Voice input
│       ├── Capture.svelte  # Screen capture
│       └── Ollama.svelte   # LLM client
├── src-mobile/          # Capacitor mobile
│   ├── ios/
│   └── android/
└── scripts/
    ├── build-desktop.sh
    └── build-mobile.sh
```

## Build Targets

- macOS 12+ (.dmg, Apple Silicon + Intel)
- Windows 10+ (.exe installer)
- Linux (.AppImage)
- iOS 15+ (App Store + TestFlight)
- Android 7+ (APK + Play Store)

## Security

- All processing local (no cloud for AI)
- API keys never leave user's machine
- Solomon OS connection via HTTPS when remote
- User must approve every automation

## Comparison vs Clicky

| Feature | Clicky | Solomon Companion |
|---------|--------|-------------------|
| macOS only | ✅ | ✅ (Mac/Windows/Linux/iOS/Android) |
| Cloud APIs | AssemblyAI + ElevenLabs | Free + local only |
| Cloudflare Worker | Required | Not needed |
| API cost | ~$50/mo | $0 |
| Automation learning | No | ✅ |
| Solomon OS integration | Webhook only | Native |
| Open source | ❌ | ✅ |