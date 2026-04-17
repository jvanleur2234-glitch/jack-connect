#!/usr/bin/env python3
"""
CloudBrowser API — Hyperbrowser equivalent for JackConnect
Playwright browser + Ollama AI = AI-controlled cloud browser.

Usage:
    python3 server.py [--port 9876]

API:
    POST /session              Create browser session
    GET  /session/<id>        Get session info
    DELETE /session/<id>       Close session
    POST /task/<id>           Submit task (runs AI + browser)
    GET  /task/<id>           Get task result
    GET  /screenshot/<id>     Get screenshot path
    GET  /health              Health check
"""
import os, uuid, json, time, threading, asyncio
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get("CLOUDBROWSER_PORT", "9876"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")
STORAGE = os.environ.get("CLOUDBROWSER_STORAGE", "/tmp/cloudbrowser-sessions")

os.makedirs(STORAGE, exist_ok=True)

# ── State ──────────────────────────────────────────────────────────────────
sessions, sessions_lock = {}, threading.Lock()

def new_id(p="cb"): return f"{p}_{uuid.uuid4().hex[:12]}"

def set_result(sid, data):
    # File-based so threads can write and main thread can read
    with open(f"{STORAGE}/{sid}_result.json", "w") as f:
        json.dump(data, f)

def get_result(sid):
    p = f"{STORAGE}/{sid}_result.json"
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return {"status": "pending"}

def load_history(sid):
    p = f"{STORAGE}/{sid}_history.json"
    return json.load(open(p)) if os.path.exists(p) else []

def save_history(sid, msgs):
    with open(f"{STORAGE}/{sid}_history.json", "w") as f: json.dump(msgs, f)

# ── Ollama Direct ───────────────────────────────────────────────────────────
def ollama_chat(model, messages, timeout=120):
    """Call Ollama chat API directly. Returns response text."""
    import urllib.request, urllib.error
    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 512}
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
            return data["message"]["content"]
    except Exception as e:
        return f"[Ollama error: {e}]"

def build_system_prompt():
    return (
        "You are a browser automation assistant. You control a web browser using Playwright. "
        "For each task: 1) decide the URL and actions needed, 2) output a JSON plan, "
        "3) after browser actions, report what you found. "
        "Use this format for your response:\n"
        '{"plan": [{"action": "goto|click|type|screenshot|wait", "url":"...", "selector":"...", "text":"..."}], "goal": "what you want to accomplish"}'
    )

# ── Browser Runner ──────────────────────────────────────────────────────────
def run_browser_task(sid, task_text, headless=True):
    """Run browser automation + AI reasoning."""
    try:
        from playwright.sync_api import sync_playwright

        history = load_history(sid)
        msgs = [{"role": "system", "content": build_system_prompt()}]
        for m in history[-6:]:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": task_text})

        # Ask Ollama for a plan
        plan_text = ollama_chat(OLLAMA_MODEL, msgs)
        save_history(sid, history + [{"role": "user", "content": task_text}, {"role": "assistant", "content": plan_text}])

        try:
            plan = json.loads(plan_text)
        except (json.JSONDecodeError, TypeError):
            plan = {"plan": [{"action": "goto", "url": "https://example.com"}], "goal": plan_text[:100]}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            screenshots = []

            for step in plan.get("plan", []):
                action = step.get("action", "")
                url = step.get("url", "")
                selector = step.get("selector", "")
                text = step.get("text", "")

                if action == "goto" and url:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                elif action == "click" and selector:
                    page.click(selector, timeout=10000)
                elif action == "type" and selector and text:
                    page.fill(selector, text, timeout=10000)
                elif action == "screenshot":
                    ss_path = f"{STORAGE}/screenshots/{sid}_{int(time.time())}.png"
                    page.screenshot(path=ss_path)
                    screenshots.append(ss_path)

            page.wait_for_timeout(1000)
            content = page.content()
            title = page.title()
            body_text = page.inner_text("body")[:500] if page.query_selector("body") else ""
            browser.close()

        result_text = f"Title: {title}\n\nContent preview:\n{body_text[:300]}"
        if screenshots:
            result_text += f"\n\nScreenshots saved: {len(screenshots)}"

        set_result(sid, {"status": "done", "result": result_text, "error": None, "screenshots": screenshots})
        save_history(sid, load_history(sid) + [{"role": "assistant", "content": result_text}])

    except Exception as e:
        import traceback; traceback.print_exc()
        set_result(sid, {"status": "failed", "result": None, "error": str(e)})

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    with sessions_lock: return jsonify({"status": "ok", "sessions": len(sessions)})

@app.route("/session", methods=["POST"])
def create_session():
    data = request.get_json() or {}
    sid = new_id()
    cfg = {"headless": data.get("headless", True)}
    with sessions_lock: sessions[sid] = {"status": "ready", "config": cfg, "created_at": time.time()}
    return jsonify({"session_id": sid, "status": "ready", "config": cfg})

@app.route("/sessions")
def list_sessions():
    with sessions_lock: return jsonify([{"id": k, **v} for k, v in sessions.items()])

@app.route("/session/<sid>", methods=["GET", "DELETE"])
def manage_session(sid):
    with sessions_lock:
        if sid not in sessions: return jsonify({"error": "Session not found"}), 404
        if request.method == "DELETE": del sessions[sid]; return jsonify({"status": "deleted"})
        return jsonify(sessions[sid])

@app.route("/task/<sid>", methods=["GET", "POST"])
def handle_task(sid):
    with sessions_lock:
        if sid not in sessions: return jsonify({"error": "Session not found"}), 404
        if request.method == "GET":
            res = get_result(sid)
            return jsonify({"id": sid, "status": sessions[sid].get("status", "unknown"), **res})
        data = request.get_json() or {}
        task_text = data.get("task")
        if not task_text: return jsonify({"error": "task required"}), 400
        sessions[sid]["status"] = "running"
        cfg = sessions[sid]["config"]

    tid = new_id("task")
    t = threading.Thread(target=run_browser_task, args=(sid, task_text, cfg.get("headless", True)), daemon=True)
    t.start()
    return jsonify({"task_id": tid, "session_id": sid, "status": "running"})

@app.route("/screenshot/<sid>")
def screenshot(sid):
    import glob
    files = sorted(glob.glob(f"{STORAGE}/screenshots/{sid}_*.png"))
    return jsonify({"screenshots": files, "latest": files[-1] if files else None})

@app.route("/download/<sid>/screenshot/<int:idx>")
def download_screenshot(sid, idx):
    import glob
    files = sorted(glob.glob(f"{STORAGE}/screenshots/{sid}_*.png"))
    if idx < 0 or idx >= len(files): return jsonify({"error": "Not found"}), 404
    return send_file(files[idx], mimetype="image/png")

if __name__ == "__main__":
    print(f"CloudBrowser running on port {PORT}")
    print(f"  Ollama: {OLLAMA_URL} ({OLLAMA_MODEL})")
    print(f"  Storage: {STORAGE}")
    print(f"  Routes:")
    print(f"    POST   /session        — create browser session")
    print(f"    POST   /task/<sid>     — submit browser task")
    print(f"    GET    /task/<sid>     — get result")
    print(f"    GET    /screenshot/<sid> — list screenshots")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
