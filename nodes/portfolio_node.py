from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error
from utils.etf_client import get_etf_profile
import re


def analyze_portfolio(etfs: list[str]) -> str:
    """
    Enhanced version using real ETF data from TwelveData or IEX Cloud.
    Fallbacks to static logic if API fails.
    """
    response_lines = ["📦 **Portfolio Breakdown:**"]
    sector_weights = {}
    risk_flags = []
    total_return = 0.0

    for symbol in etfs:
        try:
            profile = get_etf_profile(symbol)
            name = profile.get("name", symbol)
            sector = profile.get("top_sector", "unknown")
            exp_return = profile.get("expected_return", 0.05)
            risk = profile.get("risk_score", "unknown")

            # Accumulate sector exposure
            sector_weights[sector] = sector_weights.get(sector, 0) + 1
            total_return += exp_return

            if risk == "high":
                risk_flags.append(f"⚠️ `{symbol}` is a high-risk ETF in the `{sector}` sector.")

        except Exception as e:
            log_error(f"[PortfolioNode] ETF fetch failed for {symbol}: {e}")
            response_lines.append(f"- {symbol}: Data unavailable")

    total = sum(sector_weights.values()) or 1
    for sector, count in sector_weights.items():
        pct = round((count / total) * 100, 1)
        response_lines.append(f"- {sector.title()}: {pct}%")
        if pct > 50:
            risk_flags.append(f"⚠️ Overexposed to `{sector}` ({pct}%)")

    avg_return = round((total_return / len(etfs)) * 100, 2) if etfs else 0.0
    response_lines.append(f"\n📈 **Expected Annual Return**: ~{avg_return}%")

    if risk_flags:
        response_lines.append("\n🚨 **Risk Alerts:**")
        response_lines.extend(risk_flags)

    return "\n".join(response_lines)


def portfolio_node(state: TradingState) -> TradingState:
    """
    Handles portfolio management questions with:
    - Sector breakdown using real ETF data
    - Rebalancing and diversification suggestions
    - AI summary from Gemini
    """
    query = state.user_query or ""
    parsed = state.parsed_query

    mentioned = re.findall(r"\b[A-Z]{2,5}\b", query)
    etfs = [e for e in mentioned] or ["SPY", "BND"]  # fallback if none

    try:
        summary = analyze_portfolio(etfs)

        prompt = f"""
You are a professional financial advisor assistant. A user asked:
"{query}"

They mentioned these ETFs: {', '.join(etfs)}

Give:
- Diversification & rebalancing tips
- Risk flags (sector-heavy, no bonds, high volatility)
- If expected return is too low or risky
- Format output clearly.
        """

        ai = model.generate_content(prompt)
        ai_summary = ai.text.strip() if hasattr(ai, "text") else None

        state.user_response = summary
        if ai_summary:
            state.user_response += f"\n\n🤖 **AI Recommendation:**\n{ai_summary}"

        log_info("[PortfolioNode] Portfolio analysis complete.")

    except Exception as e:
        log_error(f"[PortfolioNode] Failure: {e}")
        state.user_response = "Sorry, I couldn't analyze your portfolio right now."

    return state
