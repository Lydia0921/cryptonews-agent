from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    url = Column(Text, unique=True, nullable=False)
    source = Column(Text)
    published_at = Column(DateTime)
    relevance_score = Column(Float)
    is_relevant = Column(Boolean, default=False)
    coin_symbol = Column(String(20))        # e.g. BTC, ETH
    sentiment = Column(String(20))          # Bullish / Bearish / Neutral
    category = Column(String(50))           # regulation / market / technical
    created_at = Column(DateTime, default=datetime.utcnow)


class QASession(Base):
    __tablename__ = "qa_sessions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    referenced_articles = Column(Text)  # JSON string: list of article ids
    created_at = Column(DateTime, default=datetime.utcnow)
