import re
from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error
from utils.etf_client import get_etf_profile
from state.shared_state import load_memory, save_memory


def analyze_portfolio(assets: list[str]) -> str:
    """
    🌍 Global Portfolio Analyzer
    - Handles ETFs, equities, crypto, and commodities.
    - Uses real ETF profile data when available.
    - Performs diversification, risk, and return assessment.
    - Gracefully degrades if data is missing.
    """
    response_lines = ["📦 Portfolio Breakdown:"]
    sector_weights = {}
    risk_flags = []
    total_return = 0.0
    valid_assets = 0

    for symbol in assets:
        try:
            profile = get_etf_profile(symbol)
            if not isinstance(profile, dict):
                raise ValueError("Invalid profile format")

            name = profile.get("name", symbol)
            asset_type = str(profile.get("asset_type", "Unknown")).upper()
            sector = str(profile.get("top_sector", "Misc")).title()
            exp_return = float(profile.get("expected_return", 0.05))
            risk = str(profile.get("risk_score", "medium")).lower()

            key = f"{asset_type} - {sector}"
            sector_weights[key] = sector_weights.get(key, 0) + 1
            total_return += exp_return
            valid_assets += 1

            if risk == "high":
                risk_flags.append(f"⚠️ {symbol} ({name}) is high-risk in {sector} ({asset_type}).")

        except Exception as e:
            log_error(f"[PortfolioNode] Failed to analyze {symbol}: {e}")
            response_lines.append(f"- {symbol}: ⚠️ Data unavailable")

    total = sum(sector_weights.values()) or 1
    for sector, count in sector_weights.items():
        pct = round((count / total) * 100, 1)
        response_lines.append(f"- {sector}: {pct}%")
        if pct > 50:
            risk_flags.append(f"⚠️ Overexposed to {sector} ({pct}%)")

    avg_return = round((total_return / valid_assets) * 100, 2) if valid_assets else 0.0
    response_lines.append(f"\n📈 Expected Annual Return: ~{avg_return}%")

    if risk_flags:
        response_lines.append("\n🚨 Risk Alerts:")
        response_lines.extend(risk_flags)

    return "\n".join(response_lines)


def portfolio_node(state: TradingState) -> TradingState:
    """
    🤖 Global Portfolio Intelligence Node
    - Handles ETFs, equities, crypto, and commodities globally.
    - Produces a professional risk-diversified summary.
    - Persists key insights in shared memory for continuity.
    """
    query = (state.user_query or "").strip()
    parsed = state.parsed_query
    memory = load_memory()

    # Extract mentioned symbols (2–6 uppercase letters, typical ticker range)
    mentioned = re.findall(r"\b[A-Z]{2,6}\b", query)
    assets = mentioned or ["SPY", "BND", "GLD", "BTC"]  # globally diversified fallback

    try:
        # --- Step 1: Run static portfolio analysis
        summary = analyze_portfolio(assets)

        # --- Step 2: AI summarization (fully text-only)
        prompt = f"""
You are a global financial analysis assistant.
The user asked: "{query}"

Detected assets: {', '.join(assets)}

Provide a professional, text-only response covering:
1. Diversification across equities, bonds, commodities, and crypto.
2. Risk and volatility balance.
3. Rebalancing suggestions.
4. Market correlation or concentration risks.

Style guide:
- Global finance tone (institutional-grade).
- No markdown, emojis, or informal text.
- Return clean, professional English prose.
        """

        ai = model.generate_content(prompt)
        ai_summary = getattr(ai, "text", "").strip() if ai else ""

        # --- Step 3: Combine static + AI response
        final_report = summary
        if ai_summary:
            final_report += f"\n\nAI Recommendation:\n{ai_summary}"

        # --- Step 4: Save to persistent memory
        memory["last_portfolio_query"] = query
        memory["last_analyzed_assets"] = assets
        memory["last_portfolio_summary"] = final_report
        save_memory(memory)

        # --- Step 5: Update state
        state.user_response = final_report
        log_info(f"[PortfolioNode] ✅ Completed portfolio analysis for {assets}")

    except Exception as e:
        log_error(f"[PortfolioNode] ❌ Failure: {e}")
        state.user_response = (
            "⚠️ Unable to analyze your portfolio at this time. Please try again shortly."
        )

    return state
