from core.schemas import TradingState, TechnicalAnalysis
from utils.logger import log_info, log_error
import yfinance as yf
import pandas as pd
import time
from typing import Optional, Tuple, Dict

# ---------- Simple cache for yfinance ----------
_YF_CACHE: Dict[str, Dict[str, object]] = {}
_YF_TTL_SEC = 300

def _get_yf_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    now = time.time()
    cached = _YF_CACHE.get(symbol)
    if cached and now - cached["ts"] < _YF_TTL_SEC:
        return cached["data"]

    t = yf.Ticker(symbol)
    hist = t.history(period=period)
    _YF_CACHE[symbol] = {"ts": now, "data": hist}
    return hist

# ---------- Indicator Calculations ----------
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    try:
        delta = df["Close"].diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = -delta.clip(upper=0).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi.iloc[-1]), 2)
    except Exception as e:
        log_error(f"RSI calc failed: {e}")
        return None

def calculate_macd(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    try:
        short = df["Close"].ewm(span=12, adjust=False).mean()
        long = df["Close"].ewm(span=26, adjust=False).mean()
        macd = short - long
        signal = macd.ewm(span=9, adjust=False).mean()
        return round(float(macd.iloc[-1]), 2), round(float(signal.iloc[-1]), 2)
    except Exception as e:
        log_error(f"MACD calc failed: {e}")
        return None, None

def calculate_bbands(df: pd.DataFrame, period: int = 20) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    try:
        sma = df["Close"].rolling(period).mean()
        std = df["Close"].rolling(period).std()
        upper = sma + 2 * std
        lower = sma - 2 * std
        price = df["Close"].iloc[-1]
        return round(float(upper.iloc[-1]), 2), round(float(lower.iloc[-1]), 2), round(float(price), 2)
    except Exception as e:
        log_error(f"Bollinger calc failed: {e}")
        return None, None, None

# ---------- Narrative ----------
def generate_signal_narrative(symbol, rsi, macd_val, macd_signal, ma_50, ma_200, price):
    recs = []
    if rsi is not None:
        if rsi > 70: recs.append("RSI > 70 → Overbought")
        elif rsi < 30: recs.append("RSI < 30 → Oversold")
    if macd_val and macd_signal:
        if macd_val > macd_signal: recs.append("MACD > Signal → Bullish momentum")
        else: recs.append("MACD < Signal → Bearish momentum")
    if ma_50 and ma_200:
        if ma_50 > ma_200: recs.append("50MA > 200MA → Golden Cross (bullish)")
        else: recs.append("50MA < 200MA → Death Cross (bearish)")
    return f"**Signals for {symbol.upper()}**\n- " + "\n- ".join(recs) if recs else "No strong signals detected."

# ---------- Main Node ----------
def technical_analysis_node(state: TradingState) -> TradingState:
    symbol = state.symbol or (state.parsed_query.company_mentioned if state.parsed_query else None)
    if not symbol:
        state.user_response = "No stock symbol detected."
        return state

    try:
        hist = _get_yf_history(symbol, period="1y")
        if hist.empty or len(hist) < 200:
            raise ValueError("Not enough data for indicators")

        # Compute indicators
        ma_50 = round(hist["Close"].rolling(50).mean().iloc[-1], 2)
        ma_200 = round(hist["Close"].rolling(200).mean().iloc[-1], 2)
        rsi = calculate_rsi(hist)
        macd_val, macd_signal = calculate_macd(hist)
        upper, lower, price = calculate_bbands(hist)

        # ✅ Populate TechnicalAnalysis model
        ta = TechnicalAnalysis(
            symbol=symbol,
            price=price,
            rsi=rsi,
            macd_val=macd_val,
            macd_signal=macd_signal,
            ma_50=ma_50,
            ma_200=ma_200,
            bb_upper=upper,
            bb_lower=lower
        )

        # Human-readable summary
        band_pos = (
            "above upper band 📈" if price and upper and price > upper else
            "below lower band 📉" if price and lower and price < lower else
            "within range"
        )

        summary = [
            f"📊 **Technical Analysis for {symbol.upper()}** (via yfinance)",
            f"- RSI(14): {rsi}",
            f"- MACD: {macd_val} | Signal: {macd_signal}",
            f"- 50-Day MA: ${ma_50}",
            f"- 200-Day MA: ${ma_200}",
            f"- Bollinger: Price {band_pos}"
        ]

        rec = generate_signal_narrative(symbol, rsi, macd_val, macd_signal, ma_50, ma_200, price)

        # attach final
        ta.signal = "mixed"
        ta.reasoning = rec
        state.technical_analysis = ta

        state.user_response = "\n".join(summary + ["", rec])
        log_info(f"[TA Node] {symbol} analyzed via yfinance.")
    except Exception as e:
        log_error(f"[TA Node failed]: {e}")
        state.user_response = f"Could not compute technicals for {symbol}."
    return state
