import json
import os
import re
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal
from models import NewsArticle, QASession

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

QA_SYSTEM_PROMPT = """\
You are a crypto news analyst. Answer the user's question based ONLY on the news articles provided below.
Cite specific articles by referencing their title and source. If the context doesn't contain enough information, say so.
Be concise and factual.

Context articles:
{context}
"""


def _search_articles(db, question: str, limit: int = 8) -> list[NewsArticle]:
    """Keyword-based search across title+content. Handles mixed CJK/English text.
    Ranks by number of keyword hits so multi-term matches surface first."""
    from sqlalchemy import or_
    _STOPWORDS = {'what','is','the','are','how','why','when','did','has','have',
                  'and','or','of','in','on','at','to','for','a','an','do','does',
                  'was','were','be','been','its','with','about','will','can','that'}
    # Extract ASCII words (tickers, English terms) + CJK character runs
    ascii_words = [w.lower() for w in re.findall(r'[a-zA-Z0-9]+', question)
                   if len(w) >= 2 and w.lower() not in _STOPWORDS]
    cjk_runs = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]+', question)
    keywords = (ascii_words + cjk_runs)[:6]
    if not keywords:
        keywords = [question[:50]]

    candidates = (
        db.query(NewsArticle)
        .filter(NewsArticle.is_relevant == True)
        .filter(or_(
            *[NewsArticle.title.ilike(f"%{kw}%") for kw in keywords],
            *[NewsArticle.content.ilike(f"%{kw}%") for kw in keywords],
        ))
        .all()
    )

    # score = number of keywords that appear in title+content (title counts double)
    def _score(a: NewsArticle) -> int:
        text_title = (a.title or "").lower()
        text_body = (a.content or "").lower()
        return sum(
            (2 if kw in text_title else 0) + (1 if kw in text_body else 0)
            for kw in keywords
        )

    candidates.sort(key=_score, reverse=True)
    return candidates[:limit]


def _build_context(articles: list[NewsArticle]) -> str:
    parts = []
    for i, a in enumerate(articles, 1):
        snippet = (a.content or "")[:300].strip()
        parts.append(
            f"[{i}] {a.title}\n"
            f"    Source: {a.source or 'unknown'} | {a.published_at.strftime('%Y-%m-%d') if a.published_at else 'n/a'}\n"
            f"    {snippet}"
        )
    return "\n\n".join(parts)


def answer(question: str) -> dict:
    db = SessionLocal()
    try:
        articles = _search_articles(db, question)

        if not articles:
            answer_text = "No relevant articles found in the database to answer this question."
            article_ids = []
        else:
            context = _build_context(articles)
            prompt = QA_SYSTEM_PROMPT.format(context=context)
            try:
                response = _client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Content(role="user", parts=[types.Part(text=question)]),
                    ],
                    config=types.GenerateContentConfig(system_instruction=prompt),
                )
                answer_text = response.text
            except Exception as e:
                answer_text = f"[Gemini error: {e}]"
            article_ids = [a.id for a in articles]

        session = QASession(
            question=question,
            answer=answer_text,
            referenced_articles=json.dumps(article_ids),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return {
            "id": session.id,
            "question": question,
            "answer": answer_text,
            "referenced_articles": article_ids,
            "articles": [_serialize_article(a) for a in articles],
            "created_at": session.created_at.isoformat(),
        }
    finally:
        db.close()


def _serialize_article(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "sentiment": a.sentiment,
        "coin_symbol": a.coin_symbol,
    }
