# app.py
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import re, math, os

app = Flask(__name__)

# --- EXACT helper from your file ---
def extract_number(text):
    """Convert shorthand counts like '1.2K' or '3M' to int."""
    if not text:
        return None
    m = re.search(r'(\d+[\d,.]*[KkMm]?)', text)
    if not m:
        return None
    num_str = m.group(1).replace(',', '').upper()
    try:
        if 'K' in num_str:
            return int(float(num_str.replace('K','')) * 1_000)
        if 'M' in num_str:
            return int(float(num_str.replace('M','')) * 1_000_000)
        return int(float(num_str))
    except ValueError:
        return None

# --- EXACT selectors from your file ---
LIKES_SELECTORS = [
    '.X8m.zDA.IZT.eSP.dyH.llN.Kv8',
    '[data-test-id="aggregated-reactions-container"]',
    '[data-test-id="reactions-count-button"]'
]

def extract_likes_sync(page):
    """Replicates your async extract_likes() using the same selectors."""
    for sel in LIKES_SELECTORS:
        el = page.query_selector(sel)
        if el:
            txt = el.inner_text() or ""
            num = extract_number(txt)
            if num:
                return num
    return None

def compute_score_from_avg_likes(avg_likes: float, scale: float = 150.0) -> float:
    """Your exponential normalization: 1 - exp(-avg_likes / scale)."""
    score = 1 - math.exp(-float(avg_likes) / float(scale))
    return round(min(max(score, 0.0), 1.0), 3)

def get_pinterest_score(term: str, num_pins: int = 3, delay_ms_search: int = 5000, delay_ms_pin: int = 3000, scale: float = 150.0) -> float:
    """Open search page, visit first N pins, extract likes with SAME logic, return normalized score."""
    if not term:
        return 0.0

    search_url = f"https://www.pinterest.com/search/pins/?q={term.replace(' ', '%20')}"
    total_likes = 0
    count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(delay_ms_search)

            pin_links = page.query_selector_all('a[href*="/pin/"]')
            if not pin_links:
                browser.close()
                return 0.0

            for link in pin_links[:max(1, num_pins)]:
                href = link.get_attribute('href')
                if not href:
                    continue
                pin_url = f"https://www.pinterest.com{href}" if href.startswith('/') else href

                pin_page = browser.new_page()
                try:
                    pin_page.goto(pin_url, wait_until="domcontentloaded", timeout=30000)
                    pin_page.wait_for_timeout(delay_ms_pin)
                    likes = extract_likes_sync(pin_page)  # ← SAME selector logic
                    if likes:
                        total_likes += likes
                        count += 1
                except PWTimeoutError:
                    pass
                except Exception:
                    pass
                finally:
                    pin_page.close()
        finally:
            browser.close()

    if count == 0:
        return 0.0

    avg_likes = total_likes / count
    return compute_score_from_avg_likes(avg_likes, scale=scale)

@app.route("/pinterest_score", methods=["POST"])
def pinterest_score_api():
    """
    Body:
      {
        "term": "puffer jacket",
        "num_pins": 3,                # optional (default 3)
        "delay_ms_search": 5000,      # optional
        "delay_ms_pin": 3000,         # optional
        "scale": 150.0                # optional normalization scale
      }
    """
    data = request.get_json(force=True, silent=True) or {}
    term = data.get("term", "").strip()
    if not term:
        return jsonify({"error": "term is required"}), 400

    num_pins = int(data.get("num_pins", 3))
    delay_ms_search = int(data.get("delay_ms_search", 5000))
    delay_ms_pin = int(data.get("delay_ms_pin", 3000))
    scale = float(data.get("scale", 10.0))

    score = get_pinterest_score(term, num_pins, delay_ms_search, delay_ms_pin, scale)
    return jsonify({"term": term, "pinterest_score": score})

@app.route("/")
def health():
    return "Pinterest Likes Score API ✅"
