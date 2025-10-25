# README — Fashion Product Scraper & Keyword Matcher (Python Script)

## Overview
This Python script automates the extraction of **product listings** and **image/text data** from **Zara** and **H&M “New Arrivals”** pages using Apify actors.  
It reads keywords from a text file and generates structured CSV reports showing which trends are most visible across these brands — forming the **foundation for GAP’s saturation analysis** in the AI-assisted design workflow.

The scraper automatically handles connection issues (e.g., `403 Forbidden`) and continues crawling until the desired number of products are collected.

---

## 1. Inputs

### Required File
- **`keywords.txt`** — a plain text file containing one keyword per line.  
  Example:
  ```
  knit sweater
  cargo pants
  maxi dress
  pleated skirt
  ```

---

## 2. How to Run
Run the following command in your terminal or PowerShell:

```bash
python .\scraper.py
```

The script will:
1. Initialize the **Apify Client** using your API key (from `config.py`).
2. Begin scraping Zara’s **“What’s New”** section for both *Women* and *Men*.
3. Move on to scrape H&M’s **New Arrivals**, iterating through multiple pages.
4. Collect product names, prices, and currencies.
5. Match product titles against your keyword list.
6. Export clean, structured CSV reports in the `/output` directory.

---

## 3. Output Files

| File | Description |
|------|--------------|
| `zara_products.csv` | All scraped products from Zara (name, price, section). |
| `hm_products.csv` | All scraped products from H&M. |
| `keyword_matches.csv` | Keyword frequency matches across brands — used to calculate saturation scores. |

---

## 4. Features

-  **Dual-source scraping:** pulls data from both Zara and H&M.  
-  **Auto-retry handling:** surpasses `403` or timeout errors using Apify proxy rotation.  
-  **Configurable limits:** adjusts `max_items` to control scraping volume.  
-  **Keyword matching:** automatically tallies trend frequencies for later AI analysis.  
-  **Export-ready data:** outputs CSVs compatible with the GAP Design Matrix pipeline.

---

## 5. Requirements

Ensure you have the following installed:

```bash
pip install apify-client pandas
```

Also, include your **Apify API key** in a `config.py` file located in the same directory:
```python
APIFY_API_KEY = "your_apify_key_here"
```

---

## 6. Example Log Output
```
 Scraping Zara What's New (Men's + Women's)...
   ✓ Total Zara products: 980
 Scraping H&M New Arrivals...
   Fetching 35 pages to get ~500 products...
   ✓ Total H&M products: 490
 Keyword matching complete.
```

---

## 7. Notes
- Occasional “403 blocked” messages are normal — the script will **auto-bypass** them.  
- Zara and H&M frequently update layouts; rerun the script periodically to refresh data.  
- Results feed into the **trend saturation scoring system** used by the Creativity Director Assistant.
