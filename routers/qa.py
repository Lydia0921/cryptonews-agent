import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import NewsArticle, QASession
import agents.qa_agent as qa_agent

router = APIRouter(prefix="/api", tags=["qa"])


class AskRequest(BaseModel):
    question: str


@router.post("/qa")
def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return qa_agent.answer(body.question.strip())


@router.get("/qa/history")
def qa_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(QASession).count()
    sessions = (
        db.query(QASession)
        .order_by(desc(QASession.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [_serialize(s, db) for s in sessions],
    }


def _serialize(s: QASession, db: Session) -> dict:
    try:
        article_ids = json.loads(s.referenced_articles or "[]")
    except (json.JSONDecodeError, TypeError):
        article_ids = []

    articles = []
    if article_ids:
        articles = [
            {"id": a.id, "title": a.title, "url": a.url, "source": a.source}
            for a in db.query(NewsArticle).filter(NewsArticle.id.in_(article_ids)).all()
        ]

    return {
        "id": s.id,
        "question": s.question,
        "answer": s.answer,
        "referenced_articles": articles,
        "created_at": s.created_at.isoformat(),
    }
