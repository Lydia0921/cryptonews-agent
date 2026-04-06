from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from models import NewsArticle
from tests.conftest import TestingSession


@pytest.fixture(autouse=True)
def patch_qa_session():
    """Route qa_agent's direct SessionLocal() calls to the test DB."""
    with patch("agents.qa_agent.SessionLocal", TestingSession):
        yield


def _seed_article(db, **kwargs):
    defaults = dict(
        title="SEC approves Bitcoin ETF",
        content="The SEC has officially approved a Bitcoin ETF, marking a historic moment.",
        url="https://example.com/1",
        source="coindesk",
        published_at=datetime(2024, 1, 15),
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


# ── POST /api/qa ──────────────────────────────────────────────────────────────

def test_qa_empty_question(client):
    res = client.post("/api/qa", json={"question": "  "})
    assert res.status_code == 400


def test_qa_no_articles(client):
    mock_response = MagicMock()
    mock_response.text = "No relevant articles found in the database to answer this question."

    with patch("agents.qa_agent._client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response
        res = client.post("/api/qa", json={"question": "What is happening with Bitcoin?"})

    assert res.status_code == 200
    data = res.json()
    assert "No relevant articles" in data["answer"]
    assert data["articles"] == []


def test_qa_with_articles(client):
    db = TestingSession()
    _seed_article(db)
    db.close()

    mock_response = MagicMock()
    mock_response.text = "The SEC approved a Bitcoin ETF, which is bullish for BTC."

    with patch("agents.qa_agent._client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response
        res = client.post("/api/qa", json={"question": "SEC bitcoin ETF"})

    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "The SEC approved a Bitcoin ETF, which is bullish for BTC."
    assert len(data["articles"]) >= 1
    assert data["articles"][0]["coin_symbol"] == "BTC"


def test_qa_saves_session(client):
    mock_response = MagicMock()
    mock_response.text = "Some answer."

    with patch("agents.qa_agent._client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response
        res = client.post("/api/qa", json={"question": "test question"})

    assert res.status_code == 200
    assert res.json()["id"] is not None


# ── GET /api/qa/history ───────────────────────────────────────────────────────

def test_qa_history_empty(client):
    res = client.get("/api/qa/history")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_qa_history_after_ask(client):
    mock_response = MagicMock()
    mock_response.text = "Answer."

    with patch("agents.qa_agent._client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response
        client.post("/api/qa", json={"question": "first question"})
        client.post("/api/qa", json={"question": "second question"})

    res = client.get("/api/qa/history")
    data = res.json()
    assert data["total"] == 2
    # newest first
    assert data["results"][0]["question"] == "second question"
