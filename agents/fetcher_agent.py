import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal
from models import NewsArticle

NEWSDATA_URL = "https://newsdata.io/api/1/crypto"


def fetch(keywords: list[str], count: int = 10) -> list[dict]:
    """Fetch raw articles from NewsData.io, deduplicated against DB by URL.

    Returns a list of dicts ready for analyzer_agent — only new articles
    that don't already exist in the database.
    """
    query = " OR ".join(keywords)
    response = httpx.get(
        NEWSDATA_URL,
        params={
            "apikey": os.environ["NEWSDATA_API_KEY"],
            "q": query,
            "language": "en",
        },
        timeout=30,
    )
    response.raise_for_status()
    raw = response.json().get("results", [])[:count]

    db = SessionLocal()
    try:
        new_articles = []
        for item in raw:
            url = item.get("link")
            if not url:
                continue
            if db.query(NewsArticle).filter(NewsArticle.url == url).first():
                continue

            pub_date = None
            if raw_date := item.get("pubDate"):
                try:
                    pub_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            new_articles.append({
                "title": item.get("title") or "",
                "content": item.get("content") or "",
                "url": url,
                "source": item.get("source_id"),
                "published_at": pub_date,
            })
        return new_articles
    finally:
        db.close()


if __name__ == "__main__":
    keywords = ["SEC", "ETF", "bitcoin", "ethereum", "regulation"]
    articles = fetch(keywords)
    print(f"Fetched {len(articles)} new articles.")
    for a in articles:
        print(f"  - {a['title']}")
