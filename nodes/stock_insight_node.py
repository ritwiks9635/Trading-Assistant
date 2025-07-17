from core.schemas import TradingState
from utils.logger import log_info, log_error
from utils.alpha_client import get_alpha_quote, get_alpha_overview
import yfinance as yf

def stock_insight_node(state: TradingState) -> TradingState:
    """
    Provides stock insights using Alpha Vantage (primary) with fallback to yfinance.
    Returns: current price, market cap, 52-week high/low, volume, dividend yield, PE ratio.
    """

    # Ensure symbol is pulled from the latest parsed query if available
    symbol = state.symbol or (state.parsed_query.company_mentioned if state.parsed_query else None)

    if not symbol:
        log_error("[StockInsightNode] No valid symbol provided in state.")
        state.user_response = "Sorry, I couldn't identify the stock you're referring to."
        return state

    try:
        # --- Primary source: Alpha Vantage ---
        quote = get_alpha_quote(symbol)
        overview = get_alpha_overview(symbol)

        if quote and overview and quote.get("price"):
            response_lines = [
                f"\n📊 **Stock Insight: {symbol.upper()}**",
                f"- **Current Price**: ${quote.get('price', 'N/A')}",
                f"- **Market Cap**: ${round(overview.get('market_cap', 0) / 1e9, 2)}B",
                f"- **PE Ratio (TTM)**: {overview.get('pe_ratio', 'N/A')}",
                f"- **Dividend Yield**: {round(overview.get('dividend_yield', 0) * 100, 2)}%" if overview.get("dividend_yield") else "- **Dividend Yield**: N/A",
                f"- **Volume**: {quote.get('volume', 'N/A'):,}",
                f"- **Change Percent**: {quote.get('change_percent', 0)}%",
                f"- **Sector**: {overview.get('sector', 'N/A')}",
            ]
            state.user_response = "\n".join(response_lines)
            log_info(f"[StockInsightNode] Insight generated via Alpha Vantage for {symbol.upper()}.")
            return state

    except Exception as e:
        log_error(f"[StockInsightNode] Alpha Vantage failed for {symbol.upper()}: {e}")

    # --- Fallback: yfinance ---
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or "currentPrice" not in info:
            raise ValueError("Incomplete ticker info from yfinance.")

        response_lines = [
            f"\n📊 **Stock Insight (Fallback): {symbol.upper()}**",
            f"- **Current Price**: ${info.get('currentPrice', 'N/A')}",
            f"- **Market Cap**: ${round(info.get('marketCap', 0) / 1e9, 2)}B",
            f"- **52-Week High**: ${info.get('fiftyTwoWeekHigh', 'N/A')}",
            f"- **52-Week Low**: ${info.get('fiftyTwoWeekLow', 'N/A')}",
            f"- **Volume**: {info.get('volume', 'N/A'):,}",
            f"- **Dividend Yield**: {round(info.get('dividendYield', 0) * 100, 2)}%" if info.get("dividendYield") else "- **Dividend Yield**: N/A",
            f"- **PE Ratio (TTM)**: {info.get('trailingPE', 'N/A')}",
        ]
        state.user_response = "\n".join(response_lines)
        log_info(f"[StockInsightNode] Fallback used: yfinance for {symbol.upper()}.")

    except Exception as e:
        log_error(f"[StockInsightNode] yfinance failed for {symbol.upper()}: {e}")
        state.user_response = f"Sorry, I couldn't retrieve stock insights for {symbol.upper()} at this time."

    return state
