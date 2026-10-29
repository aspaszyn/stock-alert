import os, time, requests
from bs4 import BeautifulSoup

URLS = [u.strip() for u in os.environ["PRODUCT_URL"].split(",") if u.strip()]
TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT_ID"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

OUT_WORDS = ["out of stock", "sold out", "currently unavailable",
             "notify me", "temporarily unavailable", "coming soon"]

def send(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT, "text": msg})

def check(url):
    r = requests.get(url, headers=HEADERS, timeout=25)
    html = r.text.lower()
    soup = BeautifulSoup(r.text, "html.parser")
    visible = soup.get_text(" ", strip=True).lower()

    if r.status_code != 200 or "captcha" in html or "automated access" in html:
        return f"blocked (status {r.status_code})"

    # Amazon
    if "amazon." in url:
        return "IN" if soup.find(id="add-to-cart-button") else "out"

    # E2Z Store (WooCommerce)
    if "e2zstore.com" in url:
        if "out-of-stock" in html or "out of stock" in visible:
            return "out"
        return "IN" if "single_add_to_cart_button" in html else "unknown"

    # Flipkart
    if "flipkart.com" in url:
        if any(w in visible for w in OUT_WORDS):
            return "out"
        return "IN" if ("add to cart" in visible or "buy now" in visible) else "unknown"

    # Stan Shop and Play-Asia
    if "stanshop.co" in url or "play-asia.com" in url:
        if any(w in visible for w in OUT_WORDS):
            return "out"
        if "add to cart" in visible or "buy now" in visible or "add to basket" in visible:
            return "IN"
        return "unknown"

    return "unknown"

for i, url in enumerate(URLS, 1):
    try:
        status = check(url)
        if status == "IN":
            send(f"🔥 Possibly back in stock!\n{url}")
        print(f"Product {i}: {status} | {url[:70]}")
    except Exception as e:
        print(f"Product {i}: error {e}")
    time.sleep(3)
