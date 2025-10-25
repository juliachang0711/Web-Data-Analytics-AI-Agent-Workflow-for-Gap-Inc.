README — Creativity Director Assistant (Dify Workflow)

Overview:
This workflow analyzes search and social signals to identify which fashion or lifestyle trends are currently gaining momentum.
It uses two data sources:

Google Trends via SerpAPI → calculates a Saturation Score (how mature or plateaued a trend is).

TikTok via Apify → calculates a Momentum Score (how fast a trend is gaining attention).

Both are combined into a final structured summary for each trend keyword.

1. Inputs (required in the Start node)

category → The overarching product or theme.
Example: Women's Outerwear

region → Google Trends region code.
Example: US, GB, IN

timeframe → Google Trends time window.
Example: today 12-m or today 3-m

brands_str → Comma-separated brand names for contextual insights.
Example: Old Navy, Gap, Banana Republic

seed_terms_json → A JSON array of keywords to analyze.
Example:
["puffer jacket", "trench coat", "wool blazer"]

2. API keys required

SERPAPI_KEY → SerpAPI key for Google Trends access.

APIFY_TOKEN → Apify token for TikTok hashtag scraper.

3. What the workflow does

Reads your inputs and loops over each term in seed_terms_json.

Calls SerpAPI to fetch normalized search interest for that term over time.

Calculates Saturation Score based on trend peaks, slopes, and stability.

Calls Apify TikTok scraper with that same term.

Aggregates likes, comments, and shares from recent posts.

Calculates Momentum Score (0–1) using an exponential normalization.

Combines both metrics into one JSON summary per keyword.

Generates a readable summary report highlighting:

High-momentum, low-saturation = emerging trends

Low-momentum, high-saturation = mature or fading trends

4. How to run

Import the workflow file into Dify.

Go to the Start node and fill in:

category, region, timeframe, brands_str, seed_terms_json

Click Run.

Wait for all iterations to complete — the final LLM node will generate a summarized output.

5. Example output
[
  {
    "term": "puffer jacket",
    "momentum_score": 0.82,
    "saturation_score": 0.47
  },
  {
    "term": "trench coat",
    "momentum_score": 0.31,
    "saturation_score": 0.72
  }
]

6. Notes

If SerpAPI or Apify requests fail, the workflow automatically assigns 0.0 as a default score.

You can re-run with different timeframe or region to compare seasonal or geographic shifts.

All scores are normalized (0–1) for easy comparison across sources.

README — Pinterest Visual Score API

Purpose:
This API estimates the visual engagement score of a trend or keyword on Pinterest by visiting the top few pin links and averaging their like counts. It outputs a normalized score between 0 and 1 that reflects how visually appealing or viral a term is on the platform.

HOW IT WORKS

Receives a search term (for example: "puffer jacket").

Opens Pinterest’s public search results for that term.

Visits the first few pin links.

Extracts the number of likes or reactions from each pin using specific HTML selectors.

Computes the average likes per pin and converts it to a normalized score using an exponential function.

Example output:
{
"term": "puffer jacket",
"pinterest_score": 0.67
}

SETUP INSTRUCTIONS

Requirements:

Python 3.9 or higher

Playwright (for headless Chromium scraping)

Flask (for API hosting)

Installation:
pip install flask playwright
playwright install chromium

Run Locally:

Unzip the project folder.

In the terminal, navigate into the directory.

Run the command:
python app.py

The API will start locally at:
http://127.0.0.1:5000/pinterest_score

API ENDPOINT

POST /pinterest_score

Request body:
{
"term": "puffer jacket",
"num_pins": 3,
"delay_ms_search": 5000,
"delay_ms_pin": 3000,
"scale": 150.0
}

Parameter description:
term string Required. The search keyword to analyze.
num_pins integer Optional. Default 3. Number of pins to sample.
delay_ms_search integer Optional. Default 5000. Delay after loading search results in milliseconds.
delay_ms_pin integer Optional. Default 3000. Delay after opening each pin in milliseconds.
scale float Optional. Default 150.0. Normalization constant for score scaling.

Example response:
{
"term": "trench coat",
"pinterest_score": 0.732
}

SCORE CALCULATION

Extracts all visible like counts using the following CSS selectors:
.X8m.zDA.IZT.eSP.dyH.llN.Kv8
[data-test-id="aggregated-reactions-container"]
[data-test-id="reactions-count-button"]

Converts shorthand counts (for example, 2.3K becomes 2300).

Computes the average likes per pin.

Applies exponential normalization:
score = 1 - exp(-avg_likes / scale)

The result is clamped between 0 and 1, rounded to three decimals.

DEPLOYMENT OPTIONS

Option 1: Run Locally
Simply keep the Flask app running in your terminal and call:
POST http://127.0.0.1:5000/pinterest_score

Option 2: Deploy Online
You can deploy this app to Render, Azure, or Railway.
Use the included requirements.txt and Procfile.
Set the start command as:
python app.py
Ensure that Chromium is installed in the deployment environment (Playwright handles this automatically).

After deployment, your public endpoint will look like:
https://your-app-name.onrender.com/pinterest_score

INTEGRATION WITH DIFY

You can compute the score for each term through this API and integrate that into the dify input process in the future

INSTRUCTIONS FOR PINTEREST SCRAPER NON API VERS.

first you must edit this section of code to include your specific Google API key: 

GOOGLE_VISION_API_KEY = "YOUR KEY HERE"  # 🔒 replace with your real key
GOOGLE_VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"

YOU MUST HAVE THE GOOGLE VISION AI API KEY ACTIVATED AND BILLING ENABLED FOR THIS TO WORK
Next, in the part of the code labeled "main" you will find the following: 

 query = "Your Query Here"
    num_pins = 10

This is where you will modify the code to search for your specific query, and how many pins you want to scrape and analyze

The bash command to use this code is "python pyhtonscraper.py" 
After running all contents will be stored in a Json file in the same directory as where you are running the program

