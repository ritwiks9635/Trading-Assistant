import os
import requests
from datetime import datetime
import yfinance as yf

from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error
from utils.alpha_client import get_alpha_quote

FRED_API_KEY = os.getenv("FRED_API_KEY")

# --- Sector ETF Basket (Global Scope) ---
GLOBAL_SECTOR_ETFS = {
    "US": ["XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLU", "XLI", "XLC", "XLRE"],
    "EU": ["EXS1.DE", "EXV6.DE", "EXH1.DE"],  # MSCI Europe, Financials, Healthcare
    "ASIA": ["2800.HK", "1321.T", "NIFTYBEES.NS"],  # HK, JP, IN sector ETFs
}

# --- Economic Indicator Sources ---
GLOBAL_INDICATORS = {
    "US": {
        "FEDFUNDS": "Fed Funds Rate (%)",
        "CPIAUCSL": "CPI (Inflation)",
        "UNRATE": "Unemployment Rate (%)",
        "GDP": "Real GDP Growth Rate",
    },
    "EU": {
        "ecb_inflation": "Eurozone Inflation (CPI)",
        "ecb_rate": "ECB Main Refi Rate (%)",
    },
    "ASIA": {
        "INFL_IN": "India Inflation (YoY)",
        "RATE_JP": "Japan Policy Rate (%)",
        "RATE_IN": "India Repo Rate (%)",
    },
}


# -------------------------------------------------------------
# 1️⃣ Fetch US Macro Data (FRED)
# -------------------------------------------------------------
def fetch_fred_data(series_id: str, title: str) -> str:
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        }
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        obs = data["observations"][0]
        return f"- **{title}** ({obs['date']}): `{obs['value']}`"
    except Exception as e:
        log_error(f"[MacroTrendNode] FRED fetch failed ({series_id}): {e}")
        return f"- **{title}**: Data unavailable"


# -------------------------------------------------------------
# 2️⃣ Fetch ECB / Asian Data (Fallback via yfinance proxies)
# -------------------------------------------------------------
def fetch_global_proxy_data(region: str) -> list[str]:
    """
    Fetch proxy data for regions not supported by FRED.
    Uses representative tickers (e.g. EuroStoxx50, Nikkei, Nifty50)
    """
    proxies = {
        "EU": {"^STOXX50E": "EuroStoxx 50 Index", "^DAX": "Germany DAX Index"},
        "ASIA": {"^N225": "Japan Nikkei 225", "^BSESN": "India BSE Sensex"},
    }

    lines = [f"\n🌏 **{region} Economic Indicators (proxy indices)**"]
    for symbol, title in proxies.get(region, {}).items():
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d")
            if not data.empty:
                last = data.iloc[-1]
                change = ((last["Close"] - data.iloc[-2]["Close"]) / data.iloc[-2]["Close"]) * 100 if len(data) > 1 else 0
                lines.append(f"- **{title}**: {round(last['Close'], 2)} ({round(change, 2)}%)")
            else:
                lines.append(f"- **{title}**: Data unavailable")
        except Exception as e:
            log_error(f"[MacroTrendNode] Proxy fetch failed for {symbol}: {e}")
            lines.append(f"- **{title}**: Data unavailable")
    return lines


# -------------------------------------------------------------
# 3️⃣ Sector ETF Summary (Multi-region)
# -------------------------------------------------------------
def fetch_sector_etf_data() -> str:
    lines = ["\n🏛️ **Sector ETF Trends (Global)**"]
    for region, etfs in GLOBAL_SECTOR_ETFS.items():
        lines.append(f"\n**{region} Sector ETFs:**")
        for symbol in etfs:
            try:
                data = get_alpha_quote(symbol)
                if not data or "price" not in data:
                    raise ValueError("Missing Alpha Vantage price.")

                price = data.get("price", "N/A")
                change_pct = data.get("change_percent", "N/A")
                volume = f"{int(data.get('volume', 0)):,}"

                lines.append(f"- **{symbol}**: ${price} | {change_pct}% | Vol: {volume}")
            except Exception as e:
                log_error(f"[MacroTrendNode] ETF fetch failed for {symbol}: {e}")
                lines.append(f"- **{symbol}**: Data unavailable")
    return "\n".join(lines)


# -------------------------------------------------------------
# 4️⃣ Main Macro Trend Node (Unified)
# -------------------------------------------------------------
def macro_trend_node(state: TradingState) -> TradingState:
    """
    🌍 Global Macro Trend Node
    ---------------------------------------------
    Collects macroeconomic + market data from:
    - US (FRED)
    - EU + ASIA (yfinance proxies)
    - Global Sector ETF data (Alpha)
    - Generates a structured Gemini-based global insight summary
    """

    try:
        log_info("[MacroTrendNode] Starting global macro trend collection...")

        # --- US FRED Data ---
        us_lines = ["\n🇺🇸 **US Macro Indicators**"]
        for sid, title in GLOBAL_INDICATORS["US"].items():
            us_lines.append(fetch_fred_data(sid, title))

        # --- EU + ASIA Proxy Data ---
        eu_lines = fetch_global_proxy_data("EU")
        asia_lines = fetch_global_proxy_data("ASIA")

        # --- Sector ETFs ---
        etf_section = fetch_sector_etf_data()

        # --- AI Model Summary ---
        prompt = f"""
You are a professional macroeconomic analyst.
Generate a global macro insight summary for traders and investors.

### United States Indicators:
{chr(10).join(us_lines)}

### Europe Indicators:
{chr(10).join(eu_lines)}

### Asia Indicators:
{chr(10).join(asia_lines)}

### Global Sector ETF Overview:
{etf_section}

Summarize clearly and professionally:
1. Global market sentiment (bullish, neutral, bearish)
2. Economic trends (growth, inflation, policy)
3. Sector strength and weakness
4. Regional risks and opportunities (US, EU, Asia)
5. Impact on equity markets and long-term outlook

Respond as a concise financial intelligence brief (no disclaimers).
"""
        ai = model.generate_content(prompt)
        ai_summary = ai.text.strip() if hasattr(ai, "text") else "[Insight unavailable]"

        # --- Final Assembly ---
        full_report = (
            "\n".join(us_lines)
            + "\n"
            + "\n".join(eu_lines)
            + "\n"
            + "\n".join(asia_lines)
            + "\n\n"
            + etf_section
            + "\n\n📈 **Global AI Insight**:\n"
            + ai_summary
        )

        state.user_response = full_report
        log_info("[MacroTrendNode] ✅ Global macroeconomic trend report generated successfully.")

    except Exception as e:
        log_error(f"[MacroTrendNode] ❌ Unexpected failure: {e}")
        state.user_response = (
            "Sorry, I couldn't generate a global macroeconomic trend report at this time."
        )

    return state
