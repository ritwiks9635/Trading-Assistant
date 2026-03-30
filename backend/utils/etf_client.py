import os
import requests
from dotenv import load_dotenv
from utils.logger import log_info, log_error
from state.shared_state import load_memory, save_memory

load_dotenv()

TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")
IEX_API_KEY = os.getenv("IEX_API_KEY")

# --------------------------------------------------------------------------
# 🎯 Global ETF, Equity, and Asset Profile Fetcher (Production Grade)
# --------------------------------------------------------------------------
def get_etf_profile(symbol: str) -> dict:
    """
    Fetches ETF, crypto, or commodity profile data safely and globally.

    - Uses TwelveData API for fundamentals (if available)
    - Has built-in mappings for crypto & commodities
    - Caches last successful fetch in state memory
    - Returns standardized dictionary:
        {
            "name": str,
            "asset_type": "ETF" | "Crypto" | "Commodity" | "Equity",
            "top_sector": str,
            "expected_return": float,
            "risk_score": "low" | "medium" | "high"
        }
    """

    symbol = symbol.upper().strip()
    memory = load_memory()

    # ✅ Step 1: Return cached data if available
    cached_profiles = memory.get("asset_profiles", {})
    if symbol in cached_profiles:
        log_info(f"[get_etf_profile] ⚡ Using cached profile for {symbol}")
        return cached_profiles[symbol]

    # ✅ Step 2: Predefined mappings for Crypto
    crypto_map = {
        "BTC": {"name": "Bitcoin", "asset_type": "Crypto", "top_sector": "Digital Assets", "expected_return": 0.15, "risk_score": "high"},
        "ETH": {"name": "Ethereum", "asset_type": "Crypto", "top_sector": "Smart Contracts", "expected_return": 0.12, "risk_score": "high"},
        "SOL": {"name": "Solana", "asset_type": "Crypto", "top_sector": "Blockchain", "expected_return": 0.18, "risk_score": "high"},
        "XRP": {"name": "Ripple", "asset_type": "Crypto", "top_sector": "Payments", "expected_return": 0.08, "risk_score": "medium"},
    }
    if symbol in crypto_map:
        _cache_and_save_profile(symbol, crypto_map[symbol], memory)
        return crypto_map[symbol]

    # ✅ Step 3: Predefined mappings for Commodities
    commodity_map = {
        "GLD": {"name": "SPDR Gold Shares", "asset_type": "Commodity", "top_sector": "Gold", "expected_return": 0.04, "risk_score": "low"},
        "SLV": {"name": "iShares Silver Trust", "asset_type": "Commodity", "top_sector": "Silver", "expected_return": 0.05, "risk_score": "medium"},
        "USO": {"name": "United States Oil Fund", "asset_type": "Commodity", "top_sector": "Oil", "expected_return": 0.07, "risk_score": "high"},
        "DBA": {"name": "Invesco Agriculture Fund", "asset_type": "Commodity", "top_sector": "Agriculture", "expected_return": 0.06, "risk_score": "medium"},
    }
    if symbol in commodity_map:
        _cache_and_save_profile(symbol, commodity_map[symbol], memory)
        return commodity_map[symbol]

    # ✅ Step 4: Global ETF fetch via TwelveData API
    try:
        if not TWELVE_API_KEY:
            raise EnvironmentError("Missing TWELVE_API_KEY environment variable")

        url = f"https://api.twelvedata.com/fundamentals?symbol={symbol}&apikey={TWELVE_API_KEY}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, dict) or "name" not in data:
            raise ValueError(f"Unexpected TwelveData response format for {symbol}: {data}")

        name = data.get("name", symbol)
        sectors = data.get("sector_weights", {})
        top_sector = (
            max(sectors.items(), key=lambda x: x[1])[0]
            if sectors else "Unknown"
        )

        # Basic heuristic for expected return & risk
        sector_lower = top_sector.lower()
        if "tech" in sector_lower:
            expected_return, risk_score = 0.10, "high"
        elif "bond" in sector_lower or "income" in sector_lower:
            expected_return, risk_score = 0.04, "low"
        elif "energy" in sector_lower or "oil" in sector_lower:
            expected_return, risk_score = 0.07, "medium"
        else:
            expected_return, risk_score = 0.06, "medium"

        profile = {
            "name": name,
            "asset_type": "ETF",
            "top_sector": top_sector.title(),
            "expected_return": expected_return,
            "risk_score": risk_score
        }

        log_info(f"[get_etf_profile] ✅ Loaded profile for {symbol}: {profile}")
        _cache_and_save_profile(symbol, profile, memory)
        return profile

    # ✅ Step 5: Fallback on API or data issues
    except Exception as e:
        log_error(f"[get_etf_profile] ⚠️ Fallback used for {symbol}: {e}")
        fallback = _fallback_profile(symbol)
        _cache_and_save_profile(symbol, fallback, memory)
        return fallback


# --------------------------------------------------------------------------
# 🧩 Helper: Fallback Profile Generator
# --------------------------------------------------------------------------
def _fallback_profile(symbol: str) -> dict:
    """
    Creates a simulated safe profile for missing or API-failed assets.
    """
    symbol = symbol.upper()
    if symbol.startswith(("BTC", "ETH", "SOL", "XRP")):
        asset_type, expected_return, risk_score = "Crypto", 0.12, "high"
    elif symbol in ("GLD", "SLV", "USO", "DBA"):
        asset_type, expected_return, risk_score = "Commodity", 0.05, "medium"
    elif len(symbol) <= 5:
        asset_type, expected_return, risk_score = "Equity", 0.07, "medium"
    else:
        asset_type, expected_return, risk_score = "ETF", 0.06, "medium"

    profile = {
        "name": symbol,
        "asset_type": asset_type,
        "top_sector": "Unknown",
        "expected_return": expected_return,
        "risk_score": risk_score
    }

    log_info(f"[get_etf_profile] 🧩 Generated fallback profile for {symbol}: {profile}")
    return profile


# --------------------------------------------------------------------------
# 💾 Helper: Cache and Persist Asset Profile
# --------------------------------------------------------------------------
def _cache_and_save_profile(symbol: str, profile: dict, memory: dict):
    """
    Stores the latest asset profile in persistent memory for future reuse.
    """
    if "asset_profiles" not in memory:
        memory["asset_profiles"] = {}
    memory["asset_profiles"][symbol] = profile
    save_memory(memory)
