from typing import Optional
from core.schemas import TradingState, TradeSignal, GPTInsight
from utils.logger import log_info, log_error
import math
import os

# --- Configurable thresholds (can be tuned or moved to config.yaml) ---
CONFIDENCE_THRESHOLD: float = float(os.getenv("STRAT_CONFIDENCE_THRESH", 0.6))
SENTIMENT_THRESHOLD_BUY: float = float(os.getenv("STRAT_SENTIMENT_BUY", 0.3))
SENTIMENT_THRESHOLD_SELL: float = float(os.getenv("STRAT_SENTIMENT_SELL", -0.3))

# Default suggested position sizing (fraction of capital)
DEFAULT_POSITION_SIZE = float(os.getenv("STRAT_DEFAULT_POS_SIZE", 0.05))  # 5%
MAX_POSITION_SIZE = float(os.getenv("STRAT_MAX_POS_SIZE", 0.25))        # 25% cap


def _safe_get_insight(state: TradingState) -> Optional[GPTInsight]:
    """Return a GPTInsight object or None in a safe manner."""
    insight = getattr(state, "gpt_insight", None)
    if insight is None:
        return None
    # If insight is provided as a dict, try to map to GPTInsight-like attributes
    if isinstance(insight, dict):
        try:
            return GPTInsight(
                sentiment_score=float(insight.get("sentiment_score", 0.0)),
                summary=str(insight.get("summary", "")),
                bullish_indicators=list(insight.get("bullish_indicators", []) or []),
                bearish_indicators=list(insight.get("bearish_indicators", []) or []),
                high_potential_tickers=list(insight.get("high_potential_tickers", []) or []),
                confidence=float(insight.get("confidence", 0.0)),
                forecast_summary=insight.get("forecast_summary", None),
            )
        except Exception as e:
            log_error(f"[StrategyNode] Failed to convert dict→GPTInsight: {e}")
            return None
    # If it's already a GPTInsight, return as-is
    try:
        if isinstance(insight, GPTInsight):
            return insight
    except Exception:
        pass
    return None


def _determine_position_size(state: TradingState, base: float) -> float:
    """
    Determine suggested position size (0.0-1.0) using parsed budget if available.
    - If user provided a budget in parsed_query, we try to scale the position size
      conservatively to avoid oversizing.
    """
    try:
        budget = getattr(getattr(state, "parsed_query", None), "budget", None)
        price = None
        # try to get price from price_data or stock_insight
        if getattr(state, "price_data", None):
            try:
                last = state.price_data[-1]
                price = getattr(last, "close", None) or getattr(last, "price", None)
            except Exception:
                price = None
        if not price:
            stock_insight = getattr(state, "stock_insight", None)
            if isinstance(stock_insight, dict):
                price = stock_insight.get("price")
            else:
                price = getattr(stock_insight, "price", None) if stock_insight else None

        if budget and price and price > 0:
            # number of shares affordable with budget
            max_qty = math.floor(float(budget) / float(price))
            # convert quantity into a fractional portfolio percentage estimate (rough)
            # conservative: assume portfolio size = budget * 20 (heuristic) — avoid large leaps
            portfolio_est = float(budget) * 20.0
            pct = min(base, MAX_POSITION_SIZE)
            return round(max(0.0, min(pct, float(pct))), 4)

        # default fallback
        return max(0.0, min(base, MAX_POSITION_SIZE))
    except Exception as e:
        log_error(f"[StrategyNode] Position size calc failed: {e}")
        return max(0.0, min(base, MAX_POSITION_SIZE))


def strategy_node(state: TradingState) -> TradingState:
    """
    Convert LLM insight into a TradeSignal.
    - Input: state.gpt_insight (GPTInsight or dict)
    - Output: state.trade_signal (TradeSignal) or None (explicitly set)
    """
    try:
        insight = _safe_get_insight(state)

        if not insight:
            log_info("[StrategyNode] No GPT insight available — setting trade_signal to None.")
            state.trade_signal = None
            return state

        # sanitize numeric values
        try:
            confidence = float(insight.confidence or 0.0)
        except Exception:
            confidence = 0.0
        try:
            sentiment = float(insight.sentiment_score or 0.0)
        except Exception:
            sentiment = 0.0

        # Decide action
        action = "hold"
        if confidence >= CONFIDENCE_THRESHOLD:
            if sentiment >= SENTIMENT_THRESHOLD_BUY:
                action = "buy"
            elif sentiment <= SENTIMENT_THRESHOLD_SELL:
                action = "sell"
            else:
                action = "hold"
        else:
            action = "hold"

        # Reasoning text (truncate long summaries to keep signals compact)
        summary = (insight.summary or "")[:1000]
        reasoning = (
            f"{action.upper()} | confidence={round(confidence, 3)} | sentiment={round(sentiment, 3)}"
        )
        if summary:
            reasoning += f" | summary={summary[:300]}"  # short excerpt

        # Suggested position size (budget aware)
        base_size = DEFAULT_POSITION_SIZE if action in ("buy", "sell") else 0.0
        suggested_size = _determine_position_size(state, base_size)

        # Construct TradeSignal - ensure numeric bounds enforced by model schemas
        trade_signal = TradeSignal(
            action=action,
            reasoning=reasoning,
            confidence=max(0.0, min(1.0, round(confidence, 3))),
            suggested_position_size=None if suggested_size == 0.0 else round(max(0.0, min(1.0, suggested_size)), 4)
        )

        state.trade_signal = trade_signal
        log_info(f"[StrategyNode] Generated signal: {trade_signal}")
        return state

    except Exception as e:
        log_error(f"[StrategyNode] Unexpected error: {e}")
        # never crash the pipeline — set safe fallback
        state.trade_signal = None
        return state