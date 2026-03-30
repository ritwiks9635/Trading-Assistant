from core.schemas import TradingState, StockInsight
from utils.logger import log_info, log_error
from utils.alpha_client import get_alpha_quote, get_alpha_overview
import yfinance as yf


# --- Utility Helpers ---
def normalize_dividend_yield(value):
    """Normalize dividend yield into percentage form with 2 decimals."""
    if value in [None, "None", "", "null"]:
        return None
    try:
        val = float(value)
        if val < 1:  # Convert ratio (e.g., 0.024 → 2.4%)
            val *= 100
        return round(val, 2)
    except Exception:
        return None


def safe_float(value):
    """Safely cast any numeric-like string to float."""
    try:
        if value in [None, "", "null", "N/A"]:
            return None
        return float(value)
    except Exception:
        return None


def identify_market_type(symbol: str) -> str:
    """Identify asset type heuristically (stock, etf, crypto, index)."""
    sym = symbol.upper()
    if "-" in sym and "USD" in sym:
        return "crypto"
    if sym.endswith((".NS", ".BO", ".L", ".T", ".HK", ".TO", ".DE", ".PA")):
        return "global_stock"
    if "^" in sym or sym in {"DJI", "^GSPC", "^IXIC", "^N225"}:
        return "index"
    return "equity"


# --- Main Node ---
def stock_insight_node(state: TradingState) -> TradingState:
    """
    🌍 Global Stock Insight Node (Alpha + yfinance hybrid)
    ------------------------------------------------------
    Fetches market data for any equity, ETF, index, or crypto.
    - Alpha Vantage → preferred primary source
    - yfinance → secondary fallback
    - Global tickers supported: US, India (.NS), Japan (.T), UK (.L), etc.
    """

    symbol = (
        state.symbol
        or (state.parsed_query.company_mentioned if state.parsed_query else None)
    )

    if not symbol:
        log_error("[StockInsightNode] ❌ Missing valid symbol in state.")
        return state

    symbol = symbol.strip().upper()
    market_type = identify_market_type(symbol)
    log_info(f"[StockInsightNode] 🚀 Starting analysis for {symbol} ({market_type})")

    stock_data = {"symbol": symbol, "summary": None}

    # ==============================================================
    # 1️⃣ Primary Source — Alpha Vantage
    # ==============================================================
    try:
        quote, overview = None, None
        if market_type in {"equity", "global_stock"}:
            quote = get_alpha_quote(symbol)
            overview = get_alpha_overview(symbol)

        if quote or overview:
            stock_data.update({
                "price": safe_float(quote.get("price")) if quote else None,
                "volume": safe_float(quote.get("volume")) if quote else None,
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
            log_info(f"[StockInsightNode] ✅ Alpha Vantage data fetched for {symbol}")
        else:
            log_info(f"[StockInsightNode] ⚠️ Alpha Vantage returned no data for {symbol}")

    except Exception as e:
        log_error(f"[StockInsightNode] Alpha Vantage error for {symbol}: {e}")

    # ==============================================================
    # 2️⃣ Secondary Source — yfinance
    # ==============================================================
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

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
            "beta": safe_float(info.get("beta")),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "shares_outstanding": safe_float(info.get("sharesOutstanding")),
            "profit_margin": safe_float(info.get("profitMargins")),
            "roe": safe_float(info.get("returnOnEquity")),
            "summary": info.get("longBusinessSummary"),
        }

        # Fill in missing values
        for k, v in merge_map.items():
            if stock_data.get(k) in [None, 0, "N/A", ""]:
                stock_data[k] = v

        log_info(f"[StockInsightNode] 🧩 yfinance data merged for {symbol}")

    except Exception as e:
        log_error(f"[StockInsightNode] yfinance error for {symbol}: {e}")

    # ==============================================================
    # 3️⃣ Fallback for Crypto / Index
    # ==============================================================
    try:
        if market_type in {"crypto", "index"} and not stock_data.get("price"):
            yf_data = yf.Ticker(symbol)
            hist = yf_data.history(period="1d")
            if not hist.empty:
                last_row = hist.iloc[-1]
                stock_data["price"] = safe_float(last_row["Close"])
                stock_data["high_52w"] = safe_float(hist["High"].max())
                stock_data["low_52w"] = safe_float(hist["Low"].min())
                stock_data["summary"] = f"{symbol} latest price data (crypto/index fallback)"
                log_info(f"[StockInsightNode] 🔄 Fallback data populated for {symbol}")
    except Exception as e:
        log_error(f"[StockInsightNode] Fallback fetch failed for {symbol}: {e}")

    # ==============================================================
    # 4️⃣ Final Validation
    # ==============================================================
    if not stock_data.get("price"):
        log_error(f"[StockInsightNode] ❌ No valid data retrieved for {symbol}, returning empty stub.")
        stock_data = {field: None for field in StockInsight.__fields__}
        stock_data["symbol"] = symbol
        stock_data["summary"] = f"No valid data found for {symbol}. Check ticker format or market region."

    state.stock_insight = StockInsight(**stock_data)
    log_info(f"[StockInsightNode] ✅ Stock Insight finalized for {symbol}")
    return state
