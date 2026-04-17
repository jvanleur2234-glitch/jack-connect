#!/usr/bin/env python3
"""
Watch Once API Server — JackConnect
====================================
Flask server that receives captures from Clicky Worker and creates automated skills.

Routes:
- POST /watch-once — receives capture, analyzes, creates skill
- POST /approve/<capture_id> — approves a pending capture
- GET /skills — list all Watch Once skills
- GET /pending — list pending captures
"""

import json, os, time, uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Paths
VAULT_PATH = Path("/home/workspace/solomon-vault")
WATCH_ONCE_PATH = VAULT_PATH / "raw" / "watch-once"
SKILLS_PATH = Path("/home/workspace/hermes-skills")

WATCH_ONCE_PATH.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://localhost:11434"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

JACK_CHAT_ID = os.environ.get("JACK_CHAT_ID", "")  # Set this after first Telegram message

# ──────────────────────────────────────────────────────────────
# CORE LOGIC
# ──────────────────────────────────────────────────────────────

def analyze_with_ollama(screen_data, voice_transcript, task_context=""):
    """Use Ollama to figure out what task Jack did and how to automate it."""
    prompt = f"""You are helping automate a real estate agent's work. 

Jack (real estate agent) just did a task manually. Here's what he said about it:

Voice explanation: "{voice_transcript}"
Context: {task_context}

Figure out:
1. TASK NAME — short, descriptive (e.g. "Send new lead follow-up text")
2. TRIGGER — when should this run automatically? (e.g. "When a new lead scores 8+")
3. STEPS — numbered list of what he did, written as automation instructions
4. CHANNEL — how should Jack be notified? (telegram/sms/email)
5. PRIORITY — is this HIGH (directly affects closing a deal) or standard?

Return ONLY valid JSON, no markdown, no explanation:
{{"task_name": "...", "trigger": "...", "steps": ["step 1", "step 2"], "channel": "telegram", "high_priority": true}}"""

    try:
        import requests
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "qwen3:1.7b", "prompt": prompt, "stream": False},
            timeout=90
        )
        if resp.ok:
            text = resp.json().get("response", "{}").strip()
            # Try to extract JSON from response
            if "{" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                return json.loads(text[start:end])
    except Exception as e:
        print(f"Ollama analysis error: {e}")
    
    return None

def create_skill_from_task(task_info, capture_id):
    """Save as a Hermes skill that Russell Tuna can execute."""
    task_name = task_info.get("task_name", "unknown")
    safe_name = f"watch-{task_name.lower().replace(' ', '-').replace('/', '-')[:45]}"
    
    skill_dir = SKILLS_PATH / safe_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Skill markdown
    skill_md = f"""---
name: {safe_name}
description: >
  Auto-learned from Jack's manual action on {datetime.now().strftime('%Y-%m-%d')}.
  Trigger: {task_info.get('trigger', 'manual')}
  Source: Watch Once capture {capture_id}
compatibility: JackConnect / Solomon OS
metadata:
  author: watch-once
  version: 1.0
  created: {datetime.now().isoformat()}
  capture_id: {capture_id}
allowed-tools: Bash,Read,Write,WebSearch
---

# {task_name}

## Source
Learned from Jack's manual action via Watch Once protocol.

## Trigger
{task_info.get('trigger', 'Manual activation only')}

## What It Does
This skill automates: {task_name}

## Execution Steps
"""
    for i, step in enumerate(task_info.get("steps", []), 1):
        skill_md += f"{i}. {step}\n"
    
    skill_md += f"""
## Notification
Russell Tuna notifies Jack via: {task_info.get('channel', 'telegram')}

## Priority
{'🔥 HIGH PRIORITY — affects deal closing' if task_info.get('high_priority') else 'Standard automation'}

## Notes
- Source capture: {capture_id}
- Learned via Watch Once / Clicky integration
- Refine anytime by telling Russell Tuna
"""

    with open(skill_dir / "SKILL.md", "w") as f:
        f.write(skill_md)
    
    # Also create a Telegram notification skill
    notify_md = f"""---
name: notify-jack-{safe_name[6:]}
description: >
  Notify Jack when {task_name} is completed.
compatibility: Solomon OS
metadata:
  created: {datetime.now().isoformat()}
---

# Notify Jack — {task_name} Complete

When this skill runs, send Jack a Telegram message:
"I just completed: {task_name}. [Summary of what was done]."
"""

    with open(skill_dir / "notify-skill.md", "w") as f:
        f.write(notify_md)
    
    return skill_dir

def notify_jack_telegram(skill_info):
    """Ask Jack via Telegram if he wants to automate this task."""
    if not TELEGRAM_BOT_TOKEN:
        print("No Telegram token - simulate notification")
        return {"simulated": True}
    
    try:
        import requests
        task_name = skill_info.get("task_name", "this task")
        msg = f"🤖 *Watch Once*\n\nI noticed you: *{task_name}*\n\nI can automate this for you. Reply YES to enable, NO to skip."
        
        if JACK_CHAT_ID:
            r = requests.post(
                f"https://api.telegram.org/{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": JACK_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            return r.json()
    except Exception as e:
        print(f"Telegram error: {e}")
    
    return {"error": "notification failed"}

# ──────────────────────────────────────────────────────────────
# API ROUTES
# ──────────────────────────────────────────────────────────────

@app.route("/watch-once", methods=["POST"])
def receive_capture():
    """Receive a capture from Clicky Worker (forwarded from Clicky macOS app)."""
    try:
        payload = request.json
        capture_id = f"wc-{uuid.uuid4().hex[:8]}"
        
        screen_data = payload.get("screen_data", "")
        voice_transcript = payload.get("voice_transcript", "")
        context = payload.get("context", "")
        user_id = payload.get("user_id", "jack")
        
        # Save raw capture
        capture_file = WATCH_ONCE_PATH / f"pending-{capture_id}.json"
        with open(capture_file, "w") as f:
            json.dump({
                "capture_id": capture_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "screen_data": screen_data[:500] if screen_data else "",  # Just store transcript, not full screen
                "voice_transcript": voice_transcript,
                "context": context,
                "status": "pending"
            }, f, indent=2)
        
        # Analyze with Ollama
        task_info = analyze_with_ollama(screen_data, voice_transcript, context)
        
        if task_info:
            # Ask Jack if he wants to automate
            notify_jack_telegram(task_info)
            
            return jsonify({
                "capture_id": capture_id,
                "status": "analyzed",
                "task_found": task_info.get("task_name"),
                "message": f"Got it. I see you did: {task_info.get('task_name', 'something')}. Want me to automate it?"
            })
        else:
            return jsonify({
                "capture_id": capture_id,
                "status": "received",
                "message": "Capture received. I wasn't sure what that was — want me to try again?"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/approve/<capture_id>", methods=["POST"])
def approve_capture(capture_id):
    """Jack approves a capture → create the automated skill."""
    try:
        capture_file = WATCH_ONCE_PATH / f"pending-{capture_id}.json"
        
        if not capture_file.exists():
            return jsonify({"error": "Capture not found"}), 404
        
        with open(capture_file) as f:
            capture = json.load(f)
        
        # Re-analyze to get fresh task info
        task_info = analyze_with_ollama(
            capture.get("screen_data", ""),
            capture.get("voice_transcript", ""),
            capture.get("context", "")
        )
        
        if not task_info:
            return jsonify({"error": "Analysis failed"}), 500
        
        # Create the skill
        skill_dir = create_skill_from_task(task_info, capture_id)
        
        # Move to approved
        capture_file.rename(WATCH_ONCE_PATH / f"approved-{capture_id}.json")
        
        # Notify Jack
        try:
            import requests
            msg = f"✅ *Automation enabled!*\n\n{task_info.get('task_name')} is now automated. Russell Tuna will handle this going forward."
            if TELEGRAM_BOT_TOKEN and JACK_CHAT_ID:
                requests.post(
                    f"https://api.telegram.org/{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": JACK_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                    timeout=10
                )
        except:
            pass
        
        return jsonify({
            "status": "approved",
            "skill_created": skill_dir.name,
            "task_name": task_info.get("task_name")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/skills", methods=["GET"])
def list_watch_once_skills():
    """List all Watch Once automated skills."""
    skills = []
    for d in SKILLS_PATH.glob("watch-*"):
        if d.is_dir():
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                skills.append({
                    "name": d.name,
                    "created": d.name,
                    "path": str(d)
                })
    return jsonify({"skills": skills, "count": len(skills)})

@app.route("/pending", methods=["GET"])
def list_pending():
    """List pending captures awaiting approval."""
    pending = []
    for f in sorted(WATCH_ONCE_PATH.glob("pending-*.json")):
        with open(f) as fp:
            d = json.load(fp)
            pending.append({
                "capture_id": d.get("capture_id"),
                "timestamp": d.get("timestamp"),
                "voice_transcript": d.get("voice_transcript", "")[:100],
                "context": d.get("context", "")
            })
    return jsonify({"pending": pending, "count": len(pending)})

@app.route("/status", methods=["GET"])
def status():
    """Health check."""
    return jsonify({
        "status": "ok",
        "service": "watch-once-engine",
        "vault": str(VAULT_PATH),
        "skills_path": str(SKILLS_PATH),
        "ollama": OLLAMA_URL
    })

if __name__ == "__main__":
    print("Starting Watch Once API Server...")
    print(f"Vault: {VAULT_PATH}")
    print(f"Skills: {SKILLS_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=False)