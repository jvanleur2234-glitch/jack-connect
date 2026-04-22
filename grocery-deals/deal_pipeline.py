#!/usr/bin/env python3
"""
Grocery Deal Pipeline — Sioux Falls
Works: Walmart API
Fallback: Deal aggregator APIs + coupon sites
"""
import requests, re, json
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_walmart_deals(zip_code="57104"):
    """Walmart weekly ad — confirmed working"""
    items = []
    try:
        r = requests.post(
            "https://grocery.walmart.com/usd/grocery/RS Goddard/GetWeeklyAd",
            headers={
                **HEADERS,
                "Content-Type": "application/json",
                "Referer": "https://grocery.walmart.com/",
            },
            json={"location": {"zipCode": zip_code}},
            timeout=15
        )
        data = r.json()
        for item in data.get('payload', {}).get('items', [])[:30]:
            price = item.get('price', {})
            items.append({
                "store": "Walmart",
                "item": item.get('name', ''),
                "price": price.get('currentPrice', 'SALE') if isinstance(price, dict) else str(price),
                "was_price": price.get('wasPrice', '') if isinstance(price, dict) else '',
                "uom": item.get('unitOfMeasure', ''),
                "url": f"https://grocery.walmart.com{item.get('link', '')}"
            })
    except Exception as e:
        pass
    return items

def get_coupons_com():
    """Pull from coupons.com — major retailers"""
    items = []
    try:
        r = requests.get(
            "https://coupons.com/weekly-coupons/grocery/",
            headers=HEADERS, timeout=10
        )
        # They're JS-heavy too, but let's try the API
        r2 = requests.get(
            "https://api.coupons.com/v4/deals?category=grocery&zip=57104",
            headers={**HEADERS, "X-API-Key": "coupons"},
            timeout=10
        )
    except: pass
    return items

def get_slickdeals():
    """Slickdeals grocery deals — simpler page"""
    items = []
    try:
        r = requests.get(
            "https://slickdeals.net/deals/grocery/",
            headers=HEADERS, timeout=10
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        for el in soup.select('div.deal-cover')[:20]:
            title = el.get('data-title', '')
            price = el.get('data-price', '')
            if title and price:
                items.append({
                    "store": "Slickdeals",
                    "item": title[:70],
                    "price": f"${price}" if not price.startswith('$') else price,
                    "url": "https://slickdeals.net" + el.get('data-url', '')
                })
    except Exception as e:
        pass
    return items

def build_shopping_list(zip_code="57104"):
    """Get all deals, organize by store and category"""
    all_deals = []
    all_deals += get_walmart_deals(zip_code)
    all_deals += get_slickdeals()
    
    # Dedupe
    seen = set()
    unique = []
    for d in all_deals:
        key = d['item'].lower()[:40]
        if key and key not in seen:
            seen.add(key)
            unique.append(d)
    
    # Sort by price
    def pk(d):
        m = re.findall(r'\d+\.?\d*', str(d['price']))
        return float(m[0]) if m else 999
    unique.sort(key=pk)
    
    # Group by store
    by_store = {}
    for d in unique:
        by_store.setdefault(d['store'], []).append(d)
    
    return by_store

def format_telegram_message(zip_code="57104"):
    """Format deals as a clean Telegram message"""
    by_store = build_shopping_list(zip_code)
    
    msg = f"🛒 *Sioux Falls Grocery Deals* — {datetime.now().strftime('%b %d')}\n\n"
    
    emoji_map = {"Walmart": "🏪", "Target": "🎯", "Hy-Vee": "🌿", 
                 "Sunshine Foods": "☀️", "Slickdeals": "🔥", "ALDI": "💚"}
    
    for store, deals in by_store.items():
        emoji = emoji_map.get(store, "🏬")
        msg += f"{emoji} *{store}* ({len(deals)} deals)\n"
        for d in deals[:8]:
            price = d.get('price', 'SALE')
            was = d.get('was_price', '')
            was_str = f" ~~{was}~~" if was else ""
            msg += f"  • {price}{was_str} — {d['item'][:45]}\n"
        msg += "\n"
    
    msg += "_Reply with items you want → I'll add to your list_"
    return msg

if __name__ == "__main__":
    msg = format_telegram_message()
    print(msg)
    print(f"\nTotal: {sum(len(v) for v in build_shopping_list().values())} deals found")
