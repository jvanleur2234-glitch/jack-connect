# Bonsai Bridge — Offline Brain for JackConnect

**What it is:** A local Ollama-compatible API that wraps Bonsai 1.7B ONNX via Transformers.js.
JackConnect talks to it like regular Ollama — no code changes needed.

**Why:** When Jack has no internet, Ollama is down, or he's on "airplane mode" — Bonsai keeps working.
100% offline. 100% private. Zero API cost.

## Quick Start

```bash
cd /home/workspace/jack-connect/bonsai-bridge
pip install transformers>=4.1.0 torch onnxruntime
python3 bridge.py
```

Then set in JackConnect:
```bash
export OLLAMA_URL=http://localhost:11434  # normal
# or
export OLLAMA_URL=http://localhost:11435  # Bonsai bridge (offline mode)
```

## Architecture

```
JackConnect core.py
     ↓ (ollama_chat)
OLLAMA_URL (configurable)
     ↓
┌─────────────────────────────────────┐
│  [Ollama qwen3:1.7b]  ← Normal mode │
│  OR                                │
│  [Bonsai Bridge :11435] ← Offline   │
└─────────────────────────────────────┘
```

## Status

- ✅ Bonsai WebGPU live at: https://josephv.zo.space/bonsai
- 🔧 Bridge: in progress (needs ONNX Runtime Python)
