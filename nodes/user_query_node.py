from core.schemas import TradingState
from utils.logger import log_info, log_error

def user_query_node(state: TradingState) -> TradingState:
    """
    Entry point to inject user query into the shared state.
    Ensure `user_query` exists and is clean.
    """
    if not state.user_query:
        raise ValueError("Missing user_query in TradingState.")
    
    try:
        state.user_query = state.user_query.strip()
        log_info(f"[UserQueryNode] Received query: {state.user_query}")
    except Exception as e:
        log_error(f"[UserQueryNode] Error: {e}")
        state.user_query = ""

    return state