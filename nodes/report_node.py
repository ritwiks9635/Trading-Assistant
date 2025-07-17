from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error

def report_node(state: TradingState) -> TradingState:
    """
    Generates user-facing output using top movers, GPT insight, and parsed query context.
    """

    if state.intent == "unknown":
        state.user_response = "Sorry, I can only help with trading-related questions."
        log_info("[ReportNode] Blocked non-trading intent.")
        return state

    query = state.user_query or "Provide trading update"
    insight = state.gpt_insight
    parsed = state.parsed_query
    movers = state.top_movers or []

    # Fallback if GPT insight failed
    if not insight:
        state.user_response = "Sorry, I wasn't able to analyze any company data at this time."
        log_error("[ReportNode] No GPT insight available.")
        return state

    # Format mover summaries
    mover_lines = []
    for m in movers:
        mover_lines.append(
            f"- {m.symbol} ({m.name}) | Price: ${round(m.price, 2)} | Change: {m.percent_change}% | Cap: {round(m.market_cap / 1e9, 2)}B"
        )

    summary_block = "\n".join(mover_lines)

    insight_block = f"""
📈 **AI Summary Insight**
- **Sentiment Score**: {insight.sentiment_score}
- **Confidence**: {insight.confidence}
- **Summary**: {insight.summary}
- **Bullish Picks**: {", ".join(insight.bullish_indicators)}
- **Bearish Picks**: {", ".join(insight.bearish_indicators)}
"""

    # ✅ Append forecast summary if present
    if insight.forecast_summary:
        insight_block += f"\n🔮 **Forecast Insight**: {insight.forecast_summary}"

    # 💡 Final Gemini prompt
    final_prompt = f"""
You are a stock market assistant. The user is an individual investor, not a company owner.

Their question:
"{query}"

Intent: {state.intent or 'general_advice'}

You have the following data:

## Top Movers:
{summary_block}

## AI Insight:
- Sentiment Score: {insight.sentiment_score}
- Summary: {insight.summary}
- Bullish Picks: {", ".join(insight.bullish_indicators)}
- Bearish Picks: {", ".join(insight.bearish_indicators)}
- Confidence: {insight.confidence}
{"- Forecast Insight: " + insight.forecast_summary if insight.forecast_summary else ""}

✅ Please provide a concise, professional summary tailored to a retail investor:
- Recommend **which stocks look promising**, and why.
- If any look risky, mention it.
- Format clearly (e.g., use bullet points or sections).
- Do **not** give investment advice — only describe based on today’s data.
"""

    try:
        response = model.generate_content(final_prompt)
        if response and hasattr(response, "text") and response.text:
            state.user_response = response.text.strip()
            log_info("[ReportNode] Generated user-facing response.")
        else:
            raise ValueError("Gemini returned empty response.")

    except Exception as e:
        log_error(f"[ReportNode] Gemini generation failed: {e}")
        state.user_response = "[Assistant] Sorry, I couldn't generate a response right now."

    return state