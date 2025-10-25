
# 🧠 Project TikTok
**Reproducible Notebook for TikTok Data Extraction and Analysis**

This project demonstrates how to use the **Apify API** to collect TikTok data programmatically and perform basic processing or analysis in Python.  
The notebook is designed to be reproducible, requiring only an Apify account and a valid API token.

---

## 📂 Project Structure

```
Project_tiktok.ipynb     # Main Jupyter notebook
README.md                # Documentation file (this file)
```

---

## 1. Environment Setup

This project runs entirely on **Google Colab**, so no local setup is required.

To reproduce the results:
1. Open the notebook in Google Colab.  
2. Run all cells sequentially.  
3. Make sure to install dependencies inside Colab using the first cell (which installs `apify-client`).
```

### b. Install dependencies
All required packages can be installed directly from the first cell of the notebook, or manually with:
```bash
pip install apify-client pandas
```

> **Tip:** If your notebook includes additional libraries (like `matplotlib`, `seaborn`, or `numpy`), you can install them the same way:
> ```bash
> pip install matplotlib seaborn numpy
> ```

---

## 2. Apify API Setup

1. Go to [https://console.apify.com](https://console.apify.com).  
2. Log in or create a free account.  
3. Navigate to your **Account → Integrations → API Tokens**.  
4. Copy your **API Token**.  
5. In the notebook, store your token in a variable or environment variable, for example:
   ```python
   from apify_client import ApifyClient
   client = ApifyClient("your_apify_api_token_here")
   ```

---

## 3. How to Run the Notebook

### Option 1: Run in Jupyter Notebook
1. Launch Jupyter:
   ```bash
   jupyter notebook
   ```
2. Open `Project_tiktok.ipynb`.
3. Run all cells sequentially:  
   **Kernel → Restart & Run All**

### Option 2: Run in VS Code or JupyterLab
Open the notebook and click **“Run All Cells”** in the toolbar.

---

## 4. Expected Outputs

After running all cells, the notebook will:

- Connect to the **Apify API** to fetch TikTok post data (including views, likes, comments, shares, etc.).
- Calculate a **Popularity Score** for each post.
- Identify and label posts as either:
  - **🔥 Resurging Trend** — content showing renewed popularity, or  
  - **Non-Resurging** — recent but not trending again.
- Print two ranked lists in the output:

---

## Reproducing Results

- To reproduce results:
  Simply open the notebook in Google Colab, insert your Apify API token, and run all cells in order..
- TikTok’s data accessibility depends on Apify’s actors and TikTok’s current API limits.
- If you encounter errors like *“Rate limit exceeded”* or *“Unauthorized”*, regenerate your Apify token.
- The project is for **educational and analytical use** only — follow TikTok’s [Terms of Service](https://www.tiktok.com/legal/terms-of-service).

---

## Author
- **Author:** Julia Chang
