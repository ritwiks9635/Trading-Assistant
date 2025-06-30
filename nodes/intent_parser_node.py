from core.schemas import TradingState
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash-latest")

INTENT_PROMPT = """
You are a trading assistant. Based on the user question below, classify the intent into one of these:
- report_request
- recovery_guidance
- budget_allocation
- general_advice
- unknown

User question:
"{query}"

Return only the intent label.
"""

def intent_parser_node(state: TradingState) -> TradingState:
    if not state.user_query:
        raise ValueError("user_query is required for intent classification.")

    prompt = INTENT_PROMPT.format(query=state.user_query)
    response = model.generate_content(prompt)
    intent = response.text.strip().lower()

    if intent not in {"report_request", "recovery_guidance", "budget_allocation", "general_advice"}:
        intent = "unknown"

    state.intent = intent
    return state