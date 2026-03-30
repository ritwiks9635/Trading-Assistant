import re
from core.schemas import TradingState, ParsedQuery
from utils.logger import log_info, log_error
from state.shared_state import shared_state


# =========================
# MARKET / INDEX KEYWORDS
# =========================
MARKET_KEYWORDS = {
    "nasdaq": "NASDAQ",
    "s&p 500": "SP500",
    "sp500": "SP500",
    "dow jones": "DOW",
    "dow": "DOW",
    "nifty": "NIFTY",
    "nifty 50": "NIFTY",
    "sensex": "SENSEX",
    "ftse": "FTSE",
    "dax": "DAX",
    "nikkei": "NIKKEI",
}


# =========================
# QUERY TYPE KEYWORDS
# =========================
QUERY_TYPE_KEYWORDS = {
    "top_gainers": ["top gainers", "best performing", "highest gain"],
    "top_losers": ["top losers", "worst performing"],
    "budget_picks": ["cheap", "under $", "budget", "low price"],
    "fundamental_lookup": ["pe ratio", "p/e", "market cap", "dividend", "valuation"],
    "portfolio_guidance": ["rebalance", "allocation", "diversify"],
    "risk_assessment": ["risk", "volatility", "drawdown"],
    "macro_trend": ["inflation", "interest rate", "fed", "economy"],
}


TIMEFRAME_KEYWORDS = {
    "today": ["today", "now", "current"],
    "this_week": ["this week"],
    "this_month": ["this month"],
    "long_term": ["long term", "future", "next year", "this year"],
}


# =========================
# COMPANY NAME → TICKER
# =========================
COMMON_COMPANIES = {
    "tesla": "TSLA",
    "apple": "AAPL",
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
    "netflix": "NFLX",
}


# =========================
# 🚫 INVALID SYMBOL TOKENS
# =========================
INVALID_SYMBOLS = {
    "P", "E", "PE", "EPS", "ROI", "GDP", "AI", "USA"
}


def _extract_valid_symbol(text: str) -> str | None:
    """
    Extract only VALID stock tickers.
    Prevents P/E → P bug.
    """
    candidates = re.findall(r"\b[A-Z]{2,5}\b", text)

    for sym in candidates:
        if sym not in INVALID_SYMBOLS:
            return sym

    return None


def parse_user_query(text: str) -> ParsedQuery:
    parsed = ParsedQuery()
    lowered = text.lower()

    # -------------------------
    # Top N
    # -------------------------
    match = re.search(r"top\s+(\d+)", lowered)
    if match:
        parsed.top_n_requested = int(match.group(1))

    # -------------------------
    # Timeframe
    # -------------------------
    for label, phrases in TIMEFRAME_KEYWORDS.items():
        if any(p in lowered for p in phrases):
            parsed.time_frame = label
            break
    if not parsed.time_frame:
        parsed.time_frame = "today"

    # -------------------------
    # Market detection
    # -------------------------
    for key, market in MARKET_KEYWORDS.items():
        if key in lowered:
            parsed.market = market
            parsed.query_type = "top_gainers"
            return parsed

    # -------------------------
    # Company name detection
    # -------------------------
    for name, ticker in COMMON_COMPANIES.items():
        if re.search(rf"\b{name}\b", lowered):
            parsed.company_mentioned = ticker
            break

    # -------------------------
    # Ticker detection (FIXED)
    # -------------------------
    if not parsed.company_mentioned:
        symbol = _extract_valid_symbol(text)
        if symbol:
            parsed.company_mentioned = symbol

    # -------------------------
    # Query type detection
    # -------------------------
    for label, phrases in QUERY_TYPE_KEYWORDS.items():
        if any(p in lowered for p in phrases):
            parsed.query_type = label
            break

    # -------------------------
    # Smart defaults
    # -------------------------
    if not parsed.query_type:
        if parsed.company_mentioned:
            parsed.query_type = "fundamental_lookup"
        else:
            parsed.query_type = "report_request"

    return parsed


def query_parser_node(state: TradingState, user_id: str = "default_user") -> TradingState:
    if not state.user_query:
        log_error("[QueryParserNode] Missing user query")
        return state

    try:
        parsed = parse_user_query(state.user_query)
        state.parsed_query = parsed

        # ✅ SAFE SYMBOL ASSIGNMENT
        if parsed.company_mentioned:
            state.symbol = parsed.company_mentioned
            log_info(f"[QueryParserNode] ✅ Company symbol set: {state.symbol}")
        else:
            state.symbol = None
            log_info("[QueryParserNode] 🧭 Market or discovery query detected")

        log_info(
            f"[QueryParserNode] Parsed → "
            f"type={parsed.query_type}, "
            f"timeframe={parsed.time_frame}, "
            f"company={parsed.company_mentioned or 'N/A'}"
        )

        shared_state.update_user_state(user_id, "parsed_query", parsed)

    except Exception as e:
        log_error(f"[QueryParserNode] Parsing failed: {e}")
        state.parsed_query = ParsedQuery(query_type="report_request", time_frame="today")
        state.symbol = None

    return state