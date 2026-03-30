from core.schemas import TradingState
from utils.logger import log_info, log_error
from state.shared_state import shared_state


def decision_router_node(state: TradingState) -> dict:
    """
    🌐 Global Decision Router Node (PRODUCTION HARDENED)
    ------------------------------------------------------------
    Guarantees:
    - No symbol-dependent node runs without symbol
    - Discovery queries never trigger data collection
    - AIAnalystAgent cannot crash due to missing fields
    """

    try:
        # ==========================================================
        # 1️⃣ Validate State
        # ==========================================================
        if not isinstance(state, TradingState):
            raise TypeError("State must be TradingState")

        user_query = (state.user_query or "").lower()
        intent = (state.intent or "").lower()
        parsed = state.parsed_query
        query_type = (parsed.query_type if parsed else "").lower()
        symbol = (state.symbol or "").upper().strip()

        shared_state.set_global("last_intent", intent)

        log_info(
            f"[DecisionRouter] 🔎 intent={intent or 'N/A'} | "
            f"query_type={query_type or 'N/A'} | symbol={symbol or 'N/A'}"
        )

        # ==========================================================
        # 2️⃣ KEYWORD GROUPS
        # ==========================================================
        mover_keywords = {
            "top gainers", "top losers", "gainers", "losers",
            "top movers", "movers", "advancers", "decliners",
            "momentum"
        }

        macro_keywords = {
            "macro", "economy", "inflation", "interest rate",
            "gdp", "oil", "gold", "commodities", "bitcoin",
            "currency", "fed", "central bank"
        }

        portfolio_keywords = {
            "portfolio", "rebalance", "allocation",
            "diversify", "investment plan"
        }

        risk_keywords = {
            "risk", "volatility", "beta", "hedge",
            "safe investment", "downside"
        }

        discovery_keywords = {
            "looking for", "find", "suggest", "recommend",
            "screen", "low cap", "small cap",
            "top performer", "high growth", "this year"
        }

        report_keywords = {
            "report", "summary", "overview", "analysis"
        }

        # ==========================================================
        # 3️⃣ TOP MOVERS (NO SYMBOL REQUIRED)
        # ==========================================================
        if (
            query_type in {"top_gainers", "top_losers", "movers"}
            or any(k in user_query for k in mover_keywords)
        ):
            log_info("[DecisionRouter] 🚀 Top movers detected → TopMoversNode")
            return {"next": "step_fetch_top_movers"}

        # ==========================================================
        # 4️⃣ DISCOVERY / SCREENING (NO SYMBOL)
        # ==========================================================
        if not symbol and (
            any(k in user_query for k in discovery_keywords)
        ):
            log_info("[DecisionRouter] 🔍 Discovery query → ReportNode (safe)")
            return {"next": "step_report"}

        # ==========================================================
        # 5️⃣ SYMBOL-BASED ROUTING (SYMBOL REQUIRED)
        # ==========================================================
        if symbol:
            if "technical" in user_query or intent == "technical_analysis":
                log_info(f"[DecisionRouter] 📈 Technical analysis → {symbol}")
                return {"next": "step_technical_analysis"}

            log_info(f"[DecisionRouter] 🏢 Company insight → {symbol}")
            return {"next": "step_stock_insight"}

        # ==========================================================
        # 6️⃣ MACRO ANALYSIS
        # ==========================================================
        if intent == "macro_trend" or any(k in user_query for k in macro_keywords):
            log_info("[DecisionRouter] 🌍 Macro trend → MarketAnalysisNode")
            return {"next": "step_market_analysis"}

        # ==========================================================
        # 7️⃣ PORTFOLIO GUIDANCE
        # ==========================================================
        if intent == "portfolio_guidance" or any(k in user_query for k in portfolio_keywords):
            log_info("[DecisionRouter] 💼 Portfolio guidance")
            return {"next": "step_portfolio_guidance"}

        # ==========================================================
        # 8️⃣ RISK ANALYSIS
        # ==========================================================
        if intent == "risk_assessment" or any(k in user_query for k in risk_keywords):
            log_info("[DecisionRouter] ⚖️ Risk analysis")
            return {"next": "step_risk_analysis"}

        # ==========================================================
        # 9️⃣ REPORT REQUEST (SYMBOL REQUIRED FOR DATA COLLECTION)
        # ==========================================================
        if intent == "report_request" or any(k in user_query for k in report_keywords):

            if symbol:
                log_info("[DecisionRouter] 🗂️ Symbol report → CollectData")
                return {"next": "step_collect_data"}

            # 🔒 HARD GUARD — Prevent data collection without symbol
            log_info("[DecisionRouter] 🛑 Report requested but no symbol → Safe ReportNode")
            return {"next": "step_report"}

        # ==========================================================
        # 🔟 SAFE FALLBACK
        # ==========================================================
        log_info("[DecisionRouter] ⚙️ Fallback → ReportNode")
        return {"next": "step_report"}

    except Exception as e:
        log_error(f"[DecisionRouter] ❌ Fatal routing error: {e}")
        return {"next": "step_report"}