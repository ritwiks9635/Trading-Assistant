from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error


def report_node(state: TradingState) -> TradingState:
    """
    Generates a professional user-facing market report.
    - Merges stock fundamentals, technicals, AI analysis, top movers, and risk metrics.
    - Ensures responses are concise, professional, and tailored to retail investors.
    """

    if state.intent == "unknown":
        state.user_response = (
            "I can assist with stock prices, technical analysis, fundamentals, and market insights. "
            "Could you rephrase your query with a company name or trading topic?"
        )
        log_info("[ReportNode] Blocked non-trading intent.")
        return state

    query = state.user_query or "Provide a trading update"
    insight = state.gpt_insight
    movers = state.top_movers or []
    stock_insight = getattr(state, "stock_insight", None)
    technical_analysis = getattr(state, "technical_analysis", None)
    risk_analysis = getattr(state, "risk_analysis", None)

    # --- Format Top Movers ---
    mover_lines = []
    for m in movers:
        try:
            mover_lines.append(
                f"{m.name or m.symbol} ({m.symbol}) is trading near "
                f"${round(m.price, 2) if m.price is not None else 'N/A'}, "
                f"with a {m.percent_change if m.percent_change is not None else 'N/A'}% change today."
            )
        except Exception:
            continue
    summary_block = " ".join(mover_lines) if mover_lines else None

    # --- AI Insight ---
    insight_block = None
    if insight:
        try:
            parts = []
            if getattr(insight, "sentiment_score", None) is not None:
                parts.append(f"Sentiment score {insight.sentiment_score} (confidence {insight.confidence}).")
            if getattr(insight, "summary", None):
                parts.append(insight.summary)
            if getattr(insight, "bullish_indicators", None):
                parts.append(f"Strength in {', '.join(insight.bullish_indicators)}.")
            if getattr(insight, "bearish_indicators", None):
                parts.append(f"Weakness in {', '.join(insight.bearish_indicators)}.")
            if getattr(insight, "forecast_summary", None):
                parts.append(f"Outlook: {insight.forecast_summary}")
            insight_block = " ".join(parts) if parts else None
        except Exception as e:
            log_error(f"[ReportNode] Failed to format gpt_insight: {e}")

    # --- Stock Insight ---
    stock_block = None
    if stock_insight:
        try:
            get_val = (
                stock_insight.get if isinstance(stock_insight, dict)
                else lambda k: getattr(stock_insight, k, None)
            )
            symbol = get_val("symbol")
            price = get_val("price")
            pe = get_val("pe_ratio")
            forward_pe = get_val("forward_pe")
            eps = get_val("eps")
            cap = get_val("market_cap")
            div = get_val("dividend_yield")
            div_ps = get_val("dividend_per_share")
            beta = get_val("beta")
            high_52w = get_val("high_52w")
            low_52w = get_val("low_52w")
            volume = get_val("volume")
            avg_volume = get_val("avg_volume")
            sector = get_val("sector")
            industry = get_val("industry")
            shares_outstanding = get_val("shares_outstanding")
            profit_margin = get_val("profit_margin")
            roe = get_val("roe")
            summary = get_val("summary")

            stock_parts = []
            if symbol:
                stock_parts.append(f"{symbol} is currently trading around ${round(price, 2) if price else 'N/A'}.")
            if cap:
                stock_parts.append(f"Market capitalization is approximately ${cap:,.0f}.")
            if pe:
                stock_parts.append(f"P/E ratio is {round(pe, 2)}.")
            if forward_pe:
                stock_parts.append(f"Forward P/E ratio is {round(forward_pe, 2)}.")
            if eps:
                stock_parts.append(f"Earnings per share (EPS) is {round(eps, 2)}.")
            if beta:
                stock_parts.append(f"Beta value is {round(beta, 2)}.")
            if div:
                stock_parts.append(f"Dividend yield is {div}%.")
            if div_ps:
                stock_parts.append(f"Dividend per share is {round(div_ps, 2)}.")
            if high_52w and low_52w:
                stock_parts.append(f"52-week range: ${round(low_52w, 2)} – ${round(high_52w, 2)}.")
            if volume and avg_volume:
                stock_parts.append(f"Current volume {volume:,} vs average {avg_volume:,}.")
            if sector or industry:
                stock_parts.append(f"Sector: {sector or 'N/A'}, Industry: {industry or 'N/A'}.")
            if shares_outstanding:
                stock_parts.append(f"Shares outstanding: {shares_outstanding:,}.")
            if profit_margin:
                stock_parts.append(f"Profit margin: {round(profit_margin*100, 2) if profit_margin < 1 else round(profit_margin, 2)}%.")
            if roe:
                stock_parts.append(f"Return on Equity (ROE): {round(roe*100, 2) if roe < 1 else round(roe, 2)}%.")
            if summary:
                stock_parts.append(summary)

            if stock_parts:
                stock_block = " ".join(stock_parts)

        except Exception as e:
            log_error(f"[ReportNode] Failed to format stock_insight: {e}")

    # --- Risk Analysis ---
    risk_block = None
    if risk_analysis and isinstance(risk_analysis, dict):
        try:
            risk_parts = []
            beta = risk_analysis.get("beta")
            vol = risk_analysis.get("volatility")
            sharpe = risk_analysis.get("sharpe_ratio")

            if beta is not None:
                risk_parts.append(f"Beta: {round(beta, 2)}")
            if vol is not None:
                risk_parts.append(f"Volatility (annualized): {vol}")
            if sharpe is not None:
                risk_parts.append(f"Sharpe ratio: {sharpe}")

            if risk_parts:
                risk_block = " | ".join(risk_parts)
        except Exception as e:
            log_error(f"[ReportNode] Failed to format risk_analysis: {e}")

    # --- Technical Analysis ---
    ta_block = technical_analysis if technical_analysis else None

    # --- Final Prompt ---
    final_prompt = f"""
    You are a financial research assistant. 
    Your job is to provide concise, professional stock market insights for retail investors.

    User query:
    "{query}"

    Available data:
    {f"- Top Movers: {summary_block}" if summary_block else ""}
    {f"- AI Insight: {insight_block}" if insight_block else ""}
    {f"- Stock Insight: {stock_block}" if stock_block else ""}
    {f"- Risk Analysis: {risk_block}" if risk_block else ""}
    {f"- Technical Analysis: {ta_block}" if ta_block else ""}

    Instructions:
    - Write in clear, professional English.
    - Do not greet the user (no "Hi", no "Hello").
    - Do not apologize or mention lack of real-time access.
    - ONLY mention available data. If something is missing, omit it entirely.
    - Integrate all available information smoothly into 1–2 short paragraphs (max 3 sentences).
    - Keep tone professional, neutral, and informative (like a market analyst).
    - Do not provide direct buy/sell recommendations, only observations.
    """

    try:
        response = model.generate_content(final_prompt)
        if response and hasattr(response, "text") and response.text:
            state.user_response = response.text.strip()
            log_info("[ReportNode] Generated user-facing response.")
        else:
            raise ValueError("LLM returned empty response.")
    except Exception as e:
        log_error(f"[ReportNode] LLM generation failed: {e}")
        state.user_response = (
            "I wasn’t able to generate a market summary at the moment. "
            "Please try again shortly."
        )

    return state
