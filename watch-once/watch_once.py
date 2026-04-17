#!/usr/bin/env python3
"""
Watch Once Engine — JackConnect
================================
The "Watch Once, Automate" protocol.

How it works:
1. Jack does a task manually (e.g., sends a follow-up text)
2. Clicky captures the screen + his voice explanation of what he did
3. Watch Once receives this capture, analyzes what happened
4. "I can do this for you automatically. Want me to?"
5. If Jack says yes → task is saved as a new AUTOMATED SKILL
6. Russell Tuna / Superintendent now does it automatically going forward

This is the MOAT. Competitors can copy the AI. They can't copy the learning loop.
"""

import json, os, time
from datetime import datetime
from pathlib import Path

# Storage
VAULT_PATH = Path("/home/workspace/solomon-vault")
WATCH_ONCE_PATH = VAULT_PATH / "raw" / "watch-once"
WATCH_ONCE_PATH.mkdir(parents=True, exist_ok=True)

SKILLS_PATH = Path("/home/workspace/hermes-skills")
JACK_DATA_PATH = Path("/home/workspace/jack-connect/data")

# Ollama for analysis
OLLAMA_URL = "http://localhost:11434"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

def analyze_capture(screen_data, voice_transcript, task_context=""):
    """
    Use Ollama to analyze what Jack just did and figure out:
    1. What was the task?
    2. What steps did he take?
    3. How can we automate it?
    """
    prompt = f"""Analyze this task that Jack (a real estate agent) just did manually.

Voice transcript of what Jack said:
{voice_transcript}

Task context: {task_context}

Based on this, extract:
1. The TASK NAME (short, e.g. "Follow up with hot lead")
2. The TRIGGER (when should this happen automatically? e.g. "When a new lead scores 9/10")
3. The STEPS he took (numbered list of what to automate)
4. The CHANNEL (how does Jack want to be notified? text/email/telegram)
5. Whether this is HIGH PRIORITY (yes if it directly affects closing a deal)

Return as JSON only:
{{"task_name": "...", "trigger": "...", "steps": [...], "channel": "...", "high_priority": true/false}}
"""

    try:
        import requests
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "qwen3:1.7b", "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.ok:
            result = json.loads(response.json().get("response", "{}"))
            return result
    except Exception as e:
        print(f"Analysis error: {e}")
    
    return {"task_name": "Unknown task", "trigger": "", "steps": [], "channel": "telegram", "high_priority": False}

def save_as_automated_skill(task_info, capture_id):
    """
    Save the analyzed task as a Hermes skill so Russell Tuna can execute it.
    """
    task_name = task_info.get("task_name", "unknown-task")
    safe_name = task_name.lower().replace(" ", "-").replace("/", "-")[:50]
    
    skill_dir = SKILLS_PATH / f"watch-once-{safe_name}"
    skill_dir.mkdir(exist_ok=True)
    
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
allowed-tools: Bash,Read,Write
---

# {task_name}

## Source
Learned from Jack's manual action on {datetime.now().strftime('%B %d, %Y')}.
Triggered when: {task_info.get('trigger', 'manual')}

## What It Does
{" ".join(task_info.get('steps', ['<automated steps>']))}

## How Russell Tuna Executes This

### Trigger Condition
{task_info.get('trigger', 'Manual activation only')}

### Execution Steps
"""
    for i, step in enumerate(task_info.get('steps', [])):
        skill_md += f"{i+1}. {step}\n"
    
    skill_md += f"""
### Notification Channel
{ task_info.get('channel', 'telegram') }

### Priority
{'HIGH PRIORITY - affects deal closing' if task_info.get('high_priority') else 'Standard automation'}

## Notes
- Source capture: {capture_id}
- Learned via Watch Once protocol
- Can be refined by Jack at any time
"""

    with open(skill_dir / "SKILL.md", "w") as f:
        f.write(skill_md)
    
    return skill_dir

def notify_jack(skill_info, skill_dir):
    """
    Send Jack a Telegram message asking if he wants to automate this.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("No Telegram token - would send: 'I noticed you did X. Want me to automate it?'")
        return
    
    try:
        import requests
        task_name = task_info.get('task_name', 'this task')
        message = f"🤖 *Watch Once Alert*\n\nI noticed you just did: *{task_name}*\n\nI can automate this for you going forward. Want me to?\n\nReply YES to enable automation, NO to skip."
        
        # Send to Jack via Russell Tuna's chat ID
        requests.post(
            f"https://api.telegram.org/{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": JACK_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print(f"Notification error: {e}")

def store_capture(capture_data, capture_id):
    """Store raw capture for later analysis."""
    capture_file = WATCH_ONCE_PATH / f"{capture_id}.json"
    with open(capture_file, "w") as f:
        json.dump({
            "capture_id": capture_id,
            "timestamp": datetime.now().isoformat(),
            "data": capture_data
        }, f, indent=2)
    return capture_file

def get_pending_captures():
    """Get all captures awaiting approval."""
    captures = []
    for f in sorted(WATCH_ONCE_PATH.glob("pending-*.json")):
        with open(f) as fp:
            captures.append(json.load(fp))
    return captures

def approve_capture(capture_id):
    """Approve a capture - convert to automated skill."""
    capture_file = WATCH_ONCE_PATH / f"pending-{capture_id}.json"
    if not capture_file.exists():
        return None
    
    with open(capture_file) as f:
        capture = json.load(f)
    
    task_info = analyze_capture(
        capture.get("screen_data", ""),
        capture.get("voice_transcript", ""),
        capture.get("context", "")
    )
    
    skill_dir = save_as_automated_skill(task_info, capture_id)
    
    # Move to approved
    capture_file.rename(WATCH_ONCE_PATH / f"approved-{capture_id}.json")
    
    return skill_dir, task_info

# Webhook receiver for Clicky captures
def receive_clicky_capture(capture_payload):
    """
    Receive a capture from Clicky (via Cloudflare Worker webhook).
    Payload contains:
    - screen_data: base64 screenshot
    - voice_transcript: what Jack said
    - context: any additional context
    """
    capture_id = f"wc-{int(time.time())}"
    
    # Store raw capture
    store_capture(capture_payload, capture_id)
    
    # Analyze
    task_info = analyze_capture(
        capture_payload.get("screen_data", ""),
        capture_payload.get("voice_transcript", ""),
        capture_payload.get("context", "")
    )
    
    # Ask Jack if he wants to automate
    notify_jack(task_info, None)
    
    return {"capture_id": capture_id, "status": "pending_approval"}

# Manual trigger (for testing)
def trigger_manual(task_description):
    """Jack manually triggers Watch Once on a task."""
    capture_id = f"manual-{int(time.time())}"
    task_info = {
        "task_name": task_description,
        "trigger": "manual",
        "steps": ["<Define steps>"],
        "channel": "telegram",
        "high_priority": True
    }
    
    skill_dir = save_as_automated_skill(task_info, capture_id)
    return skill_dir

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--pending":
        caps = get_pending_captures()
        print(f"Pending captures: {len(caps)}")
        for c in caps:
            print(f"  - {c.get('capture_id')}: {c.get('context', 'no context')}")
    else:
        print("Watch Once Engine — JackConnect")
        print(f"Vault: {WATCH_ONCE_PATH}")
        print(f"Skills: {SKILLS_PATH}")
        print("Run with --pending to see pending captures")