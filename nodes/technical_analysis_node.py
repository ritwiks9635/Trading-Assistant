from core.schemas import TradingState
from utils.logger import log_info, log_error
import os
import requests

FINNHUB_API = "https://finnhub.io/api/v1"
API_KEY = os.getenv("FINNHUB_API_KEY")

def fetch_finnhub_indicator(symbol: str, indicator: str, params: dict = {}) -> dict:
    url = f"{FINNHUB_API}/indicator"
    query = {
        "symbol": symbol.upper(),
        "resolution": "D",
        "from": params.get("from"),
        "to": params.get("to"),
        "indicator": indicator,
        "token": API_KEY,
        **params.get("params", {})
    }

    try:
        response = requests.get(url, params=query)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_error(f"[Finnhub] Failed to fetch {indicator} for {symbol}: {e}")
        return {}

def technical_analysis_node(state: TradingState) -> TradingState:
    """
    Uses Finnhub API to calculate RSI, MACD, MA, Bollinger Bands.
    """
    symbol = state.symbol or (state.parsed_query.company_mentioned if state.parsed_query else None)

    if not symbol:
        log_error("[TechnicalAnalysisNode] Missing symbol.")
        state.user_response = "Sorry, I couldn't identify which stock you're referring to."
        return state

    if not API_KEY:
        log_error("[TechnicalAnalysisNode] FINNHUB_API_KEY is not set.")
        state.user_response = "Internal configuration error. Missing API credentials."
        return state

    try:
        import time
        to_ts = int(time.time())
        from_ts = to_ts - 60 * 60 * 24 * 200  # Last 200 days

        # Fetch RSI
        rsi_data = fetch_finnhub_indicator(symbol, "rsi", {"from": from_ts, "to": to_ts, "params": {"timeperiod": 14}})
        rsi = rsi_data.get("rsi", [-1])[-1]

        # Fetch MACD
        macd_data = fetch_finnhub_indicator(symbol, "macd", {"from": from_ts, "to": to_ts})
        macd_val = macd_data.get("macd", [-1])[-1]
        macd_signal = macd_data.get("signal", [-1])[-1]

        # Fetch Moving Averages
        ma_50_data = fetch_finnhub_indicator(symbol, "sma", {"from": from_ts, "to": to_ts, "params": {"timeperiod": 50}})
        ma_200_data = fetch_finnhub_indicator(symbol, "sma", {"from": from_ts, "to": to_ts, "params": {"timeperiod": 200}})
        ma_50 = ma_50_data.get("sma", [-1])[-1]
        ma_200 = ma_200_data.get("sma", [-1])[-1]

        # Fetch Bollinger Bands
        bb_data = fetch_finnhub_indicator(symbol, "bbands", {"from": from_ts, "to": to_ts})
        upper = bb_data.get("upperband", [-1])[-1]
        lower = bb_data.get("lowerband", [-1])[-1]
        price = bb_data.get("real", [-1])[-1]
        position = (
            "above the upper band 📈" if price > upper else
            "below the lower band 📉" if price < lower else
            "within the normal range"
        )

        # --- Response
        response = f"""
📊 **Technical Analysis for {symbol.upper()}**

- **RSI (14-day)**: {round(rsi, 2)} {'(Overbought)' if rsi > 70 else '(Oversold)' if rsi < 30 else ''}
- **MACD**: {round(macd_val, 2)} | Signal: {round(macd_signal, 2)}
- **50-Day MA**: ${round(ma_50, 2)}
- **200-Day MA**: ${round(ma_200, 2)}
- **Bollinger Bands**: Price is currently *{position}*
"""
        state.user_response = response.strip()
        log_info(f"[TechnicalAnalysisNode] Successfully analyzed {symbol}.")

    except Exception as e:
        log_error(f"[TechnicalAnalysisNode] Failed for {symbol}: {e}")
        state.user_response = f"Sorry, I couldn't compute technical indicators for {symbol.upper()}."

    return state
