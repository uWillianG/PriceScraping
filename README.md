<<<<<<< HEAD
# PriceScraping
=======
# Home Shopping Price Assistant

A local Python assistant for monitoring Brazilian e-commerce prices across home-shopping categories such as furniture, appliances, electronics, and home decor.

## What works in v1

- Mercado Livre public search through the official API.
- API-ready adapters for Amazon Brasil, Shopee Brasil, Magazine Luiza, and Casas Bahia.
- Concurrent price collection with unified `ProductOffer` data.
- SQLite price history.
- Fake discount checks against historical prices.
- Alert rules for target price, discount percent, and historical lows.
- SMTP HTML email summaries.
- FastAPI dashboard with tracked products, alerts, and Chart.js price history.

The project avoids aggressive scraping for stores with strong bot protection. Configure official or partner endpoints in `.env` where available.

## Store reliability notes

Some Brazilian stores serve Akamai/CAPTCHA/anti-crawler pages to automated browsers. When that happens, the app saves the received page under `data/debug/` and reports that the store blocked automated access.

- Mercado Livre: works best through the implemented HTML/Playwright fallback, or through an authenticated API token.
- Amazon Brasil: scraping may return 503/CAPTCHA; PA-API credentials are the reliable path.
- Magazine Luiza: often returns an Akamai bot page; use `MAGALU_SEARCH_ENDPOINT` and `MAGALU_API_TOKEN` if you have partner access.
- Casas Bahia: often returns an Akamai custom deny page; use `CASAS_BAHIA_SEARCH_ENDPOINT` and `CASAS_BAHIA_API_TOKEN` if you have partner access.
- Shopee Brasil: often loads anti-crawler scripts without search results; use `SHOPEE_AFFILIATE_ENDPOINT` and partner credentials if available.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
python main.py
```

## Search from the command line

```powershell
python main.py "geladeira frost free" --category appliances
```

## Run the dashboard

```powershell
uvicorn shopping_assistant.dashboard.app:app --reload
```

Open http://127.0.0.1:8000.

If Mercado Livre returns no static results, the collector uses Playwright to render the JavaScript page. Run `python -m playwright install chromium` once after installing requirements.

## Tests

```powershell
pytest
```
>>>>>>> 4ab9a01 (primeiro commit)
