from core.schemas import TradingState, ExecutedTrade, TradeSignal
from datetime import datetime
from typing import Optional
from utils.logger import log_info, log_error
import math

# Default quantity if no budget is provided
DEFAULT_TRADE_QUANTITY = 10

def trade_executor_node(state: TradingState) -> TradingState:
    """
    Executes or simulates a trade based on the trade signal and budget.
    Respects user budget if provided, otherwise falls back to default size.
    """
    try:
        signal: Optional[TradeSignal] = state.trade_signal
        symbol = state.symbol

        if not signal:
            raise ValueError("Missing trade signal — cannot execute trade without it.")

        if signal.action not in ("buy", "sell"):
            # Hold signals don't trigger execution
            state.executed_trade = None
            return state

        # Determine execution price
        price = _mock_price_from_state(state)

        # ✅ Budget-aware sizing
        budget = state.parsed_query.budget if state.parsed_query else None
        if budget is not None:
            max_quantity = math.floor(budget / price)
            if max_quantity < 1:
                state.user_response = (
                    f"⚠️ Your budget (${budget:.2f}) is too small to trade {symbol} "
                    f"(current price ${price:.2f}). Consider fractional shares or cheaper stocks."
                )
                state.executed_trade = None
                log_info(f"[TradeExecutorNode] Budget too small for {symbol}. No trade executed.")
                return state
            quantity = max_quantity
        else:
            quantity = DEFAULT_TRADE_QUANTITY

        # Simulate execution
        executed = ExecutedTrade(
            timestamp=datetime.utcnow(),
            action=signal.action,
            symbol=symbol,
            quantity=quantity,
            price=price,
            status="executed"
        )

        state.executed_trade = executed
        log_info(f"[TradeExecutorNode] Executed: {executed}")
    except Exception as e:
        log_error(f"[TradeExecutorNode] Execution failed: {e}")
        state.executed_trade = None
    return state


def _mock_price_from_state(state: TradingState) -> float:
    """
    Returns latest available close price from price_data,
    or mocks it if price_data is missing.
    """
    if state.price_data and len(state.price_data) > 0:
        return round(state.price_data[-1].close, 2)
    return 100.0  # fallback price for simulation
