from core.schemas import TradingState
from nodes.strategy_node import strategy_node
from nodes.trade_executor_node import trade_executor_node

def trading_agent(state: TradingState) -> TradingState:
    """
    Applies strategy logic and executes trades.

    Args:
        state (TradingState): Shared pipeline state.

    Returns:
        TradingState: Updated state with trade_signal and executed_trade.
    """
    state = strategy_node(state)
    state = trade_executor_node(state)
    return state
