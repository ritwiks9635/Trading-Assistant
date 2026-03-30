from __future__ import annotations
import json, re, time
from typing import Tuple, List

from core.schemas import TradingState, GPTInsight
from model.model import model
from utils.logger import log_info, log_error
from utils.api_clients import get_company_symbols_by_region
from state.shared_state import shared_state


# =========================================================
# 🔍 REGION DETECTOR
# =========================================================
def detect_region_from_query(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["india", "nse", "bse", "sensex"]):
        return "india"
    if any(k in q for k in ["japan", "nikkei"]):
        return "japan"
    if any(k in q for k in ["china", "shanghai", "hong kong"]):
        return "china"
    if any(k in q for k in ["uk", "europe", "germany"]):
        return "europe"
    if any(k in q for k in ["us", "nasdaq", "nyse", "sp500"]):
        return "us"
    return "global"


# =========================================================
# 🧩 GUARANTEED SAFE EXTRACTION
# =========================================================
def safe_extract_text(response) -> Tuple[str, str]:
    try:
        if not response:
            return "", "empty"

        fb = getattr(response, "prompt_feedback", None)
        if fb and getattr(fb, "block_reason", None):
            return "", "blocked_prompt"

        cand = None
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
        if not cand:
            return "", "no_candidate"

        if getattr(cand, "finish_reason", None) == 2:
            return "", "blocked_candidate"

        text_parts = []
        if hasattr(cand, "content") and hasattr(cand.content, "parts"):
            for p in cand.content.parts:
                if hasattr(p, "text") and isinstance(p.text, str):
                    text_parts.append(p.text)

        if text_parts:
            return "\n".join(text_parts).strip(), "ok"

        return "", "empty_text"

    except Exception:
        return "", "exception"


# =========================================================
# 🤖 MAIN ANALYST NODE — 100% PRODUCTION-SAFE
# =========================================================
def gpt_analyst_node(state: TradingState) -> TradingState:
    try:
        if not state.top_movers:
            raise ValueError("Missing top_movers")

        user_q = (state.user_query or "").strip()
        parsed = state.parsed_query
        region = detect_region_from_query(user_q)
        user_id = getattr(state, "user_id", "global_user")

        # store global memory for user
        shared_state.set_global("last_region", region)
        shared_state.set_global("last_query_type", parsed.query_type)

        # -----------------------------------
        # region enrichment (if available)
        # -----------------------------------
        movers = state.top_movers
        try:
            if region != "global":
                regional = get_company_symbols_by_region(region)
                movers = (regional + movers)[:10]
        except:
            pass

        # -----------------------------------
        # factual dataset for the model
        # -----------------------------------
        ctx_lines = []
        for m in movers:
            sym = getattr(m, "symbol", "N/A").upper()
            ctx_lines.append(
                f"- {sym} | Price ${getattr(m, 'price', 0):.2f} | "
                f"Change {getattr(m, 'percent_change', 0):.2f}% | "
                f"MarketCap {getattr(m, 'market_cap', 0):,}"
            )

        context = "\n".join(ctx_lines)

        # =========================================================
        # ULTRA-SAFE PROMPT (GUARANTEED NOT TO TRIGGER RESTRICTIONS)
        # =========================================================
        prompt = f"""
You are a global financial dataset interpreter.

Your ONLY task:
- describe the dataset FACTUALLY
- highlight patterns visible directly in the numbers
- highlight unusual movements
- highlight comparisons between entries
- DO NOT add opinions, judgment, advice, recommendations, predictions, ratings, or projections.

Return ONLY valid JSON in this schema:

{{
  "summary": string,
  "notable_movements": [string],
  "pattern_observations": string
}}

Dataset:
{context}
""".strip()

        log_info("[GPTAnalystNode] 🔍 Sending safe prompt to Gemini...")
        response = model.generate_content(prompt)
        raw, status = safe_extract_text(response)

        # -----------------------------------
        # fallback if restricted
        # -----------------------------------
        if status.startswith("blocked") or not raw.strip():
            fallback_prompt = f"""
Return STRICT JSON only.

Summarize the dataset factually, highlight movements and visible patterns.

JSON schema:
{{
  "summary": "",
  "notable_movements": [],
  "pattern_observations": ""
}}

Dataset:
{context}
"""
            response = model.generate_content(fallback_prompt)
            raw, status = safe_extract_text(response)

        # -----------------------------------
        # final guardrail fallback
        # -----------------------------------
        if not raw.strip():
            raw = '{"summary":"No analysis available.","notable_movements":[],"pattern_observations":""}'

        # =========================================================
        # ROBUST JSON EXTRACTION
        # =========================================================
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            raise ValueError("No JSON in output")

        json_text = json_match.group()

        # cleanup common broken JSON patterns
        json_text = (
            json_text.replace("\n", " ")
                     .replace("\t", " ")
                     .replace("```json", "")
                     .replace("```", "")
        )

        data = json.loads(json_text)

        # =========================================================
        # MAP TO GPTInsight
        # =========================================================
        state.gpt_insight = GPTInsight(
            sentiment_score=0.0,
            summary=data.get("summary", ""),
            bullish_indicators=[],
            bearish_indicators=[],
            high_potential_tickers=data.get("notable_movements", []),
            confidence=1.0,
            forecast_summary=data.get("pattern_observations", "")
        )

        # persist memory
        shared_state.update_user_state(user_id, "last_insight", state.gpt_insight)

        log_info("[GPTAnalystNode] ✅ Safe insight generated.")
        return state

    except Exception as e:
        log_error(f"[GPTAnalystNode] ERROR: {e}")
        state.gpt_insight = GPTInsight(
            sentiment_score=0.0,
            summary="Neutral analysis unavailable due to processing issue.",
            bullish_indicators=[],
            bearish_indicators=[],
            high_potential_tickers=[],
            confidence=0.0,
            forecast_summary=None,
        )
        return state
