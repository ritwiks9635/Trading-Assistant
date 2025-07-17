import re
from core.schemas import TradingState, ParsedQuery
from utils.logger import log_info

# Expanded keyword categories for better coverage
QUERY_TYPE_KEYWORDS = {
    "top_gainers": [
        "top gainers", "most gained", "high growth", "best performing", "top performing", "strong stocks", "positive return"
    ],
    "top_losers": [
        "top losers", "biggest losses", "most down", "negative trend", "worst stocks", "loss making"
    ],
    "budget_picks": [
        "small company", "cheap", "under $", "budget", "low price", "affordable", "low cap"
    ],
    "news_driven": [
        "today's news", "based on news", "market news", "news impact", "latest announcement"
    ],
    "long_term_potential": [
        "long term", "future growth", "safe long term", "next year", "5 year", "retirement stock"
    ]
}

TIMEFRAME_KEYWORDS = {
    "today": ["today", "now", "current"],
    "this_week": ["this week", "past 7 days", "week performance"],
    "this_month": ["this month", "past 30 days", "monthly"],
    "long_term": ["long term", "next year", "future", "multi-year"]
}

# Common brands → tickers (fallback)
COMMON_COMPANIES = {
    "nvidia": "NVDA",
    "apple": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
    "netflix": "NFLX"
}

def parse_user_query(text: str) -> ParsedQuery:
    parsed = ParsedQuery()
    lowered_text = text.lower()

    # Extract top N companies
    match = re.search(r"top\s+(\d+)", lowered_text)
    if match:
        parsed.top_n_requested = int(match.group(1))

    # Extract budget like $50, ₹100, €200
    budget_match = re.search(r"[\$₹€](\d+(\.\d+)?)", text)
    if budget_match:
        parsed.budget = float(budget_match.group(1))

    # Detect query type
    for label, phrases in QUERY_TYPE_KEYWORDS.items():
        if any(p in lowered_text for p in phrases):
            parsed.query_type = label
            break

    # Detect timeframe
    for label, phrases in TIMEFRAME_KEYWORDS.items():
        if any(p in lowered_text for p in phrases):
            parsed.time_frame = label
            break

    # Extract all-caps ticker symbol
    symbol_match = re.findall(r"\b[A-Z]{2,5}\b", text)
    if symbol_match:
        parsed.company_mentioned = symbol_match[0]

    # Fallback: fuzzy brand → ticker
    for name, ticker in COMMON_COMPANIES.items():
        if name in lowered_text:
            parsed.company_mentioned = ticker
            break

    # Defaults
    if not parsed.query_type:
        parsed.query_type = "top_gainers"
    if not parsed.time_frame:
        parsed.time_frame = "today"

    return parsed


def query_parser_node(state: TradingState) -> TradingState:
    """
    Parses user query into structured ParsedQuery and sets state.symbol accordingly.
    """
    if not state.user_query:
        raise ValueError("Missing user_query in TradingState")

    parsed = parse_user_query(state.user_query)
    state.parsed_query = parsed

    # ✅ Automatically set state.symbol from parsed ticker
    if parsed.company_mentioned:
        state.symbol = parsed.company_mentioned.upper()
        log_info(f"[QueryParserNode] Symbol set from parsed company: {state.symbol}")

    log_info(f"[QueryParserNode] Parsed Query: {parsed.model_dump()}")
    return state
