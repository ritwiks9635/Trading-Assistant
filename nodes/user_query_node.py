from core.schemas import TradingState

def user_query_node(state: TradingState) -> TradingState:
    """
    Entry point to inject user query into the shared state.
    Ensure `user_query` exists and is clean.
    """
    if not state.user_query:
        raise ValueError("Missing user_query in TradingState.")
    
    state.user_query = state.user_query.strip()
    return state