from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime

# --- 1. News Article Schema ---
class NewsArticle(BaseModel):
    title: str
    summary: str
    published_at: datetime
    source: str
    sentiment: Optional[Literal["positive", "neutral", "negative"]] = None

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, v):
        if v and v.lower() not in {"positive", "neutral", "negative"}:
            raise ValueError("Invalid sentiment value.")
        return v

# --- 2. Price Point Schema ---
class PricePoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

# --- 3. GPT Insight Schema ---
class GPTInsight(BaseModel):
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    summary: str
    bullish_indicators: List[str]
    bearish_indicators: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    portfolio_fit: Optional[List[str]] = []  # ✅ Added for diversified suggestions
    forecast_summary: Optional[str] = None   # ✅ Optional field for future insights


# --- 4. Trade Signal Schema ---
class TradeSignal(BaseModel):
    action: Literal["buy", "sell", "hold"]
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_position_size: Optional[float] = Field(None, ge=0.0, le=1.0)  # % of capital

# --- 5. Executed Trade Schema ---
class ExecutedTrade(BaseModel):
    timestamp: datetime
    action: Literal["buy", "sell"]
    symbol: str
    quantity: float
    price: float
    status: Literal["executed", "rejected"]

# --- 6. Parsed Query Schema ---
class ParsedQuery(BaseModel):
    top_n_requested: Optional[int] = 5
    time_frame: Optional[str] = "today"  # today | this_week | this_month | long_term
    query_type: Optional[str] = "top_gainers"  # top_gainers | top_losers | budget_picks | news_driven
    company_mentioned: Optional[str] = None
    budget: Optional[float] = None

# --- 7. Company Data Schema ---
class CompanyData(BaseModel):
    symbol: str
    name: Optional[str] = None
    price: Optional[float] = None
    percent_change: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    bullish_percent: Optional[float] = None
    bearish_percent: Optional[float] = None
    summary: Optional[str] = None

# --- 8. Unified State Model ---
class TradingState(BaseModel):
    symbol: str = Field(..., description="The trading symbol (e.g., AAPL, BTCUSD)")

    # Add these fields for conversational pipeline
    user_query: Optional[str] = None
    intent: Optional[str] = None
    user_response: Optional[str] = None

    raw_news: Optional[List[NewsArticle]] = None
    price_data: Optional[List[PricePoint]] = None
    gpt_insight: Optional[GPTInsight] = None
    trade_signal: Optional[TradeSignal] = None
    executed_trade: Optional[ExecutedTrade] = None

    parsed_query: Optional[ParsedQuery] = None
    top_movers: Optional[List[CompanyData]] = None

    run_id: Optional[str] = None  # UUID or timestamp for tracking
    timestamp: Optional[datetime] = None
    next: Optional[str] = None
