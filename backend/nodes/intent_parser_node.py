from core.schemas import TradingState
from utils.logger import log_info, log_error
from model.model import model

# =================================================
# Canonical intent set (router-safe)
# =================================================
ALLOWED_INTENTS = {
    "top_movers",
    "stock_insight",
    "fundamental_lookup",
    "technical_analysis",
    "risk_assessment",
    "portfolio_guidance",
    "macro_trend",
    "market_report",
    "report_request",
}

# =================================================
# Fallback keyword hints (ONLY if parser missing)
# =================================================
FALLBACK_KEYWORDS = {
    "technical_analysis": {
        "rsi", "macd", "bollinger", "moving average", "support", "resistance"
    },
    "fundamental_lookup": {
        "pe ratio", "eps", "dividend", "valuation", "market cap"
    },
    "risk_assessment": {
        "risk", "safe", "volatility", "drawdown"
    },
    "portfolio_guidance": {
        "portfolio", "allocation", "diversify", "rebalance"
    },
    "macro_trend": {
        "inflation", "interest rate", "fed", "gdp", "recession"
    },
}

# =================================================
# LLM prompt (LAST resort only)
# =================================================
INTENT_PROMPT = """
Classify the trading intent into ONE label only:

top_movers
stock_insight
fundamental_lookup
technical_analysis
risk_assessment
portfolio_guidance
macro_trend
market_report
report_request

Return ONLY the label.

Query:
"{query}"
""".strip()


def _safe_llm_intent(query: str) -> str:
    """LLM fallback intent detection (never primary)."""
    try:
        response = model.generate_content(INTENT_PROMPT.format(query=query))
        text = getattr(response, "text", "").strip().lower()
        text = text.replace("-", "_").replace(" ", "_")
        return text if text in ALLOWED_INTENTS else "report_request"
    except Exception:
        return "report_request"


def intent_parser_node(state: TradingState) -> TradingState:
    """
    FINAL authority on intent.
    Structured parser > heuristic > LLM fallback
    """

    if not state.user_query:
        log_error("[IntentParserNode] ❌ Missing user query")
        state.intent = "report_request"
        return state

    query = state.user_query.lower()

    # =================================================
    # 1️⃣ STRUCTURED PARSER WINS (MOST IMPORTANT)
    # =================================================
    if state.parsed_query and state.parsed_query.query_type:
        intent = state.parsed_query.query_type

        # Normalize legacy labels
        if intent in {"top_gainers", "top_losers"}:
            intent = "top_movers"

        if intent not in ALLOWED_INTENTS:
            intent = "report_request"

        state.intent = intent
        log_info(f"[IntentParserNode] 🔒 Intent locked from parser: {intent}")
        return state

    # =================================================
    # 2️⃣ KEYWORD FALLBACK (NO LLM YET)
    # =================================================
    for intent, keywords in FALLBACK_KEYWORDS.items():
        if any(k in query for k in keywords):
            state.intent = intent
            log_info(f"[IntentParserNode] 🧠 Intent via keyword fallback: {intent}")
            return state

    # =================================================
    # 3️⃣ LLM FALLBACK (LAST RESORT)
    # =================================================
    intent = _safe_llm_intent(query)
    state.intent = intent
    log_info(f"[IntentParserNode] 🤖 Intent via LLM fallback: {intent}")

    return state