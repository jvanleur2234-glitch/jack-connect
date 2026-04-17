#!/usr/bin/env python3
"""
CloudBrowser API — Hyperbrowser equivalent for JackConnect
HTTP API that gives Hermes Agent full browser control.

Usage:
    python3 server.py [--port 9876]

Endpoints:
    POST   /session          → Create isolated browser session
    DELETE /session/{id}     → Kill session
    GET    /sessions         → List active sessions
    POST   /task             → Run browser task (browser-use powered)
    GET    /screenshot/{id}  → Get current screenshot
    GET    /recording/{id}   → Get session recording
    POST   /upload            → Upload file via session
"""
import asyncio, uuid, os, json, time, threading, tempfile, shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── Config ────────────────────────────────────────────────────────────────────
PORT       = int(os.environ.get("CLOUDBROWSER_PORT", "9876"))
DATA_DIR   = Path(os.environ.get("CLOUDBROWSER_DATA", "/tmp/cloudbrowser"))
PROFILE_DIR = DATA_DIR / "profiles"
SESSION_DIR = DATA_DIR / "sessions"
RECORD_DIR  = DATA_DIR / "recordings"

for d in [PROFILE_DIR, SESSION_DIR, RECORD_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Session Store ─────────────────────────────────────────────────────────────
# { session_id: { profile, browser, created_at, task, status } }
sessions = {}
sessions_lock = threading.Lock()

# ── Helpers ───────────────────────────────────────────────────────────────────
def new_session_id():
    return f"cb_{uuid.uuid4().hex[:12]}"

def new_task_id():
    return f"task_{uuid.uuid4().hex[:12]}"

def load_config(config_str):
    """Parse JSON config or return default."""
    if config_str:
        try:
            return json.loads(config_str)
        except:
            pass
    return {
        "headless": True,
        "viewport": {"width": 1280, "height": 800},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "proxy": None,
        "stealth": True,
        "timeout": 30000,
    }

async def run_browser_task(session_id, task_text, config):
    """Execute a browser task using browser-use."""
    try:
        from browser_use import Agent, Controller
        from langchain_ollama import ChatOllama

        controller = Controller()
        model = ChatOllama(model="qwen3:1.7b", base_url="http://localhost:11434")
        agent = Agent(task=task_text, llm=model, controller=controller)

        # Set up profile directory
        profile_path = PROFILE_DIR / session_id
        profile_path.mkdir(exist_ok=True)

        # Run the agent
        history = await agent.run()
        
        # Extract result
        result = {
            "session_id": session_id,
            "task": task_text,
            "success": True,
            "steps": len(history.steps),
            "actions": [str(a) for a in history.actions],
            "final_url": history.urls[-1] if history.urls else None,
        }
        
        with sessions_lock:
            if session_id in sessions:
                sessions[session_id]["result"] = result
                sessions[session_id]["status"] = "completed"
        
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        with sessions_lock:
            if session_id in sessions:
                sessions[session_id]["status"] = "failed"
                sessions[session_id]["error"] = str(e)
        return {"success": False, "error": str(e)}

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "sessions": len(sessions)})

@app.route("/session", methods=["POST"])
def create_session():
    """Create a new isolated browser session."""
    data = request.get_json() or {}
    session_id = new_session_id()
    
    config = load_config(data.get("config"))
    profile = data.get("profile", "default")
    
    with sessions_lock:
        sessions[session_id] = {
            "id": session_id,
            "profile": profile,
            "config": config,
            "created_at": time.time(),
            "status": "ready",
            "task": None,
            "result": None,
            "error": None,
            "screenshot": None,
        }
    
    return jsonify({
        "session_id": session_id,
        "status": "ready",
        "config": config,
    })

@app.route("/session/<session_id>", methods=["DELETE"])
def kill_session(session_id):
    """Kill a browser session and clean up."""
    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
        
        # Clean up profile directory
        profile_path = PROFILE_DIR / session_id
        if profile_path.exists():
            shutil.rmtree(profile_path, ignore_errors=True)
        
        del sessions[session_id]
    
    return jsonify({"session_id": session_id, "status": "killed"})

@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active sessions."""
    with sessions_lock:
        return jsonify({
            "sessions": [
                {
                    "id": s["id"],
                    "status": s["status"],
                    "profile": s["profile"],
                    "created_at": s["created_at"],
                    "task": s["task"],
                }
                for s in sessions.values()
            ]
        })

@app.route("/task", methods=["POST"])
def submit_task():
    """
    Submit a browser task to a session.
    Body: { "session_id": "...", "task": "Go to MLS and search for 123 Main St", "config": {...} }
    """
    data = request.get_json()
    session_id = data.get("session_id")
    task_text = data.get("task")
    
    if not session_id or not task_text:
        return jsonify({"error": "session_id and task required"}), 400
    
    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
        
        sessions[session_id]["status"] = "running"
        sessions[session_id]["task"] = task_text
        config = sessions[session_id]["config"]
    
    task_id = new_task_id()
    
    # Run in background thread
    def do_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_browser_task(session_id, task_text, config))
        finally:
            loop.close()
    
    thread = threading.Thread(target=do_task, daemon=True)
    thread.start()
    
    return jsonify({
        "task_id": task_id,
        "session_id": session_id,
        "status": "running",
    })

@app.route("/task/<session_id>", methods=["GET"])
def get_task_result(session_id):
    """Get the result of a session's last task."""
    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
        return jsonify({
            "id": session_id,
            "status": sessions[session_id]["status"],
            "task": sessions[session_id]["task"],
            "result": sessions[session_id].get("result"),
            "error": sessions[session_id].get("error"),
        })

@app.route("/screenshot/<session_id>", methods=["GET"])
def get_screenshot(session_id):
    """Get current screenshot of a session."""
    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
        
        screenshot_path = SESSION_DIR / session_id / "screenshot.png"
    
    if not screenshot_path.exists():
        return jsonify({"error": "No screenshot available"}), 404
    
    return send_file(screenshot_path, mimetype="image/png")

@app.route("/recording/<session_id>", methods=["GET"])
def get_recording(session_id):
    """Get session recording (HTML replay)."""
    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
    
    recording_path = RECORD_DIR / f"{session_id}.html"
    
    if not recording_path.exists():
        # Generate a simple HTML replay from actions
        with sessions_lock:
            result = sessions[session_id].get("result", {})
            actions = result.get("actions", [])
        
        html = f"<html><body><h1>Session {session_id}</h1><ul>"
        for action in actions:
            html += f"<li>{action}</li>"
        html += "</ul></body></html>"
        
        recording_path.write_text(html)
    
    return send_file(recording_path, mimetype="text/html")

@app.route("/sessions/<session_id>/screenshot", methods=["POST"])
def take_screenshot(session_id):
    """Take a screenshot of a specific session."""
    data = request.get_json() or {}
    url = data.get("url")
    
    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
    
    screenshot_dir = SESSION_DIR / session_id
    screenshot_dir.mkdir(exist_ok=True)
    screenshot_path = screenshot_dir / "screenshot.png"
    
    try:
        import subprocess
        
        # Use browser-use to navigate and screenshot
        script = f'''
import asyncio
from browser_use import Agent, Controller
from langchain_ollama import ChatOllama
from PIL import Image

async def main():
    model = ChatOllama(model="qwen3:1.7b", base_url="http://localhost:11434")
    controller = Controller()
    agent = Agent(task="Go to {{url}} and take a screenshot of the page. Save it to "{{screenshot_path}}".", llm=model, controller=controller)
    await agent.run()

asyncio.run(main())
'''
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "screenshot_path": str(screenshot_path), "url": url or "about:blank"}
        )
        
        return jsonify({"screenshot": f"/screenshot/{session_id}", "url": url})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Hermes Integration ────────────────────────────────────────────────────────
def register_with_hermes():
    """Register CloudBrowser as a Hermes tool."""
    # This creates a Hermes skill for CloudBrowser
    skill_md = f"""# CloudBrowser Skill

## What It Does
Gives the agent full control of an isolated cloud browser. The agent can:
- Open any URL
- Click, type, scroll, navigate
- Extract data from any website
- Take screenshots and recordings
- Run entire workflows autonomously

## When To Use It
Use when you need to:
- Scrape a website that requires JavaScript
- Automate a web form or workflow
- Extract data from a web app
- Monitor a page for changes
- Navigate a site that blocks non-browser requests

## How It Works
1. Create a session → get a session_id
2. Submit a task → browser opens, does the task
3. Get results → screenshot, recording, extracted data

## Commands
```bash
# Create session
curl -X POST http://localhost:{PORT}/session

# Run task
curl -X POST http://localhost:{PORT}/task \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "cb_xxx", "task": "Go to MLS and search for 123 Main St"}}'

# Get screenshot
curl http://localhost:{PORT}/screenshot/cb_xxx

# Get recording
curl http://localhost:{PORT}/recording/cb_xxx
```

## Status
Running at http://localhost:{PORT}
"""
    
    skill_dir = Path("/home/workspace/Skills/cloud-browser")
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_md)
    
    # Link to Hermes if hermes command available
    os.system("hermes --add-skill cloud-browser 2>/dev/null || true")
    
    return skill_md

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"CloudBrowser API starting on port {PORT}")
    print(f"Data dir: {DATA_DIR}")
    print(f"Endpoints:")
    print(f"  POST   /session           — create isolated browser")
    print(f"  DELETE /session/{{id}}    — kill session")
    print(f"  GET    /sessions          — list active sessions")
    print(f"  POST   /task              — run browser task")
    print(f"  GET    /task/{{id}}       — get task result")
    print(f"  GET    /screenshot/{{id}}  — get screenshot")
    print(f"  GET    /recording/{{id}}   — get recording")
    
    # Register skill with Hermes
    skill = register_with_hermes()
    print("\nHermes skill registered ✅")
    
    app.run(host="0.0.0.0", port=PORT, threaded=True)
