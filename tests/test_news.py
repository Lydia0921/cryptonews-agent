from datetime import datetime
from sqlalchemy.orm import Session

from database import Base
from models import NewsArticle
from tests.conftest import TestingSession


def _seed(db: Session, **kwargs) -> NewsArticle:
    defaults = dict(
        title="Bitcoin ETF approved",
        url="https://example.com/1",
        source="coindesk",
        published_at=datetime(2024, 1, 15, 12, 0),
        relevance_score=0.9,
        is_relevant=True,
        sentiment="Bullish",
        coin_symbol="BTC",
        category="regulation",
    )
    defaults.update(kwargs)
    a = NewsArticle(**defaults)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


# ── GET /api/news ─────────────────────────────────────────────────────────────

def test_list_news_empty(client):
    res = client.get("/api/news")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_list_news_returns_articles(client):
    db = TestingSession()
    _seed(db)
    db.close()

    res = client.get("/api/news")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "Bitcoin ETF approved"


def test_filter_by_sentiment(client):
    db = TestingSession()
    _seed(db, url="https://example.com/1", sentiment="Bullish")
    _seed(db, url="https://example.com/2", sentiment="Bearish", title="BTC dump")
    db.close()

    res = client.get("/api/news?sentiment=Bullish")
    assert res.json()["total"] == 1
    assert res.json()["results"][0]["sentiment"] == "Bullish"


def test_filter_by_category(client):
    db = TestingSession()
    _seed(db, url="https://example.com/1", category="regulation")
    _seed(db, url="https://example.com/2", category="market", title="market news")
    db.close()

    res = client.get("/api/news?category=regulation")
    assert res.json()["total"] == 1


def test_filter_by_coin(client):
    db = TestingSession()
    _seed(db, url="https://example.com/1", coin_symbol="BTC")
    _seed(db, url="https://example.com/2", coin_symbol="ETH", title="ETH news")
    db.close()

    res = client.get("/api/news?coin_symbol=btc")  # should uppercase
    assert res.json()["total"] == 1
    assert res.json()["results"][0]["coin_symbol"] == "BTC"


def test_filter_relevant_only(client):
    db = TestingSession()
    _seed(db, url="https://example.com/1", is_relevant=True)
    _seed(db, url="https://example.com/2", is_relevant=False, title="irrelevant")
    db.close()

    res = client.get("/api/news?is_relevant=true")
    assert res.json()["total"] == 1


def test_pagination(client):
    db = TestingSession()
    for i in range(5):
        _seed(db, url=f"https://example.com/{i}", title=f"Article {i}")
    db.close()

    res = client.get("/api/news?page=1&page_size=2")
    data = res.json()
    assert data["total"] == 5
    assert len(data["results"]) == 2


# ── GET /api/news/{id} ────────────────────────────────────────────────────────

def test_get_article_by_id(client):
    db = TestingSession()
    article = _seed(db)
    article_id = article.id
    db.close()

    res = client.get(f"/api/news/{article_id}")
    assert res.status_code == 200
    assert res.json()["id"] == article_id


def test_get_article_not_found(client):
    res = client.get("/api/news/9999")
    assert res.status_code == 404
