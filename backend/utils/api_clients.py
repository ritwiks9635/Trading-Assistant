import yfinance as yf
import requests
from datetime import datetime, timedelta
from core.schemas import CompanyData
import os
from dotenv import load_dotenv
from utils.logger import log_error

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


def get_top_movers(limit=5, timeframe="today") -> list[CompanyData]:
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META", "NFLX", "AMD", "GOOGL", "BABA"]
    results = []

    for symbol in tickers:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="7d" if timeframe != "today" else "1d")
        if hist.empty:
            continue

        open_price = hist["Open"].iloc[0]
        close_price = hist["Close"].iloc[-1]
        change = ((close_price - open_price) / open_price) * 100

        results.append(CompanyData(
            symbol=symbol,
            name=ticker.info.get("shortName"),
            price=close_price,
            percent_change=round(change, 2),
            volume=ticker.info.get("volume"),
            market_cap=ticker.info.get("marketCap")
        ))

    sorted_results = sorted(results, key=lambda x: x.percent_change or 0, reverse=True)
    return sorted_results[:limit]


def get_top_losers(limit=5, timeframe="today") -> list[CompanyData]:
    movers = get_top_movers(limit=50, timeframe=timeframe)
    sorted_losers = sorted(movers, key=lambda x: x.percent_change or 0)
    return sorted_losers[:limit]


def get_budget_picks(limit=5, max_price=10.0) -> list[CompanyData]:
    tickers = ["SIRI", "PLTR", "F", "SOFI", "INTC", "NOK", "T", "GPRO", "CHPT"]
    results = []

    for symbol in tickers:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice")

        if price and price <= max_price:
            results.append(CompanyData(
                symbol=symbol,
                name=info.get("shortName"),
                price=price,
                percent_change=info.get("regularMarketChangePercent"),
                volume=info.get("volume"),
                market_cap=info.get("marketCap")
            ))

    sorted_picks = sorted(results, key=lambda x: x.market_cap or 0)
    return sorted_picks[:limit]


def get_company_symbols_by_region(region: str):
    """Return list of company objects (or minimal dicts) for region using available APIs."""
    from core.schemas import CompanyData

    # Example stub; replace with your API integrations (Alpha Vantage, Finnhub, etc.)
    region = region.lower()
    if region == "india":
        tickers = [
            CompanyData(symbol="RELIANCE.NS", name="Reliance Industries", price=2860.5, percent_change=1.2, market_cap=1.9e12),
            CompanyData(symbol="TCS.NS", name="Tata Consultancy", price=3810.6, percent_change=0.8, market_cap=1.4e12),
        ]
    elif region == "japan":
        tickers = [
            CompanyData(symbol="7203.T", name="Toyota Motor Corp", price=2450.2, percent_change=0.5, market_cap=2.0e12),
            CompanyData(symbol="6758.T", name="Sony Group", price=12550.3, percent_change=-0.3, market_cap=1.3e12),
        ]
    elif region == "china":
        tickers = [
            CompanyData(symbol="600519.SS", name="Kweichow Moutai", price=1780.9, percent_change=0.4, market_cap=2.2e12),
            CompanyData(symbol="9988.HK", name="Alibaba", price=78.3, percent_change=0.2, market_cap=1.8e12),
        ]
    else:
        tickers = []
    return tickers

def get_company_data(symbol: str) -> CompanyData | None:
    """
    Fetch company data globally using Yahoo Finance (yfinance).
    Handles tickers like:
      - US: TSLA, AAPL
      - India: TCS.NS, RELIANCE.NS
      - Japan: 7203.T
      - Hong Kong: 9988.HK
    Always returns a CompanyData object or None.
    """
    try:
        if not symbol:
            return None

        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Basic validation — avoid broken responses
        if not info or "shortName" not in info:
            return None

        price = info.get("regularMarketPrice")
        if price is None:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]

        return CompanyData(
            symbol=symbol,
            name=info.get("shortName"),
            price=price,
            percent_change=info.get("regularMarketChangePercent"),
            volume=info.get("volume"),
            market_cap=info.get("marketCap"),
            summary=info.get("longBusinessSummary", "No summary available."),
        )

    except Exception as e:
        log_error(f"[get_company_data] ❌ Failed to fetch data for {symbol}: {e}")
        return None