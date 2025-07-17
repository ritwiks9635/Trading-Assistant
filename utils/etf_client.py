import requests
import os
from dotenv import load_dotenv

load_dotenv()

TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")
IEX_API_KEY = os.getenv("IEX_API_KEY")

def get_etf_profile(symbol: str) -> dict:
    """
    Fetch ETF profile data from TwelveData (fallback: simulated).
    Returns dict: name, expected_return, top_sector, risk_score
    """
    try:
        url = f"https://api.twelvedata.com/fundamentals?symbol={symbol}&apikey={TWELVE_API_KEY}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        # Simulate parsing (TwelveData may require custom decoding)
        name = data.get("name", symbol)
        sectors = data.get("sector_weights", {})
        top_sector = max(sectors.items(), key=lambda x: x[1])[0] if sectors else "unknown"

        return {
            "name": name,
            "top_sector": top_sector,
            "expected_return": 0.07,  # Static assumption for now
            "risk_score": "medium" if "bond" not in top_sector.lower() else "low"
        }

    except Exception as e:
        print(f"[get_etf_profile] Fallback for {symbol} due to: {e}")
        return {
            "name": symbol,
            "top_sector": "unknown",
            "expected_return": 0.05,
            "risk_score": "unknown"
        }
