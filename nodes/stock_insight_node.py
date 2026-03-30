from core.schemas import TradingState, StockInsight
from utils.logger import log_info, log_error
from utils.alpha_client import get_alpha_quote, get_alpha_overview
import yfinance as yf


def normalize_dividend_yield(value):
    """Normalize dividend yield into percentage (2 decimals)."""
    if value in [None, "None", "", "null"]:
        return None
    try:
        dy = float(value)
        if dy < 1:  # treat as ratio
            dy *= 100
        return round(dy, 2)
    except Exception:
        return None


def safe_float(val):
    """Convert safely to float, return None on failure."""
    try:
        return float(val)
    except Exception:
        return None


def stock_insight_node(state: TradingState) -> TradingState:
    """
    Fetch stock insights using Alpha Vantage + yfinance hybrid.
    - Alpha Vantage → preferred source
    - yfinance → fills missing fields (beta, EPS, etc.)
    """

    symbol = state.symbol or (state.parsed_query.company_mentioned if state.parsed_query else None)
    if not symbol:
        log_error("[StockInsightNode] No valid symbol provided in state.")
        return state

    stock_data = {"symbol": symbol.upper()}

    # --- Alpha Vantage First ---
    try:
        quote = get_alpha_quote(symbol)
        overview = get_alpha_overview(symbol)

        if quote or overview:
            stock_data.update({
                "price": safe_float(quote.get("price")) if quote else None,
                "volume": safe_float(quote.get("volume")) if quote else None,
                "change_percent": safe_float(quote.get("change_percent")) if quote else None,
                "market_cap": safe_float(overview.get("market_cap")) if overview else None,
                "pe_ratio": safe_float(overview.get("pe_ratio")) if overview else None,
                "forward_pe": safe_float(overview.get("forwardPE")) if overview else None,
                "eps": safe_float(overview.get("eps")) if overview else None,
                "dividend_yield": normalize_dividend_yield(overview.get("dividend_yield")) if overview else None,
                "dividend_per_share": safe_float(overview.get("dividend_per_share")) if overview else None,
                "beta": safe_float(overview.get("beta")) if overview else None,
                "sector": overview.get("sector"),
                "industry": overview.get("industry"),
                "shares_outstanding": safe_float(overview.get("shares_outstanding")) if overview else None,
                "profit_margin": safe_float(overview.get("profit_margin")) if overview else None,
                "roe": safe_float(overview.get("return_on_equity")) if overview else None,
                "summary": overview.get("description") if overview else None,
            })
        log_info(f"[StockInsightNode] Alpha Vantage data pulled for {symbol.upper()}.")

    except Exception as e:
        log_error(f"[StockInsightNode] Alpha Vantage failed for {symbol.upper()}: {e}")

    # --- yfinance Merge ---
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        # Fill missing values ONLY
        merge_map = {
            "price": safe_float(
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("previousClose")
                or info.get("open")
            ),
            "market_cap": safe_float(info.get("marketCap")),
            "high_52w": safe_float(info.get("fiftyTwoWeekHigh")),
            "low_52w": safe_float(info.get("fiftyTwoWeekLow")),
            "volume": safe_float(info.get("volume")),
            "avg_volume": safe_float(info.get("averageVolume")),
            "dividend_yield": normalize_dividend_yield(info.get("dividendYield")),
            "dividend_per_share": safe_float(info.get("dividendRate")),
            "pe_ratio": safe_float(info.get("trailingPE")),
            "forward_pe": safe_float(info.get("forwardPE")),
            "eps": safe_float(info.get("trailingEps")),
            "beta": safe_float(info.get("beta")),  # ✅ fills missing beta
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "shares_outstanding": safe_float(info.get("sharesOutstanding")),
            "profit_margin": safe_float(info.get("profitMargins")),
            "roe": safe_float(info.get("returnOnEquity")),
            "summary": info.get("longBusinessSummary"),
        }

        for k, v in merge_map.items():
            if stock_data.get(k) in [None, 0, "N/A", ""]:
                stock_data[k] = v

        log_info(f"[StockInsightNode] yfinance merged for {symbol.upper()}.")

    except Exception as e:
        log_error(f"[StockInsightNode] yfinance failed for {symbol.upper()}: {e}")

    # --- Final Safeguard ---
    if not stock_data.get("price"):
        stock_data = {field: None for field in StockInsight.__fields__}
        stock_data["symbol"] = symbol.upper()
        log_error(f"[StockInsightNode] ❌ No data available for {symbol.upper()}, returning empty stub.")

    state.stock_insight = stock_data
    return state
