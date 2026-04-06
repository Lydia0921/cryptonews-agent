from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import NewsArticle
import agents.monitor_agent as monitor_agent

router = APIRouter(prefix="/api", tags=["news"])


@router.get("/news")
def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sentiment: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    coin_symbol: Optional[str] = Query(None),
    is_relevant: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(NewsArticle)
    if sentiment:
        q = q.filter(NewsArticle.sentiment == sentiment)
    if category:
        q = q.filter(NewsArticle.category == category)
    if coin_symbol:
        q = q.filter(NewsArticle.coin_symbol == coin_symbol.upper())
    if is_relevant is not None:
        q = q.filter(NewsArticle.is_relevant == is_relevant)

    total = q.count()
    articles = (
        q.order_by(desc(NewsArticle.published_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [_serialize(a) for a in articles],
    }


@router.get("/news/{article_id}")
def get_news(article_id: int, db: Session = Depends(get_db)):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return _serialize(article)


@router.post("/monitor/trigger")
def trigger_monitor(
    keywords: list[str] = Query(default=["SEC", "ETF", "bitcoin", "ethereum", "regulation"])
):
    stats = monitor_agent.run(keywords)
    return stats


def _serialize(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "relevance_score": a.relevance_score,
        "is_relevant": a.is_relevant,
        "sentiment": a.sentiment,
        "coin_symbol": a.coin_symbol,
        "category": a.category,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
