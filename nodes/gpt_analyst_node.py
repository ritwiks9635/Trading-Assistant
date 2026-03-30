from core.schemas import TradingState, GPTInsight
from model.model import model
from utils.logger import log_info, log_error
import json
import re


def gpt_analyst_node(state: TradingState) -> TradingState:
    """
    Uses Gemini to analyze top movers and parsed query,
    generating structured market insights for:
    - budget queries (low-cost/fractional/ETF recommendations)
    - market trend analysis
    - dividend-focused strategies
    - technical analysis requests
    - general sentiment / report

    Always sets: state.gpt_insight (valid GPTInsight object).
    """

    # ✅ Precondition check
    if not state.top_movers or not state.parsed_query:
        raise ValueError("[GPTAnalystNode] ❌ Missing input: top_movers or parsed_query.")

    movers = state.top_movers
    parsed = state.parsed_query
    query_type = (parsed.query_type or "").lower()
    user_query = (state.user_query or "").lower()

    # ✅ Format movers context
    mover_lines = []
    for m in movers:
        try:
            price = getattr(m, "price", None)
            change = getattr(m, "percent_change", None)
            cap = getattr(m, "market_cap", None)
            summary = getattr(m, "summary", None)
            bullish = getattr(m, "bullish_percent", None)

            line = (
                f"- {getattr(m, 'symbol', 'N/A').upper()} ({getattr(m, 'name', 'N/A')}) | "
                f"Price: ${round(price, 2) if price is not None else 'N/A'} | "
                f"Change: {round(change, 2) if change is not None else 'N/A'}% | "
                f"Cap: {round(cap) if cap is not None else 'N/A'}"
            )

            if bullish is not None:
                line += f" | Bullish: {round(bullish, 2)}%"

            div_yield = getattr(m, "dividend_yield", None)
            if div_yield is not None:
                line += f" | Dividend Yield: {round(div_yield * 100, 2)}%"

            if summary:
                line += f" | {summary}"

            mover_lines.append(line)

        except Exception as e:
            log_error(f"[GPTAnalystNode] Error formatting company {getattr(m, 'symbol', 'UNKNOWN')}: {e}")

    context = "\n".join(mover_lines)
    if not context:
        raise ValueError("[GPTAnalystNode] ❌ No valid movers data to analyze.")

    # === Extra query-aware instructions ===
    is_future_query = bool(re.search(r"\b(next|future|will|prediction|forecast)\b", user_query))
    is_dividend_query = "dividend" in user_query or query_type == "dividend_focus"
    is_budget_query = query_type == "budget_picks" or parsed.budget is not None
    is_trend_query = query_type == "trend" or "market trend" in user_query

    additional_instruction = []
    if is_future_query:
        additional_instruction.append("Include a `forecast_summary` if the query is future-oriented.")
    if is_dividend_query:
        additional_instruction.append("Highlight companies with strong dividend yields.")
    if is_budget_query:
        additional_instruction.append(
            "If the budget is too low for whole shares, suggest ETFs or fractional shares in `portfolio_fit`."
        )
    if is_trend_query:
        additional_instruction.append(
            "Explain overall market direction (bullish, bearish, neutral) based on movers."
        )

    # ✅ Build Gemini prompt
    prompt = f"""
You are a professional AI market analyst. A user asked:
\"{state.user_query}\"

Here are the top {parsed.top_n_requested or 5} companies based on:
query_type = {query_type}, timeframe = {parsed.time_frame}, budget = ${parsed.budget or 'N/A'}:

{context}

Now return a **valid JSON** with the structure:
{{
  "sentiment_score": float (-1 to 1),
  "summary": string,
  "bullish_indicators": [list of stock symbols],
  "bearish_indicators": [list of stock symbols],
  "portfolio_fit": [top 2–3 tickers or ETFs for diversification],
  "confidence": float (0 to 1),
  "forecast_summary": optional string
}}

{" ".join(additional_instruction)}
""".strip()

    try:
        log_info("[GPTAnalystNode] 🔍 Sending prompt to Gemini...")
        log_info(f"[Prompt Sent]\n{prompt}\n")

        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "").strip()

        if not raw_text:
            raise ValueError("Empty response from Gemini.")

        log_info(f"[Gemini Response Raw]\n{raw_text}")

        # ✅ Extract JSON block
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
            summary="⚠️ Gemini could not parse insight. Defaulting to a neutral overview.",
            bullish_indicators=[],
            bearish_indicators=[],
            portfolio_fit=[],
            confidence=0.0,
            forecast_summary=None,
        )
        return state
