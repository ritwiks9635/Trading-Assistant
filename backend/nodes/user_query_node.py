from core.schemas import TradingState
from utils.logger import log_info, log_error
import re


def _normalize_query(text: str) -> str:
    """Normalize the query for consistent global handling."""
    if not text:
        return ""

    # Remove excess whitespace and control characters
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize symbols like ₹, €, £, ¥ etc.
    text = text.replace("₹", "INR ").replace("€", "EUR ").replace("£", "GBP ").replace("¥", "JPY ")

    # Handle tickers like AAPL:, TSLA.US, etc.
    text = re.sub(r"[^a-zA-Z0-9\s\.\-&,$%/]", "", text)
    return text.strip()


def user_query_node(state: TradingState) -> TradingState:
    """
    Entry node for injecting and validating the user query into TradingState.
    Ensures clean, normalized query for global company coverage.
    """

    try:
        query = getattr(state, "user_query", None)
        if not query or not isinstance(query, str) or not query.strip():
            state.user_query = ""
            log_error("[UserQueryNode] Missing or invalid user_query field.")
            state.user_response = (
                "Please provide a valid question or company name to analyze."
            )
            return state

        # Normalize
        clean_query = _normalize_query(query)
        state.user_query = clean_query

        # Log and return
        log_info(f"[UserQueryNode] Processed user query: {clean_query}")
        return state

    except Exception as e:
        log_error(f"[UserQueryNode] Unexpected error: {e}")
        state.user_query = ""
        state.user_response = (
            "There was an issue processing your query. Please rephrase and try again."
        )
        return state