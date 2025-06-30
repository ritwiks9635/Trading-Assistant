# nodes/news_analyst_node.py

import os
from core.schemas import TradingState, NewsArticle
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from typing import List

def news_analyst_node(state: TradingState) -> TradingState:
    """
    Fetches latest news articles related to the symbol and updates state.raw_news.

    Uses NewsAPI to fetch articles from the past 24 hours related to `state.symbol`.
    """
    api_key = os.getenv("NEWSAPI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing NEWSAPI_API_KEY in environment.")

    newsapi = NewsApiClient(api_key=api_key)
    query = state.symbol.upper()
    from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        response = newsapi.get_everything(
            q=query,
            from_param=from_date,
            language="en",
            sort_by="relevancy",
            page_size=10
        )

        articles: List[NewsArticle] = []
        for item in response.get("articles", []):
            if not all(k in item for k in ("title", "description", "publishedAt", "source")):
                continue

            article = NewsArticle(
                title=item["title"],
                summary=item.get("description", ""),
                published_at=datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00")),
                source=item["source"]["name"]
            )
            articles.append(article)

        state.raw_news = articles
        return state

    except Exception as e:
        # Log the error if using a logging framework
        print(f"[NewsAnalystNode] Error: {e}")
        state.raw_news = []
        return state
