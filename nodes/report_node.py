from core.schemas import TradingState
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash-latest")

def report_node(state: TradingState) -> TradingState:
    """
    Generates assistant-style user-facing output.
    """
    query = state.user_query or "Provide trading update"
    symbol = state.symbol
    signal = state.trade_signal
    insight = state.gpt_insight
    intent = state.intent or "general_advice"

    context_parts = [
        f"User asked: '{query}'",
        f"Intent: {intent}",
        f"Symbol: {symbol}"
    ]

    if signal:
        context_parts.append(f"Signal: {signal.action.upper()} | Confidence: {signal.confidence}, Sentiment: {insight.sentiment_score}")
        context_parts.append(f"Reasoning: {signal.reasoning}")

    full_prompt = "\n".join([
        *context_parts,
        "Now generate a helpful, assistant-style response for the user."
    ])

    response = model.generate_content(full_prompt)
    state.user_response = response.text.strip()

    return state