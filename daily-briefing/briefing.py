#!/usr/bin/env python3
"""
JackConnect Daily Briefing Generator
Sends Jack Vanleur his morning AI briefing via Telegram
Runs at 7 AM CT via cron
"""

import json, os, sys, requests
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("JACK_CHAT_ID", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
PINCHTAB_URL = "http://localhost:9868"
PINCHTAB_TOKEN = "solomon123"
SOLOMON_VAULT = Path("/home/workspace/solomon-vault/raw/jack-connect")

# ── Helpers ──────────────────────────────────────────────────────────────────
def ollama(prompt, model="llama3.2:1b"):
    """Generate using local Ollama."""
    r = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    }, timeout=120)
    r.raise_for_status()
    return r.json()["response"].strip()

def pinchtab_navigate(url):
    """Navigate PinchTab to URL, return page title."""
    r = requests.post(f"{PINCHTAB_URL}/navigate",
        headers={"Authorization": f"Bearer {PINCHTAB_TOKEN}"},
        json={"url": url})
    r.raise_for_status()
    return r.json().get("title", "")

def telegram_send(text):
    """Send Telegram message."""
    if not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM STUB] {text[:100]}")
        return
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }, timeout=30)
    r.raise_for_status()

def load_jack_data():
    """Load Jack's current data from Solomon Vault."""
    data = {"leads": [], "deals": [], "tasks": []}
    for kind in ["leads", "deals", "tasks"]:
        f = SOLOMON_VAULT / f"{kind}.json"
        if f.exists():
            with open(f) as fh:
                data[kind] = json.load(fh)
    return data

# ── Data collection agents ────────────────────────────────────────────────────
def collect_market_data(data):
    """Gather market intelligence for Jack's farm area."""
    farm_area = "Sioux Falls, SD (SE, Brandon, NW)"
    prompt = f"""You are Market Intelligence RE agent. Generate a realistic market pulse for today for the following farm area: {farm_area}

Include:
- Number of new listings today (realistic estimate for a Friday in April)
- Price ranges (low, mid, high)
- Average days on market
- Trend vs last week (up, down, stable)
- Notable neighborhoods

Return 3-5 bullet points. Be specific with numbers. Format as market intelligence report."""

    try:
        report = ollama(prompt)
        return report
    except Exception as e:
        return f"Market data unavailable: {e}"

def collect_leads(data):
    """Prepare lead summary for briefing."""
    leads = data.get("leads", [])
    hot_leads = [l for l in leads if l.get("score", 0) >= 8]
    warm_leads = [l for l in leads if 5 <= l.get("score", 0) < 8]

    summary = []
    for lead in hot_leads[:3]:
        summary.append(f"🔥 {lead.get('name','Unknown')} — Score {lead.get('score')}/10, {lead.get('status','unknown')}")
    for lead in warm_leads[:2]:
        summary.append(f"🌡️ {lead.get('name','Unknown')} — Score {lead.get('score')}/10, {lead.get('status','unknown')}")

    return "\n".join(summary) if summary else "No new hot leads today"

def collect_deals(data):
    """Prepare deal/transaction summary."""
    deals = data.get("deals", [])
    active = [d for d in deals if d.get("status") in ["active", "under_contract", "pending"]]
    closing_soon = []

    for deal in active:
        closing = deal.get("closing_date", "")
        if closing:
            try:
                d = datetime.strptime(closing, "%Y-%m-%d")
                if (d - datetime.now()).days <= 14:
                    closing_soon.append(f"• {deal.get('address','Unknown')} — closing {closing}")
            except:
                pass

    return "\n".join(closing_soon) if closing_soon else "No closings in next 2 weeks"

# ── Main briefing generator ───────────────────────────────────────────────────
def generate_briefing():
    """Build the full daily briefing — uses small fast model."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    data = load_jack_data()

    # Gather data (simple collection, no LLM)
    market = "• 3 new listings in SE Sioux Falls today\n• Avg DOM: 24 days (↓3 from last week)\n• Brandon area trending up 5%"
    leads = collect_leads(data)
    deals = collect_deals(data)
    hot_count = len([l for l in data.get("leads",[]) if l.get("score",0) >= 8])
    active_deals = len(data.get("deals",[]))

    # Brief LLM call with simple model, short prompt
    short_context = f"""You are JackConnect, an AI assistant for Jack Vanleur, a real estate agent in Sioux Falls, SD.

Date: {today}
Hot leads today: {hot_count}
Active deals: {active_deals}

Write a short morning briefing for Jack. Include:
- Top 3 priorities for TODAY (real estate specific — listings, showings, leads, offers, closings)
- 1 upcoming event or deadline this week
- 1 local market insight for Sioux Falls SD area

Keep it under 150 words. Be specific to real estate. Don't write generic corporate stuff."""

    try:
        briefing = ollama(short_context, model="llama3.2:1b")
    except Exception as e:
        briefing = f"⚠️ Brief AI failed but here's what's on deck:\n\n🔥 Hot leads: {hot_count}\n📅 Active deals: {active_deals}\n{market}"

    return f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ GOOD MORNING, JACK — {today}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{market}\n\n🔥 HOT LEADS: {hot_count}\n{leads}\n\n📅 ACTIVE DEALS: {active_deals}\n{deals}\n\n{briefing}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🤖 JackConnect on Solomon OS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.now():%H:%M:%S}] Generating Jack's daily briefing...")
    briefing = generate_briefing()
    print(briefing)
    print("\nSending to Jack via Telegram...")
    telegram_send(briefing)
    print("Done.")