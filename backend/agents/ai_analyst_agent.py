import json
from datetime import datetime, timedelta
from core.schemas import TradingState, GPTInsight
from model.model import model
from utils.logger import log_info, log_error
from state.shared_state import SharedState  # 🧠 Persistent caching and memory


def ai_analyst_agent(state: TradingState) -> TradingState:
    """
    🤖 Global AI Analyst Agent — Production Ready
    ----------------------------------------------------------
    Uses Gemini (LLM) to analyze price trends and recent news,
    generating structured global market insights.

    Integrates with persistent SharedState to:
      - Cache analysis results for each symbol
      - Avoid redundant Gemini API calls
      - Guarantee stable structured output
      
    """

    # ✅ Validate input state
    if not isinstance(state, TradingState):
        raise TypeError("[AIAnalystAgent] Expected TradingState object.")
    if not state.price_data or not state.raw_news:
        raise ValueError("[AIAnalystAgent] Missing required fields: price_data or raw_news.")

    symbol = (state.symbol or "").upper().strip()
    memory = SharedState()

    # ============================================================
    # 1️⃣ — Use Cached Insights (if within 3 hours)
    # ============================================================
    cache_key = f"insight:{symbol}"
    cached = memory.get(cache_key)
    if cached:
        try:
            last_updated = datetime.fromisoformat(cached.get("timestamp"))
            if datetime.utcnow() - last_updated < timedelta(hours=3):
                log_info(f"[AIAnalystAgent] Using cached Gemini insight for {symbol}.")
                state.gpt_insight = GPTInsight(**cached.get("data"))
                return state
        except Exception as e:
            log_error(f"[AIAnalystAgent] Cache read error: {e}")

    # ============================================================
    # 2️⃣ — Construct Prompt
    # ============================================================
    # Prepare compact versions for safety
    price_summary = str(state.price_data)[-2500:]  # truncate if too large
    news_summary = str(state.raw_news)[-2500:]

    prompt = f"""
You are a global trading analysis AI specialized in professional financial markets.

Analyze the following data for {symbol} and generate structured insights.

# 📊 Price Data:
{price_summary}

# 🗞️ News Summary:
{news_summary}

Respond ONLY in strict JSON format:
{{
  "sentiment_score": float (-1.0 = bearish, +1.0 = bullish),
  "summary": string (max 500 chars, concise, professional),
  "bullish_indicators": [list of terms or tickers],
  "bearish_indicators": [list of terms or tickers],
  "high_potential_tickers": [list of global tickers or companies],
  "confidence": float (0.0 - 1.0)
}}

⚠️ Do NOT include commentary, markdown, or text outside JSON.
""".strip()

    # ============================================================
    # 3️⃣ — Generate Insight via Gemini
    # ============================================================
    try:
        log_info(f"[AIAnalystAgent] Sending prompt to Gemini for {symbol}...")
        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "").strip()

        if not raw_text:
            raise ValueError("Empty response from Gemini model.")

        # --- Extract JSON ---
        start, end = raw_text.find("{"), raw_text.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No valid JSON detected in Gemini output.")

        json_str = raw_text[start:end]
        parsed = json.loads(json_str)

        # --- Create GPTInsight ---
        insight = GPTInsight(
            sentiment_score=float(parsed.get("sentiment_score", 0.0)),
            summary=parsed.get("summary", "No summary provided."),
            bullish_indicators=parsed.get("bullish_indicators", []),
            bearish_indicators=parsed.get("bearish_indicators", []),
            high_potential_tickers=parsed.get("high_potential_tickers", []),
            confidence=float(parsed.get("confidence", 0.0)),
            forecast_summary=None,
        )

        state.gpt_insight = insight
        log_info(f"[AIAnalystAgent] ✅ Gemini insight successfully parsed for {symbol}.")

        # --- Save to Persistent Memory ---
        memory.set(cache_key, {
            "timestamp": datetime.utcnow().isoformat(),
            "data": insight.dict(),
        })

        return state

    # ============================================================
    # 4️⃣ — Robust Fallback
    # ============================================================
    except Exception as e:
        log_error(f"[AIAnalystAgent] ❌ Gemini analysis failed for {symbol}: {e}")
        fallback_insight = GPTInsight(
            sentiment_score=0.0,
            summary="[Fallback] Unable to analyze due to model or parsing error.",
            bullish_indicators=[],
            bearish_indicators=[],
            high_potential_tickers=[],
            confidence=0.0,
            forecast_summary=None,
        )
        state.gpt_insight = fallback_insight
        return state
