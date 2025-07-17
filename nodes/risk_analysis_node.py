from core.schemas import TradingState
from utils.logger import log_info, log_error
import os
import requests
from statistics import stdev, mean
import math
import time

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def fetch_finnhub_candles(symbol: str, resolution: str = "D", days: int = 365):
    """
    Fetch historical close prices for volatility and Sharpe calculation.
    """
    try:
        to_ts = int(time.time())
        from_ts = to_ts - days * 86400
        url = f"{FINNHUB_BASE_URL}/stock/candle"
        params = {
            "symbol": symbol.upper(),
            "resolution": resolution,
            "from": from_ts,
            "to": to_ts,
            "token": FINNHUB_API_KEY
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("s") != "ok":
            raise ValueError("Invalid response or insufficient data.")
        return data.get("c", [])  # close prices
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Failed to fetch price data: {e}")
        return []


def fetch_finnhub_beta(symbol: str):
    try:
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        params = {"symbol": symbol.upper(), "token": FINNHUB_API_KEY}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("beta")
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Failed to fetch beta: {e}")
        return None


def calculate_volatility(prices: list) -> float:
    if len(prices) < 30:
        return 0.0
    returns = [(prices[i+1] - prices[i])/prices[i] for i in range(len(prices)-1)]
    return round(stdev(returns) * math.sqrt(252), 4)  # Annualized volatility


def calculate_sharpe_ratio(prices: list, risk_free_rate=0.03):
    if len(prices) < 30:
        return 0.0
    returns = [(prices[i+1] - prices[i])/prices[i] for i in range(len(prices)-1)]
    excess_returns = [r - (risk_free_rate / 252) for r in returns]
    return round(mean(excess_returns) / stdev(returns) * math.sqrt(252), 2)


def risk_analysis_node(state: TradingState) -> TradingState:
    """
    Computes Beta, Volatility, and Sharpe Ratio for the symbol using Finnhub.
    """
    symbol = state.symbol or (state.parsed_query.company_mentioned if state.parsed_query else None)

    if not symbol:
        log_error("[RiskAnalysisNode] Missing symbol in state.")
        state.user_response = "Sorry, I couldn't identify which stock to analyze risk for."
        return state

    if not FINNHUB_API_KEY:
        log_error("[RiskAnalysisNode] FINNHUB_API_KEY is not set.")
        state.user_response = "Internal configuration error."
        return state

    try:
        prices = fetch_finnhub_candles(symbol)
        beta = fetch_finnhub_beta(symbol)
        volatility = calculate_volatility(prices)
        sharpe = calculate_sharpe_ratio(prices)

        response = f"""
📉 **Risk Assessment for {symbol.upper()}**

- **Beta**: {round(beta, 2) if beta else 'N/A'}
- **Volatility (Annualized)**: {volatility}
- **Sharpe Ratio**: {sharpe}

> Beta reflects market correlation.
> Volatility shows standard deviation of returns.
> Sharpe indicates return vs risk (risk-adjusted return).
"""
        state.user_response = response.strip()
        log_info(f"[RiskAnalysisNode] Risk metrics calculated for {symbol.upper()}.")

    except Exception as e:
        log_error(f"[RiskAnalysisNode] Error: {e}")
        state.user_response = f"Sorry, I couldn't calculate risk metrics for {symbol.upper()} at this time."

    return state
