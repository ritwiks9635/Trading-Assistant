from core.schemas import TradingState

def decision_router_node(state: TradingState) -> str:
    """
    Decide the next step based on the user's intent.

    Routing rules:
    - 'report_request' and 'budget_allocation' require trading analysis.
    - 'recovery_guidance', 'general_advice', and 'unknown' go straight to response.
    """
    if state.intent in {"report_request", "budget_allocation"}:
        return "run_trading_analysis"
    
    return "generate_assistant_response"
