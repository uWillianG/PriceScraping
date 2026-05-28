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

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
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

## Tests

```powershell
pytest
```
