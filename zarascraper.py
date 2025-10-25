"""
Fashion Product Scraper & Keyword Matcher
Scrapes Zara and H&M new arrivals, matches keywords, and generates reports
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from apify_client import ApifyClient
from config import APIFY_API_KEY

# Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def scrape_zara(client, max_items=500):
    """Scrape Zara What's New pages for both men's and women's sections"""
    logger.info("📦 Scraping Zara What's New (Men's + Women's)...")
    
    try:
        all_products = []
        
        # Scrape Women's What's New
        logger.info("   Fetching Women's section...")
        run_women = client.actor("karamelo/zara-scraper").call(run_input={
            "startUrls": ["https://www.zara.com/us/en/woman-new-in-l1180.html"],
            "maxItems": max_items,
            "proxyConfiguration": {"useApifyProxy": True}
        })
        
        items_women = client.dataset(run_women["defaultDatasetId"]).list_items().items
        for item in items_women:
            all_products.append({
                'name': item.get('name', '').strip(),
                'price': item.get('price', ''),
                'currency': item.get('currency', 'USD'),
                'section': 'Women'
            })
        
        logger.info(f"      Got {len(items_women)} women's products")
        
        # Scrape Men's What's New
        logger.info("   Fetching Men's section...")
        run_men = client.actor("karamelo/zara-scraper").call(run_input={
            "startUrls": ["https://www.zara.com/us/en/man-new-in-l1180.html"],
            "maxItems": max_items,
            "proxyConfiguration": {"useApifyProxy": True}
        })
        
        items_men = client.dataset(run_men["defaultDatasetId"]).list_items().items
        for item in items_men:
            all_products.append({
                'name': item.get('name', '').strip(),
                'price': item.get('price', ''),
                'currency': item.get('currency', 'USD'),
                'section': 'Men'
            })
        
        logger.info(f"      Got {len(items_men)} men's products")
        logger.info(f"   ✓ Total Zara products: {len(all_products)}")
        return all_products
        
    except Exception as e:
        logger.error(f"   ✗ Zara error: {e}")
        return []


def scrape_hm(client, max_items=500):
    """Scrape H&M New Arrivals page - fetches multiple pages to get more products"""
    logger.info("📦 Scraping H&M New Arrivals...")
    
    try:
        products = []
        page = 1
        products_per_page = 14  # H&M returns ~14 products per page
        
        # Calculate how many pages we need to fetch
        pages_needed = min((max_items // products_per_page) + 1, 68)  # Max 68 pages available
        
        logger.info(f"   Fetching {pages_needed} pages to get ~{max_items} products...")
        
        while len(products) < max_items and page <= pages_needed:
            logger.info(f"   Fetching page {page}...")
            
            run = client.actor("pintostudio/hm-product-new-arrivals").call(run_input={
                "maxItems": 500,
                "page": str(page),  # Page parameter must be a string
                "proxyConfiguration": {"useApifyProxy": True}
            })
            
            # Get products from this page
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                if 'products' in item:
                    for product in item['products']:
                        # Get price from prices array (use redPrice if available, else first price)
                        price = None
                        if 'prices' in product and product['prices']:
                            red_price = next((p for p in product['prices'] if p.get('priceType') == 'redPrice'), None)
                            if red_price:
                                price = red_price.get('formattedPrice')
                            else:
                                price = product['prices'][0].get('formattedPrice')
                        
                        products.append({
                            'name': product.get('productName', '').strip(),
                            'price': price,
                            'currency': 'USD'
                        })
                        
                        # Stop if we've reached the desired number
                        if len(products) >= max_items:
                            break
                
                if len(products) >= max_items:
                    break
            
            page += 1
        
        logger.info(f"   ✓ Got {len(products)} H&M products from {page - 1} pages")
        return products
        
    except Exception as e:
        logger.error(f"   ✗ H&M error: {e}")
        return []


def save_products_csv(products, platform, timestamp):
    """Save products to CSV file"""
    filename = OUTPUT_DIR / f"{platform.lower()}_products_{timestamp}.csv"
    
    # Determine fieldnames based on whether 'section' exists
    if products and 'section' in products[0]:
        fieldnames = ['name', 'price', 'currency', 'section']
    else:
        fieldnames = ['name', 'price', 'currency']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
    
    logger.info(f"   ✓ Saved to {filename}")
    return filename


def load_keywords(file_path="keywords.txt"):
    """Load keywords from file"""
    keywords = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                keywords.append(line.lower())
    return keywords


def match_keyword(product_name, keyword):
    """Check if keyword matches product name (all words must be present)"""
    product_lower = product_name.lower()
    keyword_words = keyword.split()
    return all(word in product_lower for word in keyword_words)


def analyze_keywords(keywords, zara_products, hm_products):
    """Match keywords against products and count matches"""
    results = []
    
    logger.info("\n🔍 Analyzing keyword matches...")
    
    for keyword in keywords:
        # Count matches
        zara_matches = sum(1 for p in zara_products if match_keyword(p['name'], keyword))
        hm_matches = sum(1 for p in hm_products if match_keyword(p['name'], keyword))
        total = zara_matches + hm_matches
        
        results.append({
            'keyword': keyword,
            'zara_matches': zara_matches,
            'hm_matches': hm_matches,
            'total_matches': total
        })
        
        logger.info(f"   {keyword}: Zara={zara_matches}, H&M={hm_matches}")
    
    return results


def save_keyword_matches(results, timestamp):
    """Save keyword match results to CSV"""
    filename = OUTPUT_DIR / f"keyword_matches_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'keyword', 'zara_matches', 'hm_matches', 'total_matches'
        ])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"\n✓ Keyword analysis saved to {filename}")
    return filename


def print_summary(results):
    """Print formatted summary"""
    print("\n" + "="*80)
    print("KEYWORD MATCH SUMMARY")
    print("="*80)
    print(f"\n{'KEYWORD':<25} {'ZARA':<10} {'H&M':<10} {'TOTAL':<10}")
    print("-"*80)
    
    for r in results:
        print(f"{r['keyword']:<25} {r['zara_matches']:<10} {r['hm_matches']:<10} {r['total_matches']:<10}")
    
    print("-"*80)
    print("="*80)


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("FASHION SCRAPER & KEYWORD MATCHER")
    print("="*80 + "\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client = ApifyClient(APIFY_API_KEY)
    
    # Step 1: Scrape products
    logger.info("STEP 1: Scraping Products\n")
    zara_products = scrape_zara(client, max_items=500)
    hm_products = scrape_hm(client, max_items=200)  # Get 200 H&M products (~15 pages)
    
    if not zara_products and not hm_products:
        logger.error("\n✗ No products scraped from either platform")
        return
    
    # Step 2: Save product CSVs
    logger.info("\nSTEP 2: Saving Product Lists\n")
    if zara_products:
        save_products_csv(zara_products, "Zara", timestamp)
    if hm_products:
        save_products_csv(hm_products, "HM", timestamp)
    
    # Step 3: Load keywords and analyze
    logger.info("\nSTEP 3: Keyword Analysis\n")
    keywords = load_keywords()
    logger.info(f"   Loaded {len(keywords)} keywords")
    
    results = analyze_keywords(keywords, zara_products, hm_products)
    
    # Step 4: Save keyword matches
    logger.info("\nSTEP 4: Saving Results\n")
    save_keyword_matches(results, timestamp)
    
    # Print summary
    print_summary(results)
    
    print("\n✓ Done! Check the 'output' folder for all CSV files.\n")


if __name__ == "__main__":
    main()
