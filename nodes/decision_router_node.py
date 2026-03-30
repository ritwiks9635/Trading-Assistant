from core.schemas import TradingState
from utils.logger import log_info


def decision_router_node(state: TradingState) -> dict:
    """
    Routes execution flow based on detected intent and parsed query type.
    Handles: budget, market trends, dividends, forecasts, technicals, fundamentals,
    movers, portfolio guidance, risk, and general reports.
    """

    intent = (state.intent or "unknown").lower()
    parsed = state.parsed_query
    query_type = (parsed.query_type if parsed else None) or ""
    user_query = (state.user_query or "").lower()
    symbol = (state.symbol or "").upper()

    # === Company-specific override ===
    if query_type == "fundamental_lookup" and symbol:
        log_info(f"[DecisionRouter] Fundamentals lookup for {symbol} → Routing to stock insight")
        return {"next": "step_stock_insight"}

    if intent == "technical_analysis" and symbol:
        log_info(f"[DecisionRouter] Technical analysis for {symbol} → Routing to technical analysis")
        return {"next": "step_technical_analysis"}

    # === 🔑 Budget-first override ===
    if intent == "budget_allocation":
        log_info("[DecisionRouter] Budget intent detected → Routing to budget-aware movers")
        return {"next": "step_fetch_top_movers"}

    # === Special case: report on movers ===
    if query_type == "top_gainers" and intent == "report_request":
        log_info("[DecisionRouter] Top gainers report → Routing to step_fetch_top_movers")
        return {"next": "step_fetch_top_movers"}

    # === Query-type driven routing (preferred over intent) ===
    match query_type.lower():
        case "budget_picks":
            log_info("[DecisionRouter] Budget-based query → Routing to top movers for analysis")
            return {"next": "step_fetch_top_movers"}

        case "fundamental_lookup":
            log_info("[DecisionRouter] Fundamentals lookup → Routing to stock insight")
            return {"next": "step_stock_insight"}

        case "news_driven":
            log_info("[DecisionRouter] News-driven query → Routing to news collector")
            return {"next": "step_collect_news"}

        case "long_term_potential":
            log_info("[DecisionRouter] Long-term potential query → Routing to long-term analysis")
            return {"next": "step_long_term_analysis"}

        case "top_losers" | "top_gainers":
            log_info(f"[DecisionRouter] {query_type} request → Routing to top movers")
            return {"next": "step_fetch_top_movers"}

        case "macro_trend":
            log_info("[DecisionRouter] Macro trend query → Routing to market/movers for sentiment")
            return {"next": "step_fetch_top_movers"}

        case "portfolio_guidance":
            log_info("[DecisionRouter] Portfolio guidance query → Routing to portfolio analysis")
            return {"next": "step_portfolio_guidance"}

        case "risk_assessment":
            log_info("[DecisionRouter] Risk assessment query → Routing to risk analysis")
            return {"next": "step_risk_analysis"}

        case "dividend_focus":
            log_info("[DecisionRouter] Dividend-focused query → Routing to top movers for dividend screening")
            return {"next": "step_fetch_top_movers"}

        case "forecast" | "prediction":
            log_info("[DecisionRouter] Forecast query → Routing to top movers for forward-looking analysis")
            return {"next": "step_fetch_top_movers"}

    # === Intent-based fallback (if query_type not matched) ===
    match intent:
        case "technical_analysis":
            log_info("[DecisionRouter] Intent → technical analysis")
            return {"next": "step_technical_analysis"}

        case "risk_assessment":
            log_info("[DecisionRouter] Intent → risk analysis")
            return {"next": "step_risk_analysis"}

        case "portfolio_guidance":
            log_info("[DecisionRouter] Intent → portfolio guidance")
            return {"next": "step_portfolio_guidance"}

        case "stock_insight":
            log_info("[DecisionRouter] Intent → stock insight")
            return {"next": "step_stock_insight"}

        case "general_advice" | "recovery_guidance":
            log_info("[DecisionRouter] Intent → broad market advice → Routing to top movers")
            return {"next": "step_fetch_top_movers"}

        case "report_request":
            log_info("[DecisionRouter] Intent → full trading analysis pipeline")
            return {"next": "step_collect_data"}

        case _:
            log_info(f"[DecisionRouter] Unknown intent '{intent}' → fallback to generic report")
            return {"next": "step_report"}
