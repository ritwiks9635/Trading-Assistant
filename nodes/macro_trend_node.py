from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error
from utils.alpha_client import get_alpha_quote
import requests
import os
from datetime import datetime

FRED_API_KEY = os.getenv("FRED_API_KEY")

# Sector ETFs for macro sector ranking
SECTOR_ETFS = ["XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLU", "XLI", "XLC", "XLRE"]

def fetch_fred_data(series_id: str, title: str) -> str:
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1
        }
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        latest = data["observations"][0]
        date = latest["date"]
        value = latest["value"]
        return f"- **{title}** ({date}): `{value}`"
    except Exception as e:
        log_error(f"[MacroTrendNode] Failed to fetch {series_id}: {e}")
        return f"- **{title}**: Data unavailable"

def fetch_sector_etf_data() -> str:
    """
    Fetch real-time data for sector ETFs using Alpha Vantage.
    Returns a string summary.
    """
    etf_lines = ["\n🏛️ **Sector ETF Trends (via Alpha Vantage)**"]
    for symbol in SECTOR_ETFS:
        try:
            data = get_alpha_quote(symbol)
            if not data or "price" not in data:
                raise ValueError("Missing Alpha Vantage price.")

            price = data.get("price", "N/A")
            change_pct = data.get("change_percent", "N/A")
            volume = f"{int(data.get('volume', 0)):,}"

            etf_lines.append(
                f"- **{symbol}**: ${price} | {change_pct}% | Volume: {volume}"
            )
        except Exception as e:
            log_error(f"[MacroTrendNode] Alpha Vantage failed for {symbol}: {e}")
            etf_lines.append(f"- **{symbol}**: Data unavailable")
    return "\n".join(etf_lines)

def macro_trend_node(state: TradingState) -> TradingState:
    """
    Fetches macro trends:
    - Fed Rate, Inflation, Unemployment (FRED)
    - Sector ETF YTD trends (Alpha Vantage)
    - Gemini model insight summary
    """
    try:
        macro_lines = ["\n🌐 **US Macro Indicators**"]
        macro_lines.append(fetch_fred_data("FEDFUNDS", "Fed Interest Rate (%)"))
        macro_lines.append(fetch_fred_data("CPIAUCSL", "US CPI (Inflation)"))
        macro_lines.append(fetch_fred_data("UNRATE", "US Unemployment Rate (%)"))

        etf_section = fetch_sector_etf_data()

        prompt = f"""
You are a macroeconomic AI analyst. The user wants a market overview.

### Macro Indicators:
{chr(10).join(macro_lines)}

### Sector ETF Performance (via Alpha Vantage):
{etf_section}

Summarize:
- Overall economic sentiment
- Sector strength or weakness
- Rate/inflation impact
- Risks & opportunities for long-term investors

Respond clearly. No generic disclaimers.
"""

        ai = model.generate_content(prompt)
        ai_summary = ai.text.strip() if hasattr(ai, "text") else "[No macro summary generated]"

        state.user_response = "\n".join(macro_lines) + f"\n\n{etf_section}\n\n📈 **Gemini Insight**:\n{ai_summary}"
        log_info("[MacroTrendNode] Macro + ETF trend response generated.")

    except Exception as e:
        log_error(f"[MacroTrendNode] Unexpected failure: {e}")
        state.user_response = "Sorry, I couldn't generate a macroeconomic trend report at this time."

    return state
