from core.schemas import TradingState
from utils.logger import log_info

def decision_router_node(state: TradingState) -> dict:
    """
    Maps detected intent and query type to the correct downstream step
    in dual_pipeline.py. Ensures safe, production-grade routing.
    """

    intent = (state.intent or "unknown").lower()
    parsed = state.parsed_query

    # 🧠 Special override: route to top_movers first if query is about top_gainers
    if parsed and parsed.query_type == "top_gainers":
        log_info("[DecisionRouter] Detected 'top_gainers' query → Routing to step_fetch_top_movers")
        return {"next": "step_fetch_top_movers"}

    match intent:
        case "report_request" | "budget_allocation":
            return {"next": "step_collect_data"}
        case "recovery_guidance" | "general_advice":
            return {"next": "step_fetch_top_movers"}
        case "stock_insight":
            return {"next": "step_stock_insight"}
        case "technical_analysis":
            return {"next": "step_technical_analysis"}
        case "risk_assessment":
            return {"next": "step_risk_analysis"}
        case "portfolio_guidance":
            return {"next": "step_portfolio_guidance"}
        case "macro_trend":
            return {"next": "step_macro_trends"}
        case _:
            log_info("[DecisionRouter] Unknown intent — using fallback route.")
            return {"next": "step_generate_response"}
