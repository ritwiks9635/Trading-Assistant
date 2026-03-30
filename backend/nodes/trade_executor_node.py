from core.schemas import TradingState, ExecutedTrade, TradeSignal
from datetime import datetime
from typing import Optional
from utils.logger import log_info, log_error
import math

# Default quantity if no budget is provided
DEFAULT_TRADE_QUANTITY = 10


def _get_latest_price(state: TradingState) -> float:
    """
    Safely get the most recent price for the current symbol.
    Falls back gracefully if no price data available.
    """
    try:
        if state.price_data and len(state.price_data) > 0:
            latest_price = round(float(state.price_data[-1].close), 2)
            if latest_price > 0:
                return latest_price
        log_info("[TradeExecutorNode] No valid price data found, using fallback.")
    except Exception as e:
        log_error(f"[TradeExecutorNode] Price lookup failed: {e}")
    return 100.00  # fallback simulated price


def trade_executor_node(state: TradingState) -> TradingState:
    """
    Executes or simulates a trade based on the trade signal and budget.
    Designed for global use — resilient against missing data, malformed states,
    and API errors. Only text responses are produced (safe for frontend rendering).
    """
    try:
        signal: Optional[TradeSignal] = getattr(state, "trade_signal", None)
        symbol = getattr(state, "symbol", None)

        if not signal:
            raise ValueError("Missing trade signal — cannot execute trade without it.")
        if not symbol:
            raise ValueError("Missing trading symbol in state.")

        if signal.action not in ("buy", "sell"):
            # Hold or no-op signals
            log_info(f"[TradeExecutorNode] Signal '{signal.action}' ignored (no execution).")
            state.executed_trade = None
            state.user_response = f"🕒 No trade executed for {symbol} — signal type: {signal.action.upper()}."
            return state

        # Determine execution price
        price = _get_latest_price(state)

        # --- Determine quantity ---
        budget = getattr(state.parsed_query, "budget", None) if getattr(state, "parsed_query", None) else None
        if budget is not None:
            try:
                max_quantity = math.floor(float(budget) / price)
                if max_quantity < 1:
                    state.user_response = (
                        f"⚠️ Your budget (${budget:.2f}) is too small to execute a trade for {symbol} "
                        f"(current price: ${price:.2f}). Try increasing your budget."
                    )
                    log_info(f"[TradeExecutorNode] Budget too low for {symbol}, no trade executed.")
                    state.executed_trade = None
                    return state
                quantity = max_quantity
            except Exception as e:
                log_error(f"[TradeExecutorNode] Invalid budget: {e}")
                quantity = DEFAULT_TRADE_QUANTITY
        else:
            quantity = DEFAULT_TRADE_QUANTITY

        # --- Simulated trade execution ---
        executed = ExecutedTrade(
            timestamp=datetime.utcnow(),
            action=signal.action,
            symbol=symbol.upper(),
            quantity=int(quantity),
            price=float(price),
            status="executed"
        )

        # Store execution in state
        state.executed_trade = executed
        total_value = round(executed.quantity * executed.price, 2)

        # --- Build user-facing summary ---
        state.user_response = (
            f"✅ **Trade Executed Successfully**\n\n"
            f"- **Action**: {executed.action.upper()}\n"
            f"- **Symbol**: {executed.symbol}\n"
            f"- **Quantity**: {executed.quantity}\n"
            f"- **Price**: ${executed.price:.2f}\n"
            f"- **Total Value**: ${total_value:,.2f}\n"
            f"- **Status**: {executed.status.title()}"
        )

        log_info(f"[TradeExecutorNode] Executed trade: {executed.action.upper()} {executed.quantity}x {executed.symbol} @ ${executed.price}")

    except Exception as e:
        log_error(f"[TradeExecutorNode] Execution failed: {e}")
        state.executed_trade = None
        state.user_response = (
            "❌ Sorry, the trade execution simulation failed. "
            "Please verify the signal and try again."
        )

    return state
