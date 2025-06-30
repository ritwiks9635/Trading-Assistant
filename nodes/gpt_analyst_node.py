from core.schemas import TradingState, GPTInsight
from model.model import model
from typing import List
import json

def gpt_analyst_node(state: TradingState) -> TradingState:
    """
    Uses Gemini model to analyze raw_news and price_data,
    then updates state.gpt_insight with structured insight.
    """

    if not state.raw_news or not state.price_data:
        raise ValueError("Missing input data: raw_news or price_data not available.")

    news_summaries = "\n".join([f"- {a.summary}" for a in state.raw_news])
    latest_prices = state.price_data[-5:]  # last 5 points
    price_summary = "\n".join([
        f"{p.timestamp.strftime('%Y-%m-%d %H:%M')} | Close: {p.close}" for p in latest_prices
    ])

    prompt = f"""
You're a financial AI analyst. Analyze the following market data and provide a JSON insight report.

# Market News Summary:
{news_summaries}

# Recent Price Data:
{price_summary}

## Your Task:
Return the following in JSON format:
{{
  "sentiment_score": -1 to 1 (float),
  "summary": "short market insight",
  "bullish_indicators": [list of string],
  "bearish_indicators": [list of string],
  "confidence": 0 to 1 (float)
}}
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Extract JSON from response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_str = response_text[start:end]
        data = json.loads(json_str)

        # Parse to schema
        insight = GPTInsight(
            sentiment_score=float(data["sentiment_score"]),
            summary=data["summary"],
            bullish_indicators=data.get("bullish_indicators", []),
            bearish_indicators=data.get("bearish_indicators", []),
            confidence=float(data["confidence"])
        )

        state.gpt_insight = insight
        return state

    except Exception as e:
        print(f"[GPTAnalystNode] Error: {e}")
        state.gpt_insight = None
        return state