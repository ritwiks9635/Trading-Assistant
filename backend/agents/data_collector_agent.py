from core.schemas import TradingState
from nodes.news_analyst_node import news_analyst_node
from nodes.price_analyst_node import price_analyst_node
from state.shared_state import SharedState
from utils.logger import log_info, log_error
from datetime import datetime, timedelta


def data_collector_agent(state: TradingState) -> TradingState:
    """
    🌍 Global Data Collector Agent — Production Ready
    ----------------------------------------------------------
    Collects and aggregates global financial data:
      - Company news (via multiple APIs)
      - Recent price data (via yfinance or API)
    
    Integrates with persistent SharedState to:
      ✅ Avoid redundant API calls (cache for up to 2 hours)
      ✅ Fail gracefully under rate limits
      ✅ Guarantee stable structured data for frontend
    """

    # ✅ Validate input
    if not isinstance(state, TradingState):
        raise TypeError("[DataCollectorAgent] Expected TradingState object.")

    symbol = (state.symbol or "").strip().upper()
    if not symbol:
        log_error("[DataCollectorAgent] ❌ No symbol provided in state.")
        state.raw_news, state.price_data = [], None
        return state

    memory = SharedState()

    # ============================================================
    # 1️⃣ — Try Cached Data (valid for 2 hours)
    # ============================================================
    cache_key = f"data:{symbol}"
    cached = memory.get(cache_key)
    if cached:
        try:
            last_updated = datetime.fromisoformat(cached.get("timestamp"))
            if datetime.utcnow() - last_updated < timedelta(hours=2):
                log_info(f"[DataCollectorAgent] Using cached data for {symbol}.")
                cached_data = cached.get("data", {})
                state.raw_news = cached_data.get("raw_news", [])
                state.price_data = cached_data.get("price_data")
                return state
        except Exception as e:
            log_error(f"[DataCollectorAgent] Cache read failed: {e}")

    # ============================================================
    # 2️⃣ — Collect Global News Data
    # ============================================================
    try:
        log_info(f"[DataCollectorAgent] 🗞️ Fetching global news for {symbol}...")
        state = news_analyst_node(state)
    except Exception as e:
        log_error(f"[DataCollectorAgent] ❌ News fetch failed: {e}")
        state.raw_news = []

    # ============================================================
    # 3️⃣ — Collect Global Price Data
    # ============================================================
    try:
        log_info(f"[DataCollectorAgent] 💹 Fetching global price data for {symbol}...")
        state = price_analyst_node(state)
    except Exception as e:
        log_error(f"[DataCollectorAgent] ⚠️ Price analysis failed for {symbol}: {e}")
        state.price_data = None

    # ============================================================
    # 4️⃣ — Cache Combined Result
    # ============================================================
    try:
        memory.set(cache_key, {
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "raw_news": [n.dict() if hasattr(n, "dict") else n for n in (state.raw_news or [])],
                "price_data": state.price_data,
            },
        })
        log_info(f"[DataCollectorAgent] ✅ Cached fresh data for {symbol}.")
    except Exception as e:
        log_error(f"[DataCollectorAgent] Cache write failed: {e}")

    # ============================================================
    # 5️⃣ — Final Check & Return
    # ============================================================
    if not state.raw_news and not state.price_data:
        log_error(f"[DataCollectorAgent] ❌ No valid data collected for {symbol}.")
    else:
        log_info(f"[DataCollectorAgent] ✅ Data collection complete for {symbol}.")

    return state
