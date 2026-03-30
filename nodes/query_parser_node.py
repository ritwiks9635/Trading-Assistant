import re
from core.schemas import TradingState, ParsedQuery
from utils.logger import log_info

# === Keyword categories for query type detection ===
QUERY_TYPE_KEYWORDS = {
    "top_gainers": [
        "top gainers", "most gained", "high growth", "best performing",
        "top performing", "strong stocks", "positive return"
    ],
    "top_losers": [
        "top losers", "biggest losses", "most down", "negative trend",
        "worst stocks", "loss making"
    ],
    "budget_picks": [
        "small company", "cheap", "under $", "budget", "low price",
        "affordable", "low cap"
    ],
    "news_driven": [
        "today's news", "based on news", "market news", "news impact",
        "latest announcement"
    ],
    "long_term_potential": [
        "long term", "future growth", "safe long term", "next year",
        "5 year", "retirement stock"
    ],
    "fundamental_lookup": [
        "dividend", "dividend yield", "payout", "pe ratio", "p/e",
        "earnings per share", "eps", "market cap", "valuation",
        "stock fundamentals", "return on equity", "roe",
        "financial ratios", "beta", "volatility", "book value"
    ],
    "portfolio_guidance": [
        "rebalance", "allocation", "stocks and bonds", "portfolio mix",
        "asset allocation", "diversify", "distribution", "balance my portfolio"
    ],
    "risk_assessment": [
        "risk", "volatility", "drawdown", "safe investment",
        "conservative", "aggressive", "hedge"
    ],
    "macro_trend": [
        "inflation", "interest rates", "fed policy", "economic outlook",
        "geopolitical", "recession", "macro", "economy trend"
    ]
}

# === Timeframe keywords ===
TIMEFRAME_KEYWORDS = {
    "today": ["today", "now", "current"],
    "this_week": ["this week", "past 7 days", "week performance"],
    "this_month": ["this month", "past 30 days", "monthly"],
    "long_term": ["long term", "next year", "future", "multi-year"]
}

# === Brand → ticker mapping ===
COMMON_COMPANIES = {
    "nvidia": "NVDA",
    "apple": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
    "netflix": "NFLX",
    "coca-cola": "KO",
    "coca cola": "KO",
    "berkshire hathaway": "BRK.A"
}


def parse_user_query(text: str) -> ParsedQuery:
    """
    Parse free-form user text into a structured ParsedQuery object.
    Handles query type, budget, timeframe, company/ticker detection.
    """
    parsed = ParsedQuery()
    lowered_text = text.lower()

    # === Extract top N companies ===
    match = re.search(r"top\s+(\d+)", lowered_text)
    if match:
        parsed.top_n_requested = int(match.group(1))

    # === Extract budget with multiple currency formats ===
    budget_match = re.search(
        r"(?:[\$₹€]\s?(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s?(?:usd|dollars?|eur|euros?|₹|inr|rs|rupees?))",
        lowered_text
    )
    if budget_match:
        parsed.budget = float(budget_match.group(1) or budget_match.group(2))

    # === Detect query type from keywords ===
    for label, phrases in QUERY_TYPE_KEYWORDS.items():
        if any(p in lowered_text for p in phrases):
            parsed.query_type = label
            break

    # === Detect timeframe ===
    for label, phrases in TIMEFRAME_KEYWORDS.items():
        if any(p in lowered_text for p in phrases):
            parsed.time_frame = label
            break

    # === Extract ticker symbol (supports BRK.A, BRK.B, AAPL etc.) ===
    symbol_match = re.findall(r"\b[A-Z]{1,5}(?:\.[A-Z])?\b", text)
    if symbol_match:
        parsed.company_mentioned = symbol_match[0]

    # === Brand name → ticker mapping ===
    for name, ticker in COMMON_COMPANIES.items():
        if name in lowered_text:
            parsed.company_mentioned = ticker
            break

    # === Smarter defaults ===
    if not parsed.query_type:
        if parsed.budget is not None and parsed.budget < 100:
            parsed.query_type = "budget_picks"
        else:
            parsed.query_type = "top_gainers"

    # If question is clearly about fundamentals → force fundamental_lookup
    if any(word in lowered_text for word in QUERY_TYPE_KEYWORDS["fundamental_lookup"]):
        parsed.query_type = "fundamental_lookup"

    # Default timeframe = today
    if not parsed.time_frame:
        parsed.time_frame = "today"

    return parsed


def query_parser_node(state: TradingState) -> TradingState:
    """
    Node: Parses user query into structured ParsedQuery and sets state.symbol.
    """
    if not state.user_query:
        raise ValueError("Missing user_query in TradingState")

    parsed = parse_user_query(state.user_query)
    state.parsed_query = parsed

    # ✅ Auto-assign state.symbol if company/ticker found
    if parsed.company_mentioned:
        state.symbol = parsed.company_mentioned.upper()
        log_info(f"[QueryParserNode] Symbol set from parsed company: {state.symbol}")

    log_info(f"[QueryParserNode] Parsed Query: {parsed.model_dump()}")
    return state
