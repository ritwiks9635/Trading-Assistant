import os
import requests
from utils.logger import log_info, log_error

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

HEADERS = {"User-Agent": "TradingAssistant/1.0"}


def get_alpha_quote(symbol: str) -> dict:
    """
    Fetches real-time stock/ETF quote data.
    Returns price, change %, volume.
    """
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_KEY
        }
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("Global Quote", {})
        return {
            "symbol": symbol.upper(),
            "price": float(data.get("05. price", 0)),
            "change_percent": float(data.get("10. change percent", "0%").strip("%")),
            "volume": int(data.get("06. volume", 0))
        }
    except Exception as e:
        log_error(f"[Alpha] Failed to fetch quote for {symbol}: {e}")
        return {}


def get_alpha_overview(symbol: str) -> dict:
    """
    Fetches company or ETF fundamentals (overview).
    Returns market cap, PE, dividend yield.
    """
    try:
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": ALPHA_KEY
        }
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return {
            "symbol": symbol.upper(),
            "name": data.get("Name", symbol),
            "market_cap": float(data.get("MarketCapitalization", 0)),
            "pe_ratio": float(data.get("PERatio", 0)),
            "dividend_yield": float(data.get("DividendYield", 0)),
            "sector": data.get("Sector", "Unknown"),
            "description": data.get("Description", "N/A")
        }
    except Exception as e:
        log_error(f"[Alpha] Failed to fetch overview for {symbol}: {e}")
        return {}
