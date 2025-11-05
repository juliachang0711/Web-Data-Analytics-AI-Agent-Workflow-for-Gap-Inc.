import asyncio
from playwright.async_api import async_playwright
import json
import base64
import requests
import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
from PIL import Image

# --- Configuration ---
# --- Hardcoded Google Vision API Key ---
GOOGLE_VISION_API_KEY = "Replace with your own key"  # 🔒 replace with your real key
GOOGLE_VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"


DOWNLOAD_DIR = "pinterest_images"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Google Vision Functions ---

def test_vision_api():
    """Test connection to Google Vision API"""
    if not GOOGLE_VISION_API_KEY:
        print("❌ Missing GOOGLE_VISION_API_KEY in .env file.")
        return False

    try:
        test_image_path = os.path.join(DOWNLOAD_DIR, "test_image.jpg")
        Image.new('RGB', (100, 100), color='red').save(test_image_path)
        with open(test_image_path, 'rb') as img_file:
            img_content = base64.b64encode(img_file.read()).decode('utf-8')

        payload = {
            "requests": [{
                "image": {"content": img_content},
                "features": [{"type": "LABEL_DETECTION", "maxResults": 10}]
            }]
        }

        res = requests.post(GOOGLE_VISION_URL, json=payload, timeout=15)
        return res.status_code == 200
    except Exception as e:
        print(f"Vision API test failed: {e}")
        return False


def analyze_image_with_vision(image_path):
    """Analyze an image file using Google Vision AI."""
    if not GOOGLE_VISION_API_KEY or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, 'rb') as f:
            img_content = base64.b64encode(f.read()).decode('utf-8')

        payload = {
            "requests": [{
                "image": {"content": img_content},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": 10},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "WEB_DETECTION", "maxResults": 10}
                ]
            }]
        }

        res = requests.post(GOOGLE_VISION_URL, json=payload, timeout=30)
        if res.status_code != 200:
            return None

        data = res.json().get("responses", [{}])[0]
        return {
            "labels": [l['description'] for l in data.get('labelAnnotations', [])],
            "objects": [o['name'] for o in data.get('localizedObjectAnnotations', [])],
            "web_entities": [e['description'] for e in data.get('webDetection', {}).get('webEntities', [])]
        }
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return None


# --- Helper Functions ---

def download_image(image_url, pin_id):
    """Download a Pinterest image."""
    try:
        filename = f"pin_{pin_id}.jpg"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(image_url, headers=headers, timeout=20)
        res.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(res.content)
        return filepath
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")
        return None


def extract_number(text):
    """Convert '1.2K' etc. into integers"""
    if not text:
        return None
    match = re.search(r'(\d+[\d,.]*[KkMm]?)', text)
    if not match:
        return None
    num_str = match.group(1).replace(',', '').upper()
    try:
        if 'K' in num_str:
            return int(float(num_str.replace('K', '')) * 1_000)
        elif 'M' in num_str:
            return int(float(num_str.replace('M', '')) * 1_000_000)
        else:
            return int(float(num_str))
    except ValueError:
        return None


# --- Engagement Extraction Functions (from 2nd script) ---

async def extract_likes(page):
    try:
        selectors = [
            '.X8m.zDA.IZT.eSP.dyH.llN.Kv8',
            '[data-test-id="aggregated-reactions-container"]',
            '[data-test-id="reactions-count-button"]'
        ]
        for selector in selectors:
            el = await page.query_selector(selector)
            if el:
                text = await el.inner_text()
                num = extract_number(text)
                if num:
                    return num
        return None
    except:
        return None


async def extract_comments(page):
    try:
        el = await page.query_selector('[aria-label*="comment" i], [data-test-id*="comment"]')
        if el:
            text = await el.inner_text()
            num = extract_number(text)
            if num:
                return num
        action_bar = await page.query_selector('[data-test-id="closeup-action-bar"]')
        if action_bar:
            text = await action_bar.inner_text()
            match = re.search(r'(\d+[\d,.]*[KkMm]?)\s*comments?', text, re.I)
            if match:
                return extract_number(match.group(1))
        return None
    except:
        return None


async def extract_saves(page):
    try:
        save_el = await page.query_selector('[data-test-id="PinBetterSaveButton"], [aria-label*="save" i]')
        if save_el:
            text = await save_el.inner_text()
            num = extract_number(text)
            if num:
                return num
        action_bar = await page.query_selector('[data-test-id="closeup-action-bar"]')
        if action_bar:
            text = await action_bar.inner_text()
            match = re.search(r'(\d+[\d,.]*[KkMm]?)\s*saves?', text, re.I)
            if match:
                return extract_number(match.group(1))
        return None
    except:
        return None


# --- Scraping Functions ---

async def scrape_single_pin(browser, pin_url, pin_id):
    """Scrape a single Pinterest pin for metadata + engagement + vision."""
    print(f"\n🧷 Scraping pin {pin_id}: {pin_url}")
    pin_data = {
        "pin_id": pin_id,
        "pin_url": pin_url,
        "title": None,
        "image_url": None,
        "likes": None,
        "comments": None,
        "saves": None,
        "vision_analysis": None
    }

    context = await browser.new_context()
    page = await context.new_page()
    try:
        await page.goto(pin_url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        # Title
        title_el = await page.query_selector('h1, [data-test-id="pin-title"], [data-test-id="closeup-title"]')
        if title_el:
            pin_data["title"] = (await title_el.inner_text()).strip()

        # Image
        img_el = await page.query_selector('img[src*="pinimg.com"]')
        if img_el:
            img_url = await img_el.get_attribute('src')
            pin_data["image_url"] = img_url

            image_path = download_image(img_url, pin_id)
            if image_path:
                print("   🔍 Running Vision AI analysis...")
                pin_data["vision_analysis"] = analyze_image_with_vision(image_path)

        # Engagement
        pin_data["likes"] = await extract_likes(page)
        pin_data["comments"] = await extract_comments(page)
        pin_data["saves"] = await extract_saves(page)

        print(f"   ✅ Done: Likes={pin_data['likes']} | Comments={pin_data['comments']} | Saves={pin_data['saves']}")

    except Exception as e:
        print(f"   ❌ Error scraping pin: {e}")
    finally:
        await context.close()

    return pin_data


async def simple_pinterest_scraper(query, num_pins=3):
    """Search Pinterest and scrape pins."""
    print(f"\n🎯 Starting scrape for '{query}'...")
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            pin_links = await page.query_selector_all('a[href*="/pin/"]')
            for i, link in enumerate(pin_links[:num_pins]):
                href = await link.get_attribute('href')
                if not href:
                    continue
                pin_url = f"https://www.pinterest.com{href}" if href.startswith('/') else href
                data = await scrape_single_pin(browser, pin_url, i + 1)
                if data:
                    results.append(data)
        except Exception as e:
            print(f"Scraping error: {e}")
        finally:
            await browser.close()
    return results


# --- Main ---

async def main():
    print("🚀 Pinterest + Vision + Engagement Scraper\n" + "=" * 50)

    if not test_vision_api():
        print("❌ Vision API unavailable. Exiting.")
        return

    query = "Women trendy fashion"
    num_pins = 10

    data = await simple_pinterest_scraper(query, num_pins)

    if not data:
        print("❌ No data scraped.")
        return

    filename = "pinterest_vision_engagement.json"
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Completed! {len(data)} pins scraped.")
    print(f"💾 Results saved to {filename}")


if __name__ == "__main__":
    asyncio.run(main())

