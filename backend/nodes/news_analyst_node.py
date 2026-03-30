import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Optional
from dotenv import load_dotenv

from core.schemas import TradingState, NewsArticle
from utils.logger import log_info, log_error
from state.shared_state import SharedState  # 🧠 Persistent memory integration

load_dotenv()


# ============================================================
# 1️⃣ — Helper: Normalize & Validate News Data
# ============================================================
def clean_article(item: dict) -> Optional[NewsArticle]:
    """Normalize raw article dict into NewsArticle model safely."""
    try:
        published = item.get("publishedAt") or item.get("date") or ""
        if isinstance(published, str):
            try:
                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except Exception:
                published_dt = datetime.utcnow()
        else:
            published_dt = datetime.utcnow()

        title = (item.get("title") or "").strip()
        if not title:
            return None

        return NewsArticle(
            title=title[:250],
            summary=(item.get("description") or item.get("summary") or "")[:1000],
            published_at=published_dt,
            source=item.get("source", {}).get("name")
            or item.get("provider")
            or "Unknown",
        )
    except Exception as e:
        log_error(f"[NewsAnalystNode] Article normalization failed: {e}")
        return None


# ============================================================
# 2️⃣ — Global News Fetchers (Primary + Fallbacks)
# ============================================================
def fetch_newsapi(symbol: str, api_key: str) -> List[NewsArticle]:
    """Primary — NewsAPI (global English-focused)."""
    from_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": symbol,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": 10,
            "apiKey": api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise ValueError(f"NewsAPI error: {data.get('message')}")

        return [
            art for art in (clean_article(a) for a in data.get("articles", [])) if art
        ]
    except Exception as e:
        log_error(f"[NewsAnalystNode] NewsAPI fetch failed: {e}")
        return []


def fetch_yfinance_news(symbol: str) -> List[NewsArticle]:
    """Fallback — Yahoo Finance global headlines."""
    try:
        ticker = yf.Ticker(symbol)
        news_items = ticker.news or []
        articles = []
        for n in news_items[:10]:
            published_ts = n.get("providerPublishTime", datetime.utcnow().timestamp())
            article = NewsArticle(
                title=n.get("title", ""),
                summary=n.get("summary", ""),
                published_at=datetime.utcfromtimestamp(published_ts),
                source=n.get("publisher", "Yahoo Finance"),
            )
            articles.append(article)
        return articles
    except Exception as e:
        log_error(f"[NewsAnalystNode] yfinance news failed for {symbol}: {e}")
        return []


def fetch_bing_news(symbol: str, api_key: str) -> List[NewsArticle]:
    """Optional — Bing News Search fallback (if API key set)."""
    try:
        url = "https://api.bing.microsoft.com/v7.0/news/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": symbol, "count": 10, "mkt": "en-US", "sortBy": "Date"}
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("value", []):
            article = NewsArticle(
                title=item.get("name", ""),
                summary=item.get("description", ""),
                published_at=datetime.fromisoformat(
                    item.get("datePublished", datetime.utcnow().isoformat())
                ),
                source=item.get("provider", [{}])[0].get("name", "Bing News"),
            )
            articles.append(article)
        return articles
    except Exception as e:
        log_error(f"[NewsAnalystNode] Bing News fetch failed: {e}")
        return []


# ============================================================
# 3️⃣ — Main Node Logic (Global + Memory Integrated)
# ============================================================
def news_analyst_node(state: TradingState) -> TradingState:
    """
    🌍 Global News Analyst Node (Production-Ready)
    ----------------------------------------------------------
    Fetches and stores latest relevant news for global companies/tickers.
    Integrates with shared persistent memory to reduce API overhead.
    """
    symbol = (state.symbol or "").strip().upper()
    if not symbol:
        log_error("[NewsAnalystNode] No valid symbol found in state.")
        state.raw_news = []
        return state

    memory = SharedState()
    cached = memory.get(f"news:{symbol}")

    # ✅ Use cached news if still fresh (within 3 hours)
    if cached:
        last_updated = datetime.fromisoformat(cached.get("timestamp"))
        if datetime.utcnow() - last_updated < timedelta(hours=3):
            log_info(f"[NewsAnalystNode] Using cached news for {symbol}.")
            state.raw_news = [NewsArticle(**a) for a in cached.get("articles", [])]
            return state

    # --- Load API keys ---
    newsapi_key = os.getenv("NEWSAPI_API_KEY")
    bing_key = os.getenv("BING_NEWS_API_KEY")

    all_articles: List[NewsArticle] = []

    # --- Primary Fetch (NewsAPI) ---
    if newsapi_key:
        all_articles.extend(fetch_newsapi(symbol, newsapi_key))
    else:
        log_error("[NewsAnalystNode] Missing NEWSAPI_API_KEY. Skipping NewsAPI source.")

    # --- Fallback 1 (Yahoo Finance) ---
    if len(all_articles) < 3:
        yfin_articles = fetch_yfinance_news(symbol)
        if yfin_articles:
            log_info(f"[NewsAnalystNode] Added {len(yfin_articles)} Yahoo Finance articles.")
            all_articles.extend(yfin_articles)

    # --- Fallback 2 (Bing News) ---
    if len(all_articles) < 3 and bing_key:
        bing_articles = fetch_bing_news(symbol, bing_key)
        if bing_articles:
            log_info(f"[NewsAnalystNode] Added {len(bing_articles)} Bing articles.")
            all_articles.extend(bing_articles)

    # --- Deduplicate Titles ---
    seen_titles = set()
    unique_articles = []
    for art in all_articles:
        if art and art.title not in seen_titles:
            seen_titles.add(art.title)
            unique_articles.append(art)

    # --- Update State ---
    state.raw_news = unique_articles
    log_info(f"[NewsAnalystNode] ✅ Collected {len(unique_articles)} unique articles for {symbol}.")

    # --- Cache to Persistent Memory ---
    try:
        memory.set(
            f"news:{symbol}",
            {
                "timestamp": datetime.utcnow().isoformat(),
                "articles": [a.dict() for a in unique_articles],
            },
        )
    except Exception as e:
        log_error(f"[NewsAnalystNode] Cache write failed: {e}")

    if not unique_articles:
        log_error(f"[NewsAnalystNode] ❌ No news articles found for {symbol}.")
    return state
