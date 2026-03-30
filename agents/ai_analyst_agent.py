from core.schemas import TradingState, GPTInsight
from model.model import model
from utils.logger import log_info, log_error
import json


def ai_analyst_agent(state: TradingState) -> TradingState:
    """
    Uses Gemini to analyze recent price action and news summary.
    Produces structured GPTInsight used in trade execution pipeline.
    """

    # ✅ Validate input state
    if not isinstance(state, TradingState):
        raise TypeError("[AIAnalystAgent] Expected TradingState object.")

    if not state.price_data or not state.raw_news:
        raise ValueError("[AIAnalystAgent] Missing required fields: price_data or raw_news.")

    # ✅ Prompt construction
    prompt = f"""
You are a trading assistant AI. Based on the following recent price data and news, generate a structured market insight.

# Price Data:
{state.price_data}

# News Summary:
{state.raw_news}

Respond ONLY in valid JSON format:
{{
  "sentiment_score": float between -1.0 (bearish) and 1.0 (bullish),
  "summary": string,
  "bullish_indicators": [optional list of symbols or keywords],
  "bearish_indicators": [optional list of symbols or keywords],
  "portfolio_fit": [optional list of 1–2 suggestions],
  "confidence": float between 0.0 and 1.0
}}

Avoid commentary or disclaimers. Do not explain your reasoning.
""".strip()

    try:
        log_info("[AIAnalystAgent] Sending prompt to Gemini...")
        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "").strip()

        if not raw_text:
            raise ValueError("Empty response from Gemini.")

        log_info(f"[Gemini Response]\n{raw_text}")

        # ✅ Extract and parse JSON
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON block found in Gemini response.")

        json_str = raw_text[start:end]
        parsed = json.loads(json_str)

        # ✅ Safely populate GPTInsight
        insight = GPTInsight(
            sentiment_score=float(parsed.get("sentiment_score", 0.0)),
            summary=parsed.get("summary", "No summary provided."),
            bullish_indicators=parsed.get("bullish_indicators", []),
            bearish_indicators=parsed.get("bearish_indicators", []),
            portfolio_fit=parsed.get("portfolio_fit", []),
            confidence=float(parsed.get("confidence", 0.0)),
            forecast_summary=None  # Only used in top_movers, not here
        )

        state.gpt_insight = insight
        log_info("[AIAnalystAgent] ✅ Gemini insight parsed and assigned.")
        return state

    except Exception as e:
        log_error(f"[AIAnalystAgent] ❌ Fallback due to error: {e}")
        state.gpt_insight = GPTInsight(
            sentiment_score=0.0,
            summary="[Fallback] Could not generate insight from Gemini.",
            bullish_indicators=[],
            bearish_indicators=[],
            portfolio_fit=[],
            confidence=0.0,
            forecast_summary=None
        )
        return state
