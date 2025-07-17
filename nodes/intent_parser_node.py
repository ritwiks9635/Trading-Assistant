from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error

# 🚀 Production-grade categories
TOP_GAINERS_KEYWORDS = [
    "top gainers", "most gained", "high growth", "best performing",
    "top performing", "strong stocks", "positive return", "top 5 gainers",
    "nasdaq gainers", "top stocks today", "best stocks today"
]

INTENT_PROMPT = """
You are a professional trading assistant AI. Classify the user's query into one of the following categories used for routing inside a trading pipeline:

- report_request → Requests trading summary or overview
- recovery_guidance → Questions about recovering from losses
- budget_allocation → Queries with limited capital or budget
- general_advice → Generic investing or company comparison
- stock_insight → Seeks company-specific data (e.g. price, volume, market cap)
- technical_analysis → Seeks indicators like RSI, MACD, Bollinger Bands
- risk_assessment → Questions about volatility, risk, or Sharpe ratio
- portfolio_guidance → Help managing or rebalancing user portfolio
- macro_trend → Asks about market-wide trends or economic effects
- unknown → Use only if none of the above apply

Instructions:
1. Analyze the user question.
2. Select **one** most appropriate label.
3. Output only the label (lowercase), nothing else.

User question:
"{query}"
"""

def intent_parser_node(state: TradingState) -> TradingState:
    if not state.user_query:
        raise ValueError("[IntentParserNode] Missing user query.")

    query = state.user_query.strip()
    lowered = query.lower()
    prompt = INTENT_PROMPT.format(query=query)

    try:
        response = model.generate_content(prompt)
        intent = response.text.strip().lower()

        allowed = {
            "report_request",
            "recovery_guidance",
            "budget_allocation",
            "general_advice",
            "stock_insight",
            "technical_analysis",
            "risk_assessment",
            "portfolio_guidance",
            "macro_trend"
        }

        if intent not in allowed:
            intent = "unknown"

        # ✅ Hard fallback for top gainers queries
        if intent == "stock_insight":
            if any(keyword in lowered for keyword in TOP_GAINERS_KEYWORDS):
                log_info("[IntentParserNode] Override: stock_insight → report_request (matched top_gainers keyword)")
                intent = "report_request"

        state.intent = intent
        log_info(f"[IntentParserNode] Detected intent: {intent}")

    except Exception as e:
        log_error(f"[IntentParserNode] Intent classification failed: {e}")
        state.intent = "unknown"

    return state
