import requests
from bs4 import BeautifulSoup
import json
import os
import re

URL = "https://www.kicks.se/dior-sauvage-edp-60-ml"
TARGET_PRICE = 1199

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

def get_price():
    response = requests.get(URL, headers=HEADERS, timeout=20)
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
        except:
            pass
    text = soup.get_text()
    matches = re.findall(r'(\d[\d\s]*)\s*kr', text)
    prices = []
    for m in matches:
        try:
            p = float(m.replace(" ", "").replace("\xa0", ""))
            if 500 < p < 2500:
                prices.append(p)
        except:
            pass
    if prices:
        return max(set(prices), key=prices.count)
    return None

def send_telegram(price, last_price):
    message = f"🎯 PRISALARM! 【entity-Dior¦canonical_name=Dior】 Sauvage EDP 60 ml\n\nNu: {price:.0f} kr\nFörut: {last_price:.0f} kr\nMålpris: {TARGET_PRICE} kr\n\nKöp här: {URL}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=15)
    print(f"Telegram skickat: {r.status_code}")

def check():
    price = get_price()
    if price is None:
        print("Hittade inte priset")
        return
    print(f"Nuvarande pris: {price:.0f} kr")
    if price < TARGET_PRICE:
        print("Målpris nått! Skickar Telegram...")
        send_telegram(price, price)
    else:
        print(f"Fortfarande över målpris ({TARGET_PRICE} kr)")

if __name__ == "__main__":
    check()
