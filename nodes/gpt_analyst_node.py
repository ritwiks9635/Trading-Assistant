from core.schemas import TradingState, GPTInsight
from model.model import model
from utils.logger import log_info, log_error
import json
import re


def gpt_analyst_node(state: TradingState) -> TradingState:
    """
    Uses Gemini to analyze top movers and parsed query,
    generating structured market insights.
    Returns: state.gpt_insight (always a valid GPTInsight object).
    """

    # ✅ Precondition check
    if not state.top_movers or not state.parsed_query:
        raise ValueError("[GPTAnalystNode] ❌ Missing input: top_movers or parsed_query.")

    movers = state.top_movers
    parsed = state.parsed_query

    # ✅ Format movers context
    mover_lines = []
    for m in movers:
        try:
            line = (
                f"- {m.symbol.upper()} ({m.name}) | "
                f"Price: ${round(m.price, 2)} | Change: {round(m.percent_change, 2)}% | Cap: {round(m.market_cap)}"
            )
            line += f" | Bullish: {str(m.bullish_percent) if m.bullish_percent is not None else 'N/A'}% | {m.summary or 'N/A'}"
            mover_lines.append(line)
        except Exception as e:
            log_error(f"[GPTAnalystNode] Error formatting company {m.symbol}: {e}")

    context = "\n".join(mover_lines)
    if not context:
        raise ValueError("[GPTAnalystNode] ❌ No valid movers data to analyze.")

    # ✅ Detect future-oriented queries
    user_query = state.user_query.lower()
    future_flag = bool(re.search(r"\b(next|future|will|prediction|forecast)\b", user_query))

    forecast_note = (
        "\nInclude an optional field `forecast_summary` if the query asks about future expectations."
        if future_flag else ""
    )

    # ✅ Build Gemini prompt
    prompt = f"""
You are a professional AI market analyst. A user asked:
"{state.user_query}"

Here are the top {parsed.top_n_requested or 5} companies based on: 
query_type = {parsed.query_type}, timeframe = {parsed.time_frame}, budget = ${parsed.budget or 'N/A'}:

{context}

Now return a **valid JSON** with the structure:
{{
  "sentiment_score": float (-1 to 1),
  "summary": string,
  "bullish_indicators": [list of stock symbols],
  "bearish_indicators": [list of stock symbols],
  "portfolio_fit": [top 2–3 tickers for diversification],
  "confidence": float (0 to 1),
  "forecast_summary": optional string
}}
{forecast_note}
""".strip()

    try:
        log_info("[GPTAnalystNode] 🔍 Sending prompt to Gemini...")
        log_info(f"[Prompt Sent]\n{prompt}\n")

        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "").strip()

        if not raw_text:
            raise ValueError("Empty response from Gemini.")

        log_info(f"[Gemini Response Raw]\n{raw_text}")

        # ✅ Extract JSON block from response
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON block found in response.")

        json_str = raw_text[start:end]
        parsed_data = json.loads(json_str)

        # ✅ Validate & normalize types
        insight = GPTInsight(
            sentiment_score=float(parsed_data.get("sentiment_score", 0.0)),
            summary=parsed_data.get("summary", "No summary provided."),
            bullish_indicators=[s.upper() for s in parsed_data.get("bullish_indicators", [])],
            bearish_indicators=[s.upper() for s in parsed_data.get("bearish_indicators", [])],
            portfolio_fit=[s.upper() for s in parsed_data.get("portfolio_fit", [])],
            confidence=float(parsed_data.get("confidence", 0.0)),
            forecast_summary=parsed_data.get("forecast_summary", None),
        )

        state.gpt_insight = insight
        log_info("[GPTAnalystNode] ✅ Insight parsed successfully.")
        return state

    except Exception as e:
        log_error(f"[GPTAnalystNode] ❌ Fallback triggered: {e}")

        state.gpt_insight = GPTInsight(
            sentiment_score=0.0,
            summary="⚠️ Gemini could not parse insight. Defaulting to a neutral market overview.",
            bullish_indicators=[],
            bearish_indicators=[],
            portfolio_fit=[],
            confidence=0.0,
            forecast_summary=None,
        )
        return state
