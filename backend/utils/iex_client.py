# utils/iex_client.py
# Production-grade IEX Cloud integration wrapper

import os
import requests
from utils.logger import log_info, log_error

IEX_TOKEN = os.getenv("IEX_API_TOKEN")
BASE_URL = "https://cloud.iexapis.com/stable"


def get_iex_quote(symbol: str) -> dict:
    try:
        url = f"{BASE_URL}/stock/{symbol}/quote?token={IEX_TOKEN}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_error(f"[IEX] Failed to fetch quote for {symbol}: {e}")
        return {}


def get_iex_stats(symbol: str) -> dict:
    try:
        url = f"{BASE_URL}/stock/{symbol}/stats?token={IEX_TOKEN}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_error(f"[IEX] Failed to fetch stats for {symbol}: {e}")
        return {}


def get_iex_advanced(symbol: str) -> dict:
    """
    Optionally combine quote + stats into one payload.
    """
    quote = get_iex_quote(symbol)
    stats = get_iex_stats(symbol)
    return {"quote": quote, "stats": stats}
