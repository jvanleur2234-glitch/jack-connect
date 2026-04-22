#!/usr/bin/env python3
"""
Grocery Deal Scraper — Sioux Falls SD
Scrapes weekly ads from: Hy-Vee, Walmart, Target, Sunshine Foods
"""
import feedparser, requests, re
from bs4 import BeautifulSoup
from datetime import datetime

STORES = {
    "Hy-Vee": {
        "url": "https://www.hy-vee.com/aisles-online/flyers",
        "zip": "57104",
        "type": "flyer"
    },
    "Walmart": {
        "url": "https://grocery.walmart.com/usd/grocery/RS Goddard/GetWeeklyAd",
        "zip": "57104",
        "type": "api"
    },
    "Target": {
        "url": "https://www.target.com/c/weekly-ad/-/N-dt5xu",
        "zip": "57104",
        "type": "flyer"
    },
    "Sunshine Foods": {
        "url": "https://www.sunshinefoodssd.com/weekly-specials/",
        "zip": "57104",
        "type": "flyer"
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def scrape_hyvee():
    """Scrape Hy-Vee weekly ad via RSS + web scrape"""
    items = []
    try:
        r = requests.get(
            "https://www.hy-vee.com/stores/sioux-falls-41/flyer.rss",
            headers=HEADERS, timeout=10
        )
        feed = feedparser.parse(r.text)
        for entry in feed.entries[:20]:
            price = re.findall(r'\$\d+\.?\d*', entry.get('summary', ''))
            items.append({
                "store": "Hy-Vee",
                "item": entry.get('title', ''),
                "price": price[0] if price else "SALE",
                "url": entry.get('link', ''),
                "dates": entry.get('summary', '')[:100]
            })
    except Exception as e:
        items.append({"store": "Hy-Vee", "item": f"Error: {e}", "price": "", "url": "", "dates": ""})
    return items

def scrape_walmart():
    """Scrape Walmart weekly ad via API"""
    items = []
    try:
        r = requests.post(
            "https://grocery.walmart.com/usd/grocery/RS Goddard/GetWeeklyAd",
            headers={
                **HEADERS,
                "Content-Type": "application/json",
                "Referer": "https://grocery.walmart.com/"
            },
            json={"location": {"zipCode": "57104"}},
            timeout=15
        )
        data = r.json()
        for item in data.get('payload', {}).get('items', [])[:20]:
            items.append({
                "store": "Walmart",
                "item": item.get('name', ''),
                "price": item.get('price', {}).get('currentPrice', 'SALE'),
                "url": item.get('link', ''),
                "dates": ""
            })
    except Exception as e:
        items.append({"store": "Walmart", "item": f"Error: {e}", "price": "", "url": "", "dates": ""})
    return items

def scrape_target():
    """Scrape Target weekly ad"""
    items = []
    try:
        r = requests.get(
            "https://www.target.com/c/weekly-ad/-/N-dt5xu",
            headers=HEADERS, timeout=15
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        # Target uses JSON-LD for structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string) if hasattr(script, 'string') else {}
                if isinstance(data, list):
                    for ad in data:
                        for item in ad.get('hasOfferCatalog', {}).get('itemListElement', []):
                            offer = item.get('offers', {})
                            if isinstance(offer, list): offer = offer[0] if offer else {}
                            items.append({
                                "store": "Target",
                                "item": item.get('name', ''),
                                "price": f"${offer.get('price', 'SALE')}",
                                "url": item.get('url', ''),
                                "dates": ""
                            })
            except: pass
        # Fallback: scrape for item names in structured data
        if not items:
            for el in soup.find_all(attrs={'data-test': 'offerTile'})[:20]:
                name = el.get('aria-label', '') or el.get_text()
                price_el = el.find(class_=re.compile('price'))
                price = price_el.get_text() if price_el else 'SALE'
                items.append({
                    "store": "Target",
                    "item": name.strip(),
                    "price": price.strip(),
                    "url": "",
                    "dates": ""
                })
    except Exception as e:
        items.append({"store": "Target", "item": f"Error: {e}", "price": "", "url": "", "dates": ""})
    return items

def scrape_sunshine():
    """Scrape Sunshine Foods weekly ad"""
    items = []
    try:
        r = requests.get(
            "https://www.sunshinefoodssd.com/weekly-specials/",
            headers=HEADERS, timeout=15
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        # Find ad items
        for el in soup.find_all(['li', 'div'], class_=re.compile('sale|ad|item|product'))[:20]:
            text = el.get_text(separator=' ').strip()
            price = re.findall(r'\$\d+\.?\d*', text)
            if price and len(text) > 5:
                item_name = re.sub(r'\$\d+\.?\d*', '', text).strip()[:80]
                items.append({
                    "store": "Sunshine Foods",
                    "item": item_name,
                    "price": price[0],
                    "url": "https://www.sunshinefoodssd.com/weekly-specials/",
                    "dates": ""
                })
    except Exception as e:
        items.append({"store": "Sunshine Foods", "item": f"Error: {e}", "price": "", "url": "", "dates": ""})
    return items

def scrape_all():
    """Scrape all stores, combine and sort by price"""
    import json
    all_deals = []
    all_deals += scrape_hyvee()
    all_deals += scrape_walmart()
    all_deals += scrape_target()
    all_deals += scrape_sunshine()
    
    # Dedupe by item name (lowercase)
    seen = set()
    unique = []
    for deal in all_deals:
        key = deal['item'].lower()[:50]
        if key and key not in seen:
            seen.add(key)
            unique.append(deal)
    
    # Sort by price (extract numeric)
    def price_key(d):
        m = re.findall(r'\d+\.?\d*', str(d['price']))
        return float(m[0]) if m else 999
    unique.sort(key=price_key)
    
    return unique

if __name__ == "__main__":
    import json
    deals = scrape_all()
    print(f"Found {len(deals)} deals across 4 stores:")
    for d in deals[:30]:
        print(f"  {d['store']:15} | {d['price']:8} | {d['item'][:50]}")
