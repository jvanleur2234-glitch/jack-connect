#!/usr/bin/env python3
"""
Solomon Companion Core — local AI companion
100% free + open source: Ollama + Whisper + Piper TTS + MSS
"""
import os, sys, json, base64, time, subprocess, threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import urllib.request

# ── Config ──────────────────────────────────────────
SOLOMON_OS_URL = os.environ.get("SOLOMON_OS_URL", "http://localhost:5000")
OLLAMA_URL    = os.environ.get("OLLAMA_URL", "http://localhost:11434")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "Systran/faster-whisper-tiny")
PIPER_VOICE   = os.environ.get("PIPER_VOICE", "~/.local/share/piper/voices/amy.onnx")

# ── Screen Capture ─────────────────────────────────
def capture_screen():
    """Cross-platform screen capture returning PNG bytes."""
    try:
        import mss
        with mss.mss() as s:
            monitor = s.monitors[1]
            screenshot = s.grab(monitor)
            return mss.tools.to_png(screenshot.rgb, screenshot.size)
    except Exception as e:
        return None, str(e)

# ── Whisper STT ───────────────────────────────────
def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using faster-whisper (local, free)."""
    import faster_whisper
    import tempfile

    # Write audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        model = faster_whisper.load_model(WHISPER_MODEL, device="cpu")
        segments, _ = model.transcribe(temp_path, vad_filter=True)
        return " ".join(seg.text for seg in segments)
    except Exception as e:
        return f"[STT error: {e}]"
    finally:
        os.unlink(temp_path)

# ── Ollama LLM ────────────────────────────────────
def ollama_chat(messages: list, model: str = "llama3.2:1b",
                stream: bool = False) -> str:
    """Call Ollama for chat completion (local, free)."""
    # Use Ollama native /api/chat endpoint
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["message"]["content"]
    except Exception as e:
        # Fallback: try collecting streaming response
        return f"[Ollama error: {e}]"

# ── Piper TTS ─────────────────────────────────────
def piper_speak(text: str, output_path: str = "/tmp/piper_output.wav") -> str:
    """Synthesize speech using Piper TTS (local, free)."""
    voice = Path(PIPER_VOICE).expanduser()
    if not voice.exists():
        return f"[Piper voice not found at {voice}]"

    #piper --model ~/.local/share/piper/voices/amy.onnx --output_file /tmp/out.wav <<< "Hello"
    result = subprocess.run(
        ["piper", "--model", str(voice), "--output_file", output_path],
        input=text.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return f"[Piper error: {result.stderr.decode()[:200]}]"
    return output_path

# ── Watch Once Engine ─────────────────────────────
def analyze_action(screenshot_bytes: bytes, transcript: str = "") -> dict:
    """Use Ollama to analyze what action was taken and if it can be automated."""
    import base64

    # Encode screenshot
    img_b64 = base64.b64encode(screenshot_bytes).decode()

    system_prompt = """You are the Watch Once automation engine. A user just performed an action on their screen.

Analyze what they did and determine:
1. What action did they perform?
2. Is this something that could be automated?
3. What would the automation look like?

Respond ONLY in this JSON format:
{
  "action_description": "brief description of what they did",
  "can_automate": true or false,
  "automation_steps": ["step 1", "step 2"],
  "confidence": 0.0 to 1.0,
  "suggested_skill_name": " kebab-case-name-for-skill"
}

Be specific. If they sent an email, include the subject line they used. If they clicked through a menu, name each step."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Screenshot available: {img_b64[:200]}... (truncated)\nTranscript: {transcript}"}
    ]

    try:
        response = ollama_chat(messages)
        # Try to parse as JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "action_description": response[:200],
                "can_automate": False,
                "automation_steps": [],
                "confidence": 0.5,
                "suggested_skill_name": "unknown"
            }
    except Exception as e:
        return {"error": str(e)}

# ── Solomon OS API ────────────────────────────────
def notify_solomon(event: str, data: dict) -> bool:
    """Send event to Solomon OS Watch Once API."""
    try:
        payload = json.dumps({"event": event, **data}).encode()
        req = urllib.request.Request(
            f"{SOLOMON_OS_URL}/watch-once/event",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        return False

def send_screenshot_to_solomon(screenshot_bytes: bytes, analysis: dict) -> bool:
    """Upload screenshot + analysis to Solomon OS for skill creation."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(screenshot_bytes)
        temp_path = f.name

    try:
        with open(temp_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        payload = json.dumps({
            "screenshot": img_b64,
            "analysis": analysis,
            "action": "offer_automation",
        }).encode()

        req = urllib.request.Request(
            f"{SOLOMON_OS_URL}/watch-once/capture",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30):
            return True
    except Exception as e:
        return False
    finally:
        os.unlink(temp_path)

# ── Upgrade Advisor ───────────────────────────────
UPGRADE_TIERS = [
    {
        "name": "Solo (Free)",
        "models": {"llm": "qwen3:1.7b", "stt": "Systran/faster-whisper-tiny", "tts": "piper-amy"},
        "cost": 0,
        "good_for": "Learning, testing, single-agent tasks",
        "limits": "Slow for long documents, limited context window"
    },
    {
        "name": "Pro ($30/mo)",
        "models": {"llm": "qwen3:14b", "stt": "Systran/faster-whisper-small", "tts": "elevenlabs-amy"},
        "cost": 30,
        "good_for": "Small teams, 5-10 tasks/day, real estate agent workflows",
        "limits": "Good for most SMB workflows"
    },
    {
        "name": "Business ($100/mo)",
        "models": {"llm": "qwen3:32b", "stt": "Systran/faster-whisper-medium", "tts": "elevenlabs-amy"},
        "cost": 100,
        "good_for": "Growing teams, 20-50 tasks/day, multiple clients",
        "limits": "Handles complex multi-step workflows"
    },
    {
        "name": "Enterprise (Custom)",
        "models": {"llm": "claude-sonnet-4", "stt": "AssemblyAI", "tts": "elevenlabs"},
        "cost": 0,  # custom pricing
        "good_for": "Large teams, mission-critical workflows, compliance required",
        "limits": "Unlimited scale, dedicated support"
    }
]

def explain_upgrade_for_user(user_type: str, current_tier: str = "Solo") -> dict:
    """Generate a personalized upgrade explanation for any user type."""
    prompt = f"""A {user_type} is using Solomon OS on the free tier. Based on their business type, explain:
1. What upgraded models would do for them specifically
2. Which tier makes sense and why
3. What specific tasks would improve
4. What the upgrade experience would be like (one command / superintendent asks)

Be concrete with examples relevant to their business type. Keep it to 3-4 short paragraphs."""

    messages = [{"role": "user", "content": prompt}]
    explanation = ollama_chat(messages)
    return explanation

def get_recommended_tier(user_type: str, tasks_per_day: int, budget: str = "any") -> dict:
    """Recommend the right tier based on user profile."""
    tier = "Solo"
    if tasks_per_day > 50 or budget == "unlimited":
        tier = "Enterprise"
    elif tasks_per_day > 20 or budget == "medium":
        tier = "Business"
    elif tasks_per_day > 5:
        tier = "Pro"

    rec = next(t for t in UPGRADE_TIERS if t["name"].startswith(tier.split()[0]))
    return rec

def generate_upgrade_script(from_tier: str, to_tier: str) -> str:
    """Generate the installation script for an upgrade."""
    # This would be generated dynamically based on the tier
    if to_tier == "Pro":
        return """# Upgrade to Pro - one command:
curl -sSL https://solomon.os/install | bash -s pro

# What this does:
# 1. Downloads qwen3:14b (~9GB, 10 min)
# 2. Installs faster-whisper-small model
# 3. Configures local TTS with Piper
# 4. Restarts Solomon Companion with new models
# 5. Superintendent asks: "Ready to upgrade your AI team?"
"""
    elif to_tier == "Business":
        return """# Upgrade to Business — one command:
curl -sSL https://solomon.os/install | bash -s business

# What this does:
# 1. Downloads qwen3:32b (~18GB, 20 min)
# 2. Installs faster-whisper-medium model
# 3. Sets up multi-agent coordination
# 4. Configures Ollama with GPU acceleration
# 5. Superintendent asks: "Ready to scale your AI team?" """
    elif to_tier == "Enterprise":
        return """# Upgrade to Enterprise — custom setup:
curl -sSL https://solomon.os/install | bash -s enterprise

# What this does:
# 1. Sets up Claude API with your key
# 2. Configures AssemblyAI for production STT
# 3. Sets up multi-tenant infrastructure
# 4. Dedicated Slack/Teams support channel
# 5. Monthly check-in with your AI team"""

    return "# Same tier — no upgrade needed!"

# ── HTTP API Server ──────────────────────────────
class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif self.path == "/capabilities":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            caps = {
                "llm": "ollama qwen3:1.7b",
                "stt": "faster-whisper Systran/faster-whisper-tiny",
                "tts": "piper TTS amy",
                "screen_capture": "mss",
                "automation": "watch-once engine",
                "solomon_os": SOLOMON_OS_URL,
            }
            self.wfile.write(json.dumps(caps).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)

        if self.path == "/capture":
            # Screen capture + analysis
            screenshot = capture_screen()
            if isinstance(screenshot, tuple):
                screenshot, err = screenshot
                self.send_error(500, err)
                return

            analysis = analyze_action(screenshot)
            solomon_ok = send_screenshot_to_solomon(screenshot, analysis)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "analysis": analysis,
                "solomon_synced": solomon_ok
            }).encode())

        elif self.path == "/chat":
            data = json.loads(body)
            messages = data.get("messages", [])
            response = ollama_chat(messages)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}).encode())

        elif self.path == "/speak":
            data = json.loads(body)
            text = data.get("text", "")
            output_path = piper_speak(text)

            if output_path.startswith("/"):
                with open(output_path, "rb") as f:
                    audio_bytes = f.read()
                os.unlink(output_path)

                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", len(audio_bytes))
                self.end_headers()
                self.wfile.write(audio_bytes)
            else:
                self.send_error(500, output_path)

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[SolomonCore] {format % args}")

def run_server(port: int = 7890):
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"[SolomonCore] Running on http://0.0.0.0:{port}")
    print(f"[SolomonCore] LLM: {OLLAMA_URL} | Solomon OS: {SOLOMON_OS_URL}")
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7890
    run_server(port)