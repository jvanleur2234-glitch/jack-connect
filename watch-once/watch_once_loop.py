#!/usr/bin/env python3
"""
Watch Once Improvement Loop - JackConnect
=========================================
Inspired by davebcn87/pi-autoresearch

The autonomous loop: Watch Once -> Create Skill -> Test -> Measure -> Keep/Improve -> Repeat.
Jack does the task once -> we create a skill -> test it -> measure quality -> keep/improve -> repeat forever.
"""

import json, os, time, hashlib, subprocess
from datetime import datetime
from pathlib import Path

# Paths
VAULT = Path(os.environ.get("VAULT_PATH", "/home/workspace/solomon-vault"))
WO_LOOP = VAULT / "raw" / "watch-once-loop"
WO_LOOP.mkdir(parents=True, exist_ok=True)
SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "/home/workspace/solomon-skills"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()[:8]

def now():
    return datetime.now().isoformat()

def init_session(task_name, task_description, trigger, channel="telegram"):
    session_id = f"wo-{hash_text(task_name + now())}"
    session_dir = WO_LOOP / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    doc = f"""# Watch Once Loop: {task_name}

## Objective
{task_description}

## Trigger
{trigger}

## Channel
{channel}

## Objectives
- Quality score above 80/100
- Response time under 30 seconds
- Jack is notified immediately when trigger fires

## Baseline
_Completed: {now()}_
_Quality score: pending first run_

## What We Have Tried
_None yet - awaiting first execution._

## Results Log
| Run ID | Quality | Time | Status | Notes |
|--------|---------|------|--------|-------|
"""
    (session_dir / "session.md").write_text(doc)
    (session_dir / "runs.jsonl").write_text("")
    print(f"[Watch Once Loop] Session started: {session_id}")
    return session_id

def create_skill(session_id, task_name, trigger, steps, channel="telegram"):
    safe_name = task_name.lower().replace(" ", "-").replace("/", "-")[:50]
    skill_dir = SKILLS_DIR / safe_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    
    skill_md = f"""---
name: {safe_name}
description: {task_name} - {trigger}. Activates when: {trigger}.
---

# {task_name}

**Watch Once Skill** - Created {now()}

## Trigger
{trigger}

## Steps
{steps_text}

## Channel
{channel}

## How to Run
Russell Tuna / Superintendent executes this automatically when the trigger fires.
Notify Jack via {channel} with the result.

## Quality Criteria
- Jack is notified within 30 seconds of trigger firing
- Message is clear, actionable, includes the key info Jack needs
- Follows Jack's communication style (brief, friendly, gets to the point)
"""

    ref_md = f"""# {task_name} - Reference

## Trigger
{trigger}

## Original Steps
""" + "\n".join(f"- {s}" for s in steps) + """

## Quality Criteria
- Jack is notified within 30 seconds of trigger firing
- Message is clear and actionable
- Follows Jack's communication style

## Version History
- v1.0 ({now()}) - Created from Watch Once capture
"""
    
    (skill_dir / "SKILL.md").write_text(skill_md)
    (skill_dir / "VERSION").write_text("1.0.0")
    
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(exist_ok=True)
    (ref_dir / "original-workflow.md").write_text(ref_md)
    (skill_dir / "test_results.json").write_text(json.dumps({"runs": []}, indent=2))

    print(f"[Watch Once Loop] Skill created: {safe_name}")
    return str(skill_dir)

def test_skill(skill_name, test_inputs=None):
    import requests
    start = time.time()
    
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        return {"error": "Skill not found", "quality_score": 0, "response_time_ms": 0}
    
    skill_content = skill_path.read_text()
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "qwen3:1.7b",
                "prompt": f"Execute this skill with the given inputs.\n\nSkill: {skill_name}\nContent: {skill_content}\nInputs: {test_inputs or {}}\n\nOutput the result as JSON: {{\"result\": \"what was done\", \"message\": \"notification to send to Jack\"}}",
                "stream": False
            },
            timeout=60
        )
        elapsed_ms = (time.time() - start) * 1000
        result_text = response.json().get("response", "{}")
        
        try:
            result = json.loads(result_text)
        except:
            result = {"result": result_text[:200], "message": result_text[:200]}
        
        quality = 70
        if len(result.get("message", "")) > 10:
            quality += 15
        if elapsed_ms < 30000:
            quality += 15
        
        return {
            "quality_score": min(quality, 100),
            "response_time_ms": elapsed_ms,
            "output": result
        }
    except Exception as e:
        return {"error": str(e), "quality_score": 0, "response_time_ms": (time.time()-start)*1000}

def log_run(session_id, quality_score, response_time_ms, outcome, notes=""):
    run_id = hash_text(now())
    run = {
        "run_id": run_id,
        "session_id": session_id,
        "timestamp": now(),
        "quality_score": quality_score,
        "response_time_ms": response_time_ms,
        "outcome": outcome,
        "notes": notes
    }
    
    log_file = WO_LOOP / session_id / "runs.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(run) + "\n")
    
    _update_doc(session_id, run)
    print_dashboard(session_id)
    return run_id

def _update_doc(session_id, run):
    doc_file = WO_LOOP / session_id / "session.md"
    if not doc_file.exists():
        return
    doc = doc_file.read_text()
    
    emoji = {"kept": "OK", "improved": "STAR", "reverted": "REV", "failed": "FAIL"}.get(run["outcome"], "-")
    row = f"| {run['run_id'][:8]} | {run['quality_score']}/100 | {run['response_time_ms']/1000:.1f}s | {emoji} | {run['notes'][:50]} |"
    
    if "| Run ID |" in doc:
        doc = doc.replace("| Run ID |", row + "\n| Run ID |")
    
    if run["outcome"] in ("kept", "improved") and run["quality_score"] > 80:
        doc += f"\n\n## Best Result\n**Score: {run['quality_score']}/100** - {run['notes']}"
    
    doc_file.write_text(doc)

def get_runs(session_id):
    log_file = WO_LOOP / session_id / "runs.jsonl"
    if not log_file.exists():
        return []
    runs = []
    with open(log_file) as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    return sorted(runs, key=lambda r: r["quality_score"], reverse=True)

def print_dashboard(session_id):
    runs = get_runs(session_id)
    total = len(runs)
    kept = sum(1 for r in runs if r["outcome"] in ("kept", "improved"))
    best = runs[0] if runs else None
    
    print(f"WATCH ONCE LOOP | {total} runs, {kept} kept", end="")
    if best:
        print(f" | BEST: {best['quality_score']}/100 ({best['response_time_ms']/1000:.1f}s)", end="")
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Watch Once Improvement Loop")
        print("Commands:")
        print("  init <task> <description> <trigger>")
        print("  create <session_id> <task> <trigger> --steps step1|step2|step3")
        print("  test <session_id> <skill_name>")
        print("  log <session_id> <quality> <ms> <outcome> [notes]")
        print("  dashboard <session_id>")
        print("  list")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        sid = init_session(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"Session: {sid}")
    
    elif cmd == "create":
        steps = []
        for arg in sys.argv[5:]:
            if arg.startswith("--steps="):
                steps = arg[8:].split("|")
            elif arg.startswith("--steps"):
                steps = sys.argv[sys.argv.index(arg)+1].split("|")
                break
        path = create_skill(sys.argv[2], sys.argv[3], sys.argv[4], steps)
        print(f"Skill: {path}")
    
    elif cmd == "test":
        result = test_skill(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
        print(json.dumps(result, indent=2))
    
    elif cmd == "log":
        log_run(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "")
    
    elif cmd == "dashboard":
        print_dashboard(sys.argv[2])
    
    elif cmd == "list":
        for d in sorted(WO_LOOP.iterdir()):
            if d.is_dir():
                print(d.name)

# === CALLING LAYER ===
# After every task, ask: what did that feel like?
# After every session, surface: what are you avoiding? What lights you up?
# After every month, generate: what does this point toward?

CALLING_PROMPT = """Look at this person's work patterns over the past month:

Tasks they avoid: {avoid}
Tasks that energize them: {energize}
How they spend reclaimed time: {reclaimed_time}
What they say about their work: {reflections}

Generate 3 observations about what they might be DESIGNED for, based on their patterns.
Keep it short, specific, and kind. No fluff.

Format:
OBSERVATION: [what you noticed]
DESIGNED_FOR: [what this might point toward]
CONFIDENCE: [high/medium/low]

Be honest but gentle. This is someone's life calling, not a performance review."""

def generate_calling_insights(sessions: list) -> str:
    """Generate calling insights from session data."""
    avoid = [s.get("task_name","") for s in sessions if s.get("quality",0) < 50]
    energize = [s.get("task_name","") for s in sessions if s.get("quality",0) >= 80]
    reclaimed = [s.get("time_saved",0) for s in sessions]
    reflections = [s.get("reflection","") for s in sessions if s.get("reflection")]
    
    prompt = CALLING_PROMPT.format(
        avoid=", ".join(avoid[:5]) or "nothing recorded",
        energize=", ".join(energize[:5]) or "nothing recorded",
        reclaimed_time=f"{sum(reclaimed):.0f} hours total",
        reflections="; ".join(reflections[:5]) or "no reflections recorded"
    )
    
    # Use Ollama to generate insights
    messages = [{"role": "user", "content": prompt}]
    return ollama_chat(messages)

def weekly_freedom_review(sessions: list, week_num: int) -> str:
    """Generate weekly freedom review."""
    total_runs = len(sessions)
    kept = len([s for s in sessions if s.get("quality",0) >= 70])
    avg_quality = sum(s.get("quality",0) for s in sessions) / max(total_runs, 1)
    time_saved = sum(s.get("time_saved",0) for s in sessions)
    
    review = f"""WEEK {week_num} FREEDOM REVIEW
=====================
Tasks automated: {total_runs}
Skills kept: {kept}
Avg quality: {avg_quality:.0f}/100
Time saved: {time_saved:.1f} hours

YOUR FREEDOM MOMENTS:
"""
    for s in sessions:
        review += f"- {s.get('task_name','')}: saved {s.get('time_saved',0):.1f}h, quality {s.get('quality',0)}/100\n"
    
    review += """
THIS WEEK'S QUESTION:
What did you do with the time you got back?
Did you feel more like yourself?
"""
    return review
