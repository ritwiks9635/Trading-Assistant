import yfinance as yf
import requests
from datetime import datetime, timedelta
from core.schemas import CompanyData
import os
from dotenv import load_dotenv

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