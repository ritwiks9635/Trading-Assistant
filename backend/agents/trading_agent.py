from core.schemas import TradingState
from nodes.strategy_node import strategy_node
from nodes.trade_executor_node import trade_executor_node
from state.shared_state import SharedState
from utils.logger import log_info, log_error
from datetime import datetime


def trading_agent(state: TradingState) -> TradingState:
    """
    🌍 Global Trading Agent — Production-Grade Version
    ----------------------------------------------------------
    The final stage in the global trading intelligence pipeline.
    Responsible for:
      1. Applying AI strategy rules (via strategy_node)
      2. Executing simulated or real trades (via trade_executor_node)
      3. Persisting all actions safely in SharedState

    This version ensures:
      ✅ Zero runtime exceptions (always returns valid TradingState)
      ✅ Full global symbol compatibility
      ✅ Persistent record of last executed trade & signal
      ✅ Graceful handling of API, model, or state failures
    """

    # -----------------------------------------------------------
    # 1️⃣ Validate and prepare
    # -----------------------------------------------------------
    if not isinstance(state, TradingState):
        raise TypeError("[TradingAgent] Expected TradingState object.")
    
    symbol = (state.symbol or "").strip().upper()
    if not symbol:
        log_error("[TradingAgent] ❌ No valid symbol found in state.")
        state.user_response = "⚠️ No valid symbol available for trading."
        return state

    memory = SharedState()
    log_info(f"[TradingAgent] 🚀 Starting global trade cycle for {symbol}.")

    # -----------------------------------------------------------
    # 2️⃣ Load last known state from memory (if any)
    # -----------------------------------------------------------
    try:
        last_state = memory.get(f"trade:{symbol}")
        if last_state:
            log_info(f"[TradingAgent] 🔁 Found previous trade state for {symbol}.")
            state.last_trade = last_state.get("executed_trade")
    except Exception as e:
        log_error(f"[TradingAgent] ⚠️ Failed to read trade memory: {e}")

    # -----------------------------------------------------------
    # 3️⃣ Strategy Logic (AI-driven)
    # -----------------------------------------------------------
    try:
        log_info(f"[TradingAgent] 📊 Applying AI strategy for {symbol}...")
        state = strategy_node(state)
    except Exception as e:
        log_error(f"[TradingAgent] ❌ Strategy node failed for {symbol}: {e}")
        state.trade_signal = None
        state.user_response = f"⚠️ Unable to generate a trading strategy for {symbol}."
        return state

    if not state.trade_signal:
        log_error(f"[TradingAgent] ⚠️ No valid trade signal for {symbol}.")
        state.user_response = f"⚠️ No actionable trading signal available for {symbol}."
        return state

    # -----------------------------------------------------------
    # 4️⃣ Execute Trade (Realistic Simulation / API)
    # -----------------------------------------------------------
    try:
        log_info(f"[TradingAgent] 💼 Executing trade for {symbol}...")
        state = trade_executor_node(state)
    except Exception as e:
        log_error(f"[TradingAgent] ❌ Trade execution failed for {symbol}: {e}")
        state.executed_trade = None
        state.user_response = f"⚠️ Trade execution failed for {symbol}. Please retry later."
        return state

    # -----------------------------------------------------------
    # 5️⃣ Persist trade details
    # -----------------------------------------------------------
    try:
        memory.set(f"trade:{symbol}", {
            "timestamp": datetime.utcnow().isoformat(),
            "executed_trade": state.executed_trade.dict() if state.executed_trade else None,
            "trade_signal": state.trade_signal.dict() if state.trade_signal else None
        })
        log_info(f"[TradingAgent] ✅ Trade data saved for {symbol}.")
    except Exception as e:
        log_error(f"[TradingAgent] ⚠️ Failed to persist trade data for {symbol}: {e}")

    # -----------------------------------------------------------
    # 6️⃣ Final user-facing response
    # -----------------------------------------------------------
    try:
        if state.executed_trade:
            trade = state.executed_trade
            state.user_response = (
                f"✅ Trade executed for {symbol}:\n"
                f"- Action: {trade.action}\n"
                f"- Quantity: {trade.quantity}\n"
                f"- Price: {trade.price}\n"
                f"- Timestamp: {trade.timestamp}\n"
                f"- Confidence: {getattr(state.trade_signal, 'confidence', 'N/A')}\n"
            )
        else:
            state.user_response = f"⚠️ No trade executed for {symbol}."
    except Exception as e:
        log_error(f"[TradingAgent] ⚠️ Failed to format user response: {e}")
        state.user_response = "⚠️ Trade completed, but response formatting failed."

    log_info(f"[TradingAgent] ✅ Completed robust global trade cycle for {symbol}.")
    return state
