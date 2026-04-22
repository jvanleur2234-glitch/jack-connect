#!/usr/bin/env python3
"""
Telegram Grocery Bot — Joseph Vanleur
Commands:
  /deals — weekly grocery deals for Sioux Falls
  /list — your shopping list
  /add <item> — add to list
  /remove <item> — remove from list
  /clear — clear your list
  /compare <item> — compare price across stores
"""
import os, json, re, requests
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_CHAT_IDS = os.environ.get("TELEGRAM_ALLOWED_CHATS", "").split(",")

WALMART_ZIP = "57104"
DATA_DIR = os.path.expanduser("~/.grocery-bot/")
os.makedirs(DATA_DIR, exist_ok=True)
LIST_FILE = os.path.join(DATA_DIR, "list.json")
DEALS_CACHE = os.path.join(DATA_DIR, "deals_cache.json")

# ── Auth ─────────────────────────────────────────────────────────────────────
def is_allowed(chat_id):
    if not ALLOWED_CHAT_IDS or "" in ALLOWED_CHAT_IDS:
        return True  # No restriction in dev
    return str(chat_id) in ALLOWED_CHAT_IDS

# ── Walmart API ───────────────────────────────────────────────────────────────
def get_walmart_deals(zip_code=WALMART_ZIP, limit=40):
    """Fetch weekly ad from Walmart grocery API"""
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
        if r.status_code != 200:
            return []
        data = r.json()
        items = []
        for item in data.get("payload", {}).get("items", [])[:limit]:
            price = item.get("price", {})
            if isinstance(price, dict):
                items.append({
                    "name": item.get("name", ""),
                    "price": price.get("currentPrice", ""),
                    "was": price.get("wasPrice", ""),
                    "uom": item.get("unitOfMeasure", ""),
                    "store": "Walmart"
                })
            else:
                items.append({
                    "name": item.get("name", ""),
                    "price": str(price),
                    "was": "",
                    "uom": item.get("unitOfMeasure", ""),
                    "store": "Walmart"
                })
        return items
    except Exception as e:
        return [{"name": f"Walmart error: {e}", "price": "", "was": "", "uom": "", "store": "Walmart"}]

def get_cached_deals(force=False):
    """Cache deals for 1 hour"""
    try:
        if not force:
            with open(DEALS_CACHE) as f:
                cache = json.load(f)
            age = datetime.now().timestamp() - cache.get("ts", 0)
            if age < 3600:
                return cache["deals"]
    except:
        pass
    deals = get_walmart_deals()
    with open(DEALS_CACHE, "w") as f:
        json.dump({"deals": deals, "ts": datetime.now().timestamp()}, f)
    return deals

# ── Shopping List ─────────────────────────────────────────────────────────────
def load_list():
    try:
        with open(LIST_FILE) as f:
            return json.load(f)
    except:
        return []

def save_list(items):
    with open(LIST_FILE, "w") as f:
        json.dump(items, f, indent=2)

def format_list(items):
    if not items:
        return "🛒 Your list is empty.\n\nCommands:\n/add milk\ne.g. /add eggs"
    msg = f"🛒 *Your List* ({len(items)} items)\n\n"
    for i, item in enumerate(items, 1):
        check = "✅" if item.get("done") else "⬜"
        msg += f"{check} {i}. {item['name']}\n"
    msg += "\n/add <item> — add\n/remove <item> — remove\n/clear — empty list"
    return msg

# ── Telegram API ────────────────────────────────────────────────────────────────
def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }, timeout=10)
    return r.json()

def send_replykeyboard(chat_id, text, commands):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    keyboard = [[c] for c in commands]
    r = requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"keyboard": keyboard, "resize_keyboard": True}
    }, timeout=10)
    return r.json()

# ── Command Handlers ──────────────────────────────────────────────────────────
def handle_deals(chat_id):
    deals = get_cached_deals()
    if not deals:
        return send_message(chat_id, "❌ Couldn't fetch Walmart deals right now. Try again in a few minutes.")
    
    # Group by category
    msg = f"🏪 *Walmart Weekly Deals* — Sioux Falls\n"
    msg += f"_Updated {datetime.now().strftime('%b %d %I:%M %p')} CT_\n\n"
    
    shown = 0
    for d in deals[:25]:
        was = f" ~~${d['was']}~~" if d.get('was') else ""
        uom = f" / {d['uom']}" if d.get('uom') else ""
        price = f"${d['price']}" if d.get('price') and d['price'] != 'None' else "SALE"
        msg += f"💰 {price}{was} — {d['name'][:50]}{uom}\n"
        shown += 1
    
    msg += f"\n_Showing {shown} of {len(deals)} deals_"
    return send_message(chat_id, msg)

def handle_list(chat_id):
    items = load_list()
    return send_message(chat_id, format_list(items))

def handle_add(chat_id, text):
    item = text.strip()
    if not item:
        return send_message(chat_id, "Usage: /add milk")
    items = load_list()
    items.append({"name": item, "done": False, "added": datetime.now().isoformat()})
    save_list(items)
    return send_message(chat_id, f"✅ Added: *{item}*\n\n{format_list(items)}")

def handle_remove(chat_id, text):
    item = text.strip().lower()
    items = load_list()
    before = len(items)
    items = [i for i in items if i["name"].lower() != item]
    if len(items) == before:
        return send_message(chat_id, f"❌ Couldn't find: *{text}*")
    save_list(items)
    return send_message(chat_id, f"❌ Removed: *{text}*\n\n{format_list(items)}")

def handle_clear(chat_id):
    save_list([])
    return send_message(chat_id, "🧹 List cleared!")

def handle_compare(chat_id, query):
    """Search deals for an item"""
    if not query:
        return send_message(chat_id, "Usage: /compare milk")
    deals = get_cached_deals()
    query_lower = query.lower()
    matches = [d for d in deals if query_lower in d["name"].lower()]
    
    if not matches:
        return send_message(chat_id, f"🔍 No Walmart deals found for: *{query}*\n\nWant me to check other stores?")
    
    msg = f"🔍 *Price Check: {query}*\n\n"
    for d in matches[:10]:
        was = f" ~~${d['was']}~~" if d.get('was') else ""
        price = f"${d['price']}" if d.get('price') and d['price'] != 'None' else "SALE"
        msg += f"🏪 Walmart: {price}{was} — {d['name'][:60]}\n"
    
    return send_message(chat_id, msg)

def handle_help(chat_id):
    msg = "🛒 *Grocery Bot Commands*\n\n"
    msg += "/deals — Weekly Walmart deals\n"
    msg += "/list — Your shopping list\n"
    msg += "/add <item> — Add to list\n"
    msg += "/remove <item> — Remove from list\n"
    msg += "/compare <item> — Check price\n"
    msg += "/clear — Empty list\n"
    msg += "/farmsd — Sioux Falls store info\n"
    return send_message(chat_id, msg)

def handle_farmsd(chat_id):
    msg = "🏪 *Sioux Falls Grocery Stores*\n\n"
    msg += "💚 *ALDI* — 49th & Louise\n"
    msg += "   Budget, excellent produce\n\n"
    msg += "🏪 *Walmart Supercenter* — 57th & Louise\n"
    msg += "   Use /deals for weekly ads\n\n"
    msg += "☀️ *Sunshine Foods* — 26th & Minnesota\n"
    msg += "   Local, ethnic foods, great butcher\n\n"
    msg += "🌿 *Hy-Vee* — Multiple locations\n"
    msg += "   Use /compare for price checks\n\n"
    msg += "🥩 *Sam's Club* — 70th & Louise\n"
    msg += "   Bulk, Membership needed"
    return send_message(chat_id, msg)

# ── Main Webhook Handler ───────────────────────────────────────────────────────
def handle_update(update):
    """Process a Telegram update (webhook or long-polling)"""
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    if not chat_id or not is_allowed(chat_id):
        return {"ok": False, "error": "not allowed"}
    
    # Route commands
    if text.startswith("/deals"):
        return handle_deals(chat_id)
    elif text.startswith("/list"):
        return handle_list(chat_id)
    elif text.startswith("/add "):
        return handle_add(chat_id, text[5:])
    elif text.startswith("/remove "):
        return handle_remove(chat_id, text[8:])
    elif text.startswith("/clear"):
        return handle_clear(chat_id)
    elif text.startswith("/compare "):
        return handle_compare(chat_id, text[9:])
    elif text in ["/help", "/start"]:
        return handle_help(chat_id)
    elif text in ["/farmsd", "/stores"]:
        return handle_farmsd(chat_id)
    elif text.startswith("/"):
        return handle_help(chat_id)
    else:
        # Free text — search deals
        return handle_compare(chat_id, text)

# ── Long-poll Mode ──────────────────────────────────────────────────────────────
def long_poll():
    """Poll Telegram for updates (simple alternative to webhooks)"""
    offset = None
    print("[Grocery Bot] Starting long-poll mode...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"timeout": 30, "limit": 1}
            if offset:
                params["offset"] = offset
            r = requests.get(url, params=params, timeout=35)
            updates = r.json().get("result", [])
            for update in updates:
                handle_update(update)
                offset = update["update_id"] + 1
        except Exception as e:
            print(f"[Grocery Bot] Error: {e}")
            import time; time.sleep(5)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--poll":
        long_poll()
    elif len(sys.argv) > 1 and sys.argv[1] == "--deals":
        deals = get_cached_deals(force=True)
        print(f"Fetched {len(deals)} deals from Walmart")
        for d in deals[:10]:
            print(f"  {d.get('price','')} — {d['name'][:50]}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Testing Walmart API...")
        deals = get_walmart_deals()
        print(f"Got {len(deals)} deals")
        for d in deals[:5]:
            print(f"  {d}")
    else:
        print("Usage:")
        print("  python3 telegram_handler.py --poll     # Start Telegram bot")
        print("  python3 telegram_handler.py --deals    # Fetch and show deals")
        print("  python3 telegram_handler.py --test     # Test Walmart API")
        print("\nRequires env vars:")
        print("  TELEGRAM_BOT_TOKEN=...  TELEGRAM_ALLOWED_CHATS=123456")
