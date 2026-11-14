import requests
from bs4 import BeautifulSoup
import json
import os
import re

PRODUCTS = [
    {
        "name": "dior sauvage edp 60 ml",
        "store": "KICKS",
        "url": "https://www.kicks.se/dior-sauvage-edp-60-ml",
        "target": 1000,
    },
    {
        "name": "dior sauvage parfum",
        "store": "Ahlens",
        "url": "https://www.ahlens.se/produkter/skonhet/sauvage-parfum-22e37afa-d87a-44f2-a411-aae05b668215",
        "target": 1000,
    },
    {
        "name": "dior sauvage edp 60 ml",
        "store": "Deloox",
        "url": "https://www.deloox.se/produkt/1167425/dior-sauvage-eau-de-parfum-60-ml.html",
        "target": 1000,
    },
    {
        "name": "dior sauvage edp",
        "store": "Notino",
        "url": "https://www.notino.se/dior/sauvage-eau-de-parfum-for-man/p-15676582/",
        "target": 1000,
    },
]

STATE_FILE = "last_state.json"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

def get_price(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and "offers" in item:
                    offers = item["offers"]
                    if isinstance(offers, dict) and "price" in offers:
                        return float(offers["price"])
                    if isinstance(offers, list) and len(offers) > 0 and "price" in offers[0]:
                        return float(offers[0]["price"])
        except:
            pass
    text = soup.get_text()
    matches = re.findall(r'(\d[\d\s]*)\s*kr', text)
    prices = []
    for m in matches:
        try:
            p = float(m.replace(" ", "").replace("\xa0", ""))
            if 500 < p < 3000:
                prices.append(p)
        except:
            pass
    if prices:
        return max(set(prices), key=prices.count)
    return None

def send_telegram(product, price, last_price):
    message = f"PRISALARM! {product['name']}\n\nButik: {product['store']}\nNu: {price:.0f} kr\nForut: {last_price:.0f} kr\nMalpris: {product['target']} kr\n\nKop har: {product['url']}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=15)
    print(f"Telegram skickat for {product['store']}: {r.status_code}")

def check():
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
        except:
            pass
    for product in PRODUCTS:
        key = product["store"]
        print(f"\n--- Kollar {product['store']} ---")
        try:
            price = get_price(product["url"])
        except Exception as e:
            print(f"Fel hos {product['store']}: {e}")
            continue
        if price is None:
            print(f"Hittade inte priset hos {product['store']}")
            continue
        print(f"{product['store']}: {price:.0f} kr (mal: {product['target']} kr)")
        prev = state.get(key, {})
        last_notified = prev.get("notified", False)
        last_price = prev.get("price")
        if price < product["target"]:
            if not last_notified:
                print(f"Malpris natt hos {product['store']}! Skickar...")
                send_telegram(product, price, last_price if last_price else price)
                state[key] = {"price": price, "notified": True}
            else:
                print(f"Redan skickat for {product['store']}, hoppar over.")
                state[key] = {"price": price, "notified": True}
        else:
            print(f"Fortfarande over malpris hos {product['store']}")
            state[key] = {"price": price, "notified": False}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

if __name__ == "__main__":
    check()
