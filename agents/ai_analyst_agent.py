from core.schemas import TradingState
from nodes.gpt_analyst_node import gpt_analyst_node

def ai_analyst_agent(state: TradingState) -> TradingState:
    """
    Analyzes raw data using GPT to generate market insight.

    Args:
        state (TradingState): Shared pipeline state.

    Returns:
        TradingState: Updated state with gpt_insight.
    """
    return gpt_analyst_node(state)
