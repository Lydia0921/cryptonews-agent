import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from sqlalchemy.exc import IntegrityError

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal
from models import NewsArticle

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

ANALYSIS_PROMPT = """\
Analyze this crypto news article and return a JSON object with exactly these fields.

Title: {title}
Content: {content}

Return JSON only, no other text:
{{
  "relevance_score": <integer 0-10, relevance to crypto markets>,
  "is_relevant": <true if relevance_score >= 7, else false>,
  "sentiment": "<Bullish | Bearish | Neutral>",
  "coin_symbol": "<uppercase ticker e.g. BTC, ETH — null if none specifically mentioned>",
  "category": "<regulation | market | technical | other>"
}}
"""


def _analyze(title: str, content: str) -> dict:
    prompt = ANALYSIS_PROMPT.format(title=title, content=content[:800])
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "relevance_score": 0,
            "is_relevant": False,
            "sentiment": "Neutral",
            "coin_symbol": None,
            "category": "other",
        }


def analyze_and_save(articles: list[dict]) -> int:
    """Analyze a list of article dicts (from fetcher_agent) and save to DB.

    Each dict must have: title, content, url, source, published_at.
    Returns the number of articles successfully saved.
    """
    if not articles:
        return 0

    db = SessionLocal()
    added = 0

    try:
        for item in articles:
            analysis = _analyze(item["title"], item["content"])

            article = NewsArticle(
                title=item["title"],
                content=item["content"],
                url=item["url"],
                source=item["source"],
                published_at=item["published_at"],
                relevance_score=analysis.get("relevance_score", 0) / 10,
                is_relevant=analysis.get("is_relevant", False),
                sentiment=analysis.get("sentiment", "Neutral"),
                coin_symbol=analysis.get("coin_symbol"),
                category=analysis.get("category", "other"),
            )
            db.add(article)
            try:
                db.commit()
                added += 1
            except IntegrityError:
                db.rollback()  # url unique constraint race condition

            time.sleep(13)  # gemini-2.5-flash free tier: 5 RPM → 12s/req minimum
    finally:
        db.close()

    return added
