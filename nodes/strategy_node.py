from core.schemas import TradingState, TradeSignal, GPTInsight
from typing import Optional
from utils.logger import log_info, log_error

# --- Configurable thresholds for signal generation ---
CONFIDENCE_THRESHOLD = 0.6
SENTIMENT_THRESHOLD_BUY = 0.3
SENTIMENT_THRESHOLD_SELL = -0.3

def strategy_node(state: TradingState) -> TradingState:
    """
    Converts AI market insight into a trade signal based on defined thresholds.

    Inputs:
        - state.gpt_insight (must be present)

    Outputs:
        - state.trade_signal (Buy/Sell/Hold)
    """
    insight: Optional[GPTInsight] = state.gpt_insight

    if not insight:
        raise ValueError("Missing GPT insight in state — strategy_node requires this input.")
    
    try:
        action: str
        confidence = round(insight.confidence, 2)
        sentiment = round(insight.sentiment_score, 2)

        if confidence >= CONFIDENCE_THRESHOLD:
            if sentiment >= SENTIMENT_THRESHOLD_BUY:
                action = "buy"
            elif sentiment <= SENTIMENT_THRESHOLD_SELL:
                action = "sell"
            else:
                action = "hold"
        else:
            action = "hold"  # Low confidence fallback

        reasoning = (
            f"Action: {action.upper()} — Confidence: {confidence}, "
            f"Sentiment: {sentiment}, Summary: {insight.summary}"
        )

        position_size = 0.05 if action in ("buy", "sell") else 0.0  # Example: 5% of portfolio

        trade_signal = TradeSignal(
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            suggested_position_size=position_size
        )

        state.trade_signal = trade_signal

        log_info(f"[StrategyNode] Generated signal: {state.trade_signal}")
    except Exception as e:
        log_error(f"[StrategyNode] Error: {e}")
        state.trade_signal = None

    return state
