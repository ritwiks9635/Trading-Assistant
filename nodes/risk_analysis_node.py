from core.schemas import TradingState
from utils.logger import log_info, log_error
import os, requests, time, math
from statistics import stdev, mean
import yfinance as yf

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def fetch_finnhub_candles(symbol: str, resolution="D", days=90) -> list:
    """Fetch historical close prices (Finnhub)."""
    try:
        to_ts = int(time.time()) - 60
        from_ts = to_ts - days * 86400
        url = f"{FINNHUB_BASE_URL}/stock/candle"
        params = {"symbol": symbol.upper(), "resolution": resolution,
                  "from": from_ts, "to": to_ts, "token": FINNHUB_API_KEY}
        resp = requests.get(url, params=params, timeout=5)  # ✅ fast timeout
        if resp.status_code == 403:
            raise PermissionError("403 Forbidden: Finnhub plan limit")
        resp.raise_for_status()
        data = resp.json()
        return data.get("c", []) if data.get("s") == "ok" else []
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Finnhub candles failed: {e}")
        return []


def fetch_yfinance_prices(symbol: str, period="3mo") -> list:
    """Fallback: use yfinance if Finnhub fails."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval="1d")
        return hist["Close"].dropna().tolist()
    except Exception as e:
        log_error(f"[RiskAnalysisNode] yfinance fallback failed: {e}")
        return []


def fetch_finnhub_beta(symbol: str) -> float | None:
    """Try Finnhub beta, else fallback yfinance."""
    try:
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        resp = requests.get(url, params={"symbol": symbol.upper(), "token": FINNHUB_API_KEY}, timeout=5)
        if resp.status_code == 403:
            raise PermissionError("403 Forbidden: Finnhub plan limit")
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("beta")) if "beta" in data else None
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Finnhub beta failed: {e}")
        # fallback yfinance
        try:
            return float(yf.Ticker(symbol).info.get("beta"))
        except Exception:
            return None


def calculate_volatility(prices: list) -> float:
    try:
        if len(prices) < 30: return 0.0
        returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices) - 1)]
        return round(stdev(returns) * math.sqrt(252), 4)
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Volatility calc failed: {e}")
        return 0.0


def calculate_sharpe_ratio(prices: list, risk_free_rate=0.03) -> float:
    try:
        if len(prices) < 30: return 0.0
        returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices) - 1)]
        excess_returns = [r - (risk_free_rate / 252) for r in returns]
        return round(mean(excess_returns) / stdev(returns) * math.sqrt(252), 2)
    except Exception as e:
        log_error(f"[RiskAnalysisNode] Sharpe calc failed: {e}")
        return 0.0


def risk_analysis_node(state: TradingState) -> TradingState:
    """Compute risk metrics with Finnhub + yfinance fallback."""
    symbol = state.symbol or (state.parsed_query.company_mentioned if state.parsed_query else None)
    if not symbol:
        log_error("[RiskAnalysisNode] No symbol in state")
        state.user_response = "Sorry, I couldn't identify which stock to analyze risk for."
        return state

    # --- Fetch Prices ---
    prices = fetch_finnhub_candles(symbol)
    if not prices:  # fallback
        prices = fetch_yfinance_prices(symbol)

    beta = fetch_finnhub_beta(symbol)
    volatility = calculate_volatility(prices)
    sharpe = calculate_sharpe_ratio(prices)

    if not prices:
        state.user_response = f"⚠️ Could not fetch enough price data for {symbol.upper()} to perform risk analysis."
        return state

    state.risk_analysis = {
        "symbol": symbol.upper(),
        "beta": beta,
        "volatility": volatility,
        "sharpe_ratio": sharpe,
    }

    state.user_response = f"""
📉 **Risk Assessment for {symbol.upper()}**

- **Beta**: {round(beta,2) if beta else 'N/A'}
- **Volatility (Annualized)**: {volatility}
- **Sharpe Ratio**: {sharpe}

> Beta → market correlation  
> Volatility → risk of large swings  
> Sharpe → risk-adjusted return quality
""".strip()

    log_info(f"[RiskAnalysisNode] Risk metrics done for {symbol.upper()}")
    return state
