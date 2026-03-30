import os
import time
import math
import requests
import yfinance as yf
from statistics import stdev, mean
from typing import List, Optional
from core.schemas import TradingState
from utils.logger import log_info, log_error
from state.shared_state import shared_state

# ---------------- Configuration ----------------
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
YF_FALLBACK_PERIOD = "3mo"


# ---------------- Utility Fetchers ----------------
def fetch_finnhub_candles(symbol: str, resolution: str = "D", days: int = 90) -> List[float]:
    """Fetch daily closing prices via Finnhub (fallback-safe)."""
    if not FINNHUB_API_KEY:
        log_error("[RiskAnalysisNode] Missing FINNHUB_API_KEY in environment.")
        return []

    try:
        now = int(time.time()) - 60
        start = now - days * 86400
        url = f"{FINNHUB_BASE_URL}/stock/candle"
        params = {
            "symbol": symbol.upper(),
            "resolution": resolution,
            "from": start,
            "to": now,
            "token": FINNHUB_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 403:
            raise PermissionError("403 Forbidden: Finnhub plan limit reached.")
        resp.raise_for_status()
        data = resp.json()
        return data.get("c", []) if data.get("s") == "ok" else []
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Finnhub candle fetch failed for {symbol}: {e}")
        return []


def fetch_yfinance_prices(symbol: str, period: str = YF_FALLBACK_PERIOD) -> List[float]:
    """Fallback to yfinance for historical prices."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval="1d", auto_adjust=True)
        if hist.empty:
            raise ValueError("Empty dataframe from yfinance.")
        return hist["Close"].dropna().tolist()
    except Exception as e:
        log_error(f"[RiskAnalysisNode] yfinance price fallback failed for {symbol}: {e}")
        return []


def fetch_finnhub_beta(symbol: str) -> Optional[float]:
    """Retrieve Beta value from Finnhub or fallback to yfinance."""
    if not FINNHUB_API_KEY:
        log_error("[RiskAnalysisNode] No API key — skipping Finnhub beta fetch.")
        return None
    try:
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        resp = requests.get(url, params={"symbol": symbol.upper(), "token": FINNHUB_API_KEY}, timeout=5)
        if resp.status_code == 403:
            raise PermissionError("403 Forbidden: Finnhub plan limit reached.")
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("beta")) if "beta" in data else None
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Finnhub beta fetch failed for {symbol}: {e}")
        try:
            info = yf.Ticker(symbol).info
            return float(info.get("beta")) if "beta" in info else None
        except Exception:
            return None


# ---------------- Calculations ----------------
def calculate_volatility(prices: List[float]) -> float:
    """Compute annualized volatility from price series."""
    try:
        if len(prices) < 30:
            return 0.0
        returns = [(prices[i + 1] - prices[i]) / prices[i] for i in range(len(prices) - 1) if prices[i] > 0]
        return round(stdev(returns) * math.sqrt(252), 4)
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Volatility calculation failed: {e}")
        return 0.0


def calculate_sharpe_ratio(prices: List[float], risk_free_rate: float = 0.03) -> float:
    """Compute annualized Sharpe ratio."""
    try:
        if len(prices) < 30:
            return 0.0
        returns = [(prices[i + 1] - prices[i]) / prices[i] for i in range(len(prices) - 1) if prices[i] > 0]
        excess = [r - (risk_free_rate / 252) for r in returns]
        return round(mean(excess) / stdev(returns) * math.sqrt(252), 2)
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Sharpe ratio calculation failed: {e}")
        return 0.0


# ---------------- Main Node ----------------
def risk_analysis_node(state: TradingState, user_id: str = "default_user") -> TradingState:
    """
    Perform global risk analysis for any stock symbol.

    ✅ Fetches data globally via Finnhub (fallback: yfinance)
    ✅ Calculates Beta, Volatility, Sharpe Ratio
    ✅ Integrates with shared_state for persistent memory
    ✅ Handles API, timeout, and data edge cases
    ✅ Never crashes — always returns clean, professional output
    """

    # --- Determine symbol ---
    symbol = (
        (state.symbol or getattr(state.parsed_query, "company_mentioned", None))
        or shared_state.get_global("last_company_symbol")
        or ""
    ).upper().strip()

    if not symbol:
        log_error("[RiskAnalysisNode] No symbol detected in state or memory.")
        state.user_response = "⚠️ I couldn’t identify which stock to analyze. Please specify a valid company or ticker."
        return state

    log_info(f"[RiskAnalysisNode] Starting risk analysis for {symbol}...")

    # --- Multi-source data fetch ---
    prices = fetch_finnhub_candles(symbol)
    if not prices:
        prices = fetch_yfinance_prices(symbol)

    beta = fetch_finnhub_beta(symbol)

    if not prices:
        state.user_response = (
            f"⚠️ Unable to retrieve sufficient price data for {symbol}. "
            f"Please try another symbol or extend the timeframe."
        )
        return state

    # --- Metrics calculation ---
    volatility = calculate_volatility(prices)
    sharpe = calculate_sharpe_ratio(prices)

    # --- Structured result ---
    result = {
        "symbol": symbol,
        "beta": beta,
        "volatility": volatility,
        "sharpe_ratio": sharpe,
        "source": "Finnhub" if FINNHUB_API_KEY else "yfinance",
    }

    state.risk_analysis = result
    shared_state.update_user_state(user_id, "risk_analysis", result)
    shared_state.set_global("last_risk_symbol", symbol)

    # --- Human-readable summary ---
    beta_txt = f"{round(beta, 2)}" if beta is not None else "N/A"
    msg = f"""
📊 **Global Risk Analysis: {symbol}**

• **Beta:** {beta_txt}  
• **Volatility (Annualized):** {volatility}  
• **Sharpe Ratio:** {sharpe}  

**Interpretation**
- *Beta* → Measures market correlation (≥1 = high risk exposure).  
- *Volatility* → Indicates daily price fluctuation (risk level).  
- *Sharpe Ratio* → Shows risk-adjusted returns (≥1 = strong performance).  

Data Source: {result['source']}
"""

    state.user_response = msg.strip()
    log_info(f"[RiskAnalysisNode] ✅ Completed global risk analysis for {symbol}.")
    return state
