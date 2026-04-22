#!/usr/bin/env python3
"""
Grocery Deal Bot — Sioux Falls
Telegram bot that sends weekly deals and manages shopping list
"""
import os, json, re, requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WALMART_ZIP = "57104"

SHOPPING_LIST_FILE = os.path.expanduser("~/.grocery_list.json")

# ── Walmart API ──────────────────────────────────────────────────────────────
def get_walmart_deals(zip_code=WALMART_ZIP, limit=30):
    items = []
    try:
        r = requests.post(
            "https://grocery.walmart.com/usd/grocery/RS%20Goddard/GetWeeklyAd",
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
                "Content-Type": "application/json",
                "Referer": "https://grocery.walmart.com/",
            },
            json={"location": {"zipCode": zip_code}},
            timeout=15
        )
        data = r.json()
        for item in data.get("payload", {}).get("items", [])[:limit]:
            price = item.get("price", {})
            items.append({
                "name": item.get("name", ""),
                "price": price.get("currentPrice", "SALE") if isinstance(price, dict) else str(price),
                "was": price.get("wasPrice", "") if isinstance(price, dict) else "",
                "uom": item.get("unitOfMeasure", ""),
            })
    except Exception as e:
        items.append({"name": f"Walmart API error: {e}", "price": "", "was": "", "uom": ""})
    return items

# ── Shopping List ────────────────────────────────────────────────────────────
def load_list():
    try:
        with open(SHOPPING_LIST_FILE) as f:
            return json.load(f)
    except:
        return {"items": [], "stores": {}}

def save_list(data):
    with open(SHOPPING_LIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_item(text):
    data = load_list()
    item = text.strip().lstrip("+").lstrip("-").lstrip("add ").strip()
    if item:
        data["items"].append({"name": item, "done": False, "added": datetime.now().isoformat()})
        save_list(data)
        return f"✅ Added: {item}"
    return "Usage: /add milk"

def remove_item(text):
    data = load_list()
    item = text.strip().lstrip("-").lstrip("remove ").strip()
    removed = None
    data["items"] = [i for i in data["items"] if i["name"].lower() != item.lower()]
    save_list(data)
    return f"❌ Removed: {item}" if removed else f"Couldn't find: {item}"

def list_items():
    data = load_list()
    if not data["items"]:
        return "🛒 Your list is empty. Say /add <item>"
    msg = "🛒 *Your Shopping List*\n"
    for i, item in enumerate(data["items"], 1):
        check = "✅" if item.get("done") else "⬜"
        msg += f"{check} {i}. {item['name']}\n"
    return msg

# ── Telegram ───────────────────────────────────────────────────────────────
def send_message(text, parse_mode="Markdown"):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(text)  # Fallback to stdout
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }, timeout=10)

def send_photo(photo_url, caption=""):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": photo_url,
        "caption": caption
    }, timeout=10)

# ── Weekly Deals Report ──────────────────────────────────────────────────────
def build_weekly_report(zip_code=WALMART_ZIP):
    """Build the full weekly deals message"""
    deals = get_walmart_deals(zip_code)
    msg = f"🛒 *Sioux Falls Weekly Deals* — {datetime.now().strftime('%b %d')\n\n"
    msg += f"Walmart (zip {zip_code}) — {len(deals)} sale items\n"
    for d in deals[:20]:
        was = f" ~~${d['was']}~~" if d.get('was') else ""
        uom = f" / {d['uom']}" if d.get('uom') else ""
        msg += f"  💰 {d['price']}{was} — {d['name'][:50]}{uom}\n"
    msg += f"\n_Generated {datetime.now().strftime('%b %d %I:%M %p')} CT_"
    return msg

# ── CLI Commands ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    
    if cmd == "report":
        msg = build_weekly_report()
        print(msg)
        send_message(msg)
    elif cmd == "list":
        print(list_items())
        send_message(list_items())
    elif cmd == "add":
        result = add_item(args)
        print(result)
        send_message(result)
    elif cmd == "remove":
        result = remove_item(args)
        print(result)
        send_message(result)
