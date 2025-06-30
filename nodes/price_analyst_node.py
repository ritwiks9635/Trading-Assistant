import yfinance as yf
from core.schemas import TradingState, PricePoint
from datetime import datetime
from typing import List

def price_analyst_node(state: TradingState) -> TradingState:
    """
    Fetches historical price data (last 7 days) for the symbol and updates state.price_data.

    Uses yfinance to retrieve OHLCV values at 1-hour intervals.
    """
    try:
        ticker = yf.Ticker(state.symbol)
        df = ticker.history(period="7d", interval="1h", auto_adjust=True)

        if df.empty:
            raise ValueError("Empty dataframe received from yfinance.")

        data: List[PricePoint] = []
        for ts, row in df.iterrows():
            point = PricePoint(
                timestamp=ts.to_pydatetime(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"])
            )
            data.append(point)

        state.price_data = data
        return state

    except Exception as e:
        # Log the error if using a logging framework
        print(f"[PriceAnalystNode] Error: {e}")
        state.price_data = []
        return state