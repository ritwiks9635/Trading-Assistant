from core.schemas import TradingState, ExecutedTrade, TradeSignal
from datetime import datetime
from typing import Optional

# Simulated symbol quantity map (could later be dynamic or config-driven)
DEFAULT_TRADE_QUANTITY = 10

def trade_executor_node(state: TradingState) -> TradingState:
    """
    Executes or simulates a trade based on the trade signal.

    Inputs:
        - state.trade_signal

    Outputs:
        - state.executed_trade
    """
    signal: Optional[TradeSignal] = state.trade_signal
    symbol = state.symbol

    if not signal:
        raise ValueError("Missing trade signal — cannot execute trade without it.")

    if signal.action not in ("buy", "sell"):
        # Hold signals are valid but don't trigger trade
        state.executed_trade = None
        return state

    # Simulate execution — could later call real brokerage API here
    executed = ExecutedTrade(
        timestamp=datetime.utcnow(),
        action=signal.action,
        symbol=symbol,
        quantity=DEFAULT_TRADE_QUANTITY,
        price=_mock_price_from_state(state),
        status="executed"
    )

    state.executed_trade = executed
    return state

def _mock_price_from_state(state: TradingState) -> float:
    """
    Returns latest available close price from price_data,
    or mocks it if price_data is missing.
    """
    if state.price_data and len(state.price_data) > 0:
        return round(state.price_data[-1].close, 2)
    return 100.0  # fallback price for simulation