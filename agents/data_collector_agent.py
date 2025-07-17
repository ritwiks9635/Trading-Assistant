from core.schemas import TradingState
from nodes.news_analyst_node import news_analyst_node
from nodes.price_analyst_node import price_analyst_node

def data_collector_agent(state: TradingState) -> TradingState:
    """
    Runs news and price analyst nodes to collect data.
    
    Args:
        state (TradingState): Shared pipeline state.

    Returns:
        TradingState: Updated state with raw_news and price_data populated.
    """
    if not isinstance(state, TradingState):
        raise TypeError("Expected TradingState")
    
    state = news_analyst_node(state)
    try:
        state = price_analyst_node(state)
    except Exception as e:
        print(f"[DataCollectorAgent] Price analysis failed: {e}")
        state.price_data = None
    return state
