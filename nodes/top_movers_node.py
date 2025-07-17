from core.schemas import TradingState, CompanyData
from utils.api_clients import get_top_movers, get_budget_picks, get_top_losers
from utils.logger import log_info, log_error


def top_movers_node(state: TradingState) -> TradingState:
    """
    Uses parsed query to fetch company data based on intent:
    - top_gainers
    - top_losers
    - budget_picks (low-cost stocks under budget)

    Sets state.top_movers with valid CompanyData list.
    """
    try:
        query = state.parsed_query

        if not query:
            raise ValueError("[TopMoversNode] Missing parsed_query in state.")

        movers: list[CompanyData] = []

        match query.query_type:
            case "top_gainers":
                movers = get_top_movers(limit=query.top_n_requested or 5, timeframe=query.time_frame)
            case "top_losers":
                movers = get_top_losers(limit=query.top_n_requested or 5, timeframe=query.time_frame)
            case "budget_picks":
                movers = get_budget_picks(limit=query.top_n_requested or 5, max_price=query.budget or 15)
            case _:
                log_info("[TopMoversNode] Unknown query_type. Falling back to default top_gainers.")
                movers = get_top_movers(limit=query.top_n_requested or 5, timeframe="today")

        if not movers:
            raise ValueError("[TopMoversNode] No companies returned from API.")

        log_info(f"[TopMoversNode] ✅ Fetched {len(movers)} companies.")
        state.top_movers = movers

    except Exception as e:
        log_error(f"[TopMoversNode] ❌ Failed with error: {e}")
        state.top_movers = []

    return state
