from core.schemas import TradingState, CompanyData
from utils.api_clients import get_top_movers, get_budget_picks, get_top_losers
from utils.logger import log_info, log_error


def top_movers_node(state: TradingState) -> TradingState:
    """
    Uses parsed query to fetch company/ETF data based on intent:
    - top_gainers
    - top_losers
    - budget_picks (low-cost stocks under budget)
    - trend (market trend proxy via top movers)
    
    Handles user budget constraint:
    - Filters stocks above budget
    - If none are affordable, injects ETF fallback (SPY, QQQ, VOO)
    """
    try:
        query = state.parsed_query

        if not query:
            raise ValueError("[TopMoversNode] Missing parsed_query in state.")

        movers: list[CompanyData] = []

        # === Handle different query types ===
        match query.query_type:
            case "top_gainers":
                movers = get_top_movers(limit=query.top_n_requested or 5, timeframe=query.time_frame)
            case "top_losers":
                movers = get_top_losers(limit=query.top_n_requested or 5, timeframe=query.time_frame)
            case "budget_picks":
                movers = get_budget_picks(limit=query.top_n_requested or 5, max_price=query.budget or 15)
            case "trend":
                # trend: reuse top movers as proxy for market momentum
                movers = get_top_movers(limit=query.top_n_requested or 5, timeframe=query.time_frame)
            case _:
                log_info("[TopMoversNode] Unknown query_type. Falling back to default top_gainers.")
                movers = get_top_movers(limit=query.top_n_requested or 5, timeframe="today")

        if not movers:
            raise ValueError("[TopMoversNode] No companies returned from API.")

        # === Budget filter ===
        if query.budget:
            budget = query.budget
            affordable = [s for s in movers if s.price and s.price <= budget]

            if affordable:
                log_info(f"[TopMoversNode] 🎯 {len(affordable)} stocks fit the budget (${budget}).")
                movers = affordable
            else:
                log_info(f"[TopMoversNode] ⚠️ No stocks under budget ${budget}. Adding ETF fallback.")
                movers = [
                    CompanyData(
                        symbol="SPY",
                        name="SPDR S&P 500 ETF",
                        price=450.0,
                        percent_change=0.5,
                        volume=None,
                        market_cap=430_000_000_000,
                        summary="ETF fallback for low-budget investors"
                    ),
                    CompanyData(
                        symbol="QQQ",
                        name="Invesco QQQ ETF",
                        price=380.0,
                        percent_change=0.3,
                        volume=None,
                        market_cap=200_000_000_000,
                        summary="ETF fallback for low-budget investors"
                    ),
                    CompanyData(
                        symbol="VOO",
                        name="Vanguard S&P 500 ETF",
                        price=400.0,
                        percent_change=0.4,
                        volume=None,
                        market_cap=350_000_000_000,
                        summary="ETF fallback for low-budget investors"
                    )
                ]

        log_info(f"[TopMoversNode] ✅ Finalized {len(movers)} companies for analysis.")
        state.top_movers = movers

    except Exception as e:
        log_error(f"[TopMoversNode] ❌ Failed with error: {e}")
        state.top_movers = []

    return state
