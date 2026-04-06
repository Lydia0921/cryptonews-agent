---
name: test-generator
description: 新增 API endpoint 或 agent 功能後，生成符合本專案風格的 pytest 測試。提供 conftest fixture 規範、mock Gemini 寫法、in-memory SQLite 使用規範、命名慣例。
---

# 測試生成 Skill

## 觸發時機
- 新增 `routers/` 下的 API endpoint 後
- 新增或修改 `agents/` 下的 agent 函式後
- 需要補齊現有功能的測試覆蓋率時

---

## 專案測試架構

```
tests/
├── conftest.py       # 共用 fixtures：in-memory DB、FastAPI test client
├── test_news.py      # routers/news.py 的 9 個測試
└── test_qa.py        # routers/qa.py + agents/qa_agent.py 的 6 個測試
```

執行：`pytest` 或 `pytest -v tests/test_news.py`

---

## conftest.py 規範（不要修改，直接使用）

```python
# tests/conftest.py — 現行實作，勿修改
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# ⚠️ 必須用 shared cache，讓多個連線看到同一個 in-memory DB
TEST_DB_URL = "sqlite:///file::memory:?cache=shared&uri=true"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)      # 每個 test 自動建/清 schema
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():                       # 需要 HTTP client 的 test 才宣告
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**為什麼用 shared cache URL：** 普通 `:memory:` 每個連線是獨立 DB。`setup_db` 建表在連線 A，FastAPI router 在連線 B 查詢會看不到表。`?cache=shared&uri=true` 讓所有連線共用同一個 in-memory DB。

---

## Router 測試模板（參考 test_news.py 風格）

### Seed 函式

每個 test 檔案定義一個 `_seed()` 函式，帶預設值 + `**kwargs` 覆寫：

```python
from datetime import datetime
from sqlalchemy.orm import Session
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
```

seed 完記得 `db.close()`，否則鎖住 in-memory DB。

### 測試命名規則

`test_{endpoint_or_feature}_{scenario}`

```python
def test_list_news_empty(client): ...          # GET /api/news，空資料庫
def test_list_news_returns_articles(client): ... # 正常回傳
def test_filter_by_sentiment(client): ...      # 過濾功能
def test_get_article_not_found(client): ...    # 404 edge case
```

### 標準 assert 風格

```python
def test_filter_by_coin(client):
    db = TestingSession()
    _seed(db, url="https://example.com/1", coin_symbol="BTC")
    _seed(db, url="https://example.com/2", coin_symbol="ETH", title="ETH news")
    db.close()

    res = client.get("/api/news?coin_symbol=btc")   # 測試大小寫 normalization
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["results"][0]["coin_symbol"] == "BTC"
```

分頁測試固定模式：

```python
def test_pagination(client):
    db = TestingSession()
    for i in range(5):
        _seed(db, url=f"https://example.com/{i}", title=f"Article {i}")
    db.close()

    res = client.get("/api/news?page=1&page_size=2")
    data = res.json()
    assert data["total"] == 5
    assert len(data["results"]) == 2
```

---

## Agent 測試模板（參考 test_qa.py 風格）

Agent 直接呼叫 `SessionLocal()`，不走 FastAPI DI，所以需要額外 patch：

### Fixture：把 agent 的 SessionLocal 指向測試 DB

```python
import pytest
from unittest.mock import MagicMock, patch
from tests.conftest import TestingSession

@pytest.fixture(autouse=True)
def patch_agent_session():
    """Route agent's direct SessionLocal() calls to the test DB."""
    with patch("agents.your_agent.SessionLocal", TestingSession):
        yield
```

`autouse=True` → 檔案裡所有 test 自動套用，不用逐一宣告。

### Mock Gemini API

```python
def test_your_feature_with_articles(client):
    db = TestingSession()
    _seed_article(db)
    db.close()

    mock_response = MagicMock()
    mock_response.text = "Mocked answer from Gemini."

    with patch("agents.your_agent._client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response
        res = client.post("/api/your-endpoint", json={"question": "test"})

    assert res.status_code == 200
    assert res.json()["answer"] == "Mocked answer from Gemini."
```

**為什麼 patch `_client` 而非 `genai.Client`：** agent 在模組載入時就建立了 `_client = genai.Client(...)` 這個物件，patch `genai.Client` 無法替換已建立的實例。直接 patch 模組內的 `_client` 名稱才有效。

### JSON 回應的 Gemini mock

當 agent 使用 `json.loads(response.text)` 時：

```python
mock_response = MagicMock()
mock_response.text = '{"is_relevant": true, "relevance_score": 8, "sentiment": "Bullish", "coin_symbol": "BTC", "category": "regulation"}'

with patch("agents.monitor_agent._client") as mock_client:
    mock_client.models.generate_content.return_value = mock_response
    result = analyze_article("Bitcoin ETF approved", "The SEC approved...")

assert result["is_relevant"] is True
assert result["sentiment"] == "Bullish"
```

---

## 新 Endpoint 測試清單

每個新 endpoint 應涵蓋的最小測試集：

| 情境 | 必測 |
|------|------|
| 空資料庫 / 空結果 | ✅ |
| 正常回傳 + 欄位驗證 | ✅ |
| 每個 filter 參數 | ✅ |
| 分頁（total 正確、results 筆數正確） | ✅ |
| 404 / 資源不存在 | ✅ |
| 400 / 非法輸入 | ✅（有 validation 的 endpoint） |
| 排序方向正確（newest first） | ✅（有排序的 endpoint） |

---

## 完整新 Endpoint 範例

假設新增 `GET /api/events` 和 `POST /api/events`：

```python
# tests/test_events.py
from datetime import datetime
from models import Event          # 假設的新 model
from tests.conftest import TestingSession


def _seed_event(db, **kwargs):
    defaults = dict(
        title="BTC halving",
        url="https://example.com/event/1",
        event_date=datetime(2024, 4, 20),
        category="technical",
    )
    defaults.update(kwargs)
    e = Event(**defaults)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def test_list_events_empty(client):
    res = client.get("/api/events")
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_list_events_returns_data(client):
    db = TestingSession()
    _seed_event(db)
    db.close()

    res = client.get("/api/events")
    data = res.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "BTC halving"


def test_create_event(client):
    res = client.post("/api/events", json={
        "title": "ETH merge",
        "url": "https://example.com/eth",
        "event_date": "2024-09-15T00:00:00",
        "category": "technical",
    })
    assert res.status_code == 201
    assert res.json()["title"] == "ETH merge"


def test_get_event_not_found(client):
    res = client.get("/api/events/9999")
    assert res.status_code == 404
```

---

## 常見錯誤

### "no such table: news_articles"
原因：用了普通 `:memory:` URL，`setup_db` 和 router 連線不同。
修正：確認 `TEST_DB_URL = "sqlite:///file::memory:?cache=shared&uri=true"`

### patch 無效，仍然呼叫真實 Gemini
原因：patch 路徑錯誤。路徑必須是 **被 patch 的名稱所在的模組**，不是定義它的模組。
```python
# ❌ patch 定義位置
with patch("google.genai.Client") as mock: ...

# ✅ patch 使用位置（agent 模組內的名稱）
with patch("agents.qa_agent._client") as mock: ...
```

### setup_db autouse 但 test 仍看到舊資料
原因：seed 後沒有 `db.close()`，連線未釋放，`drop_all` 在清理時被跳過。
修正：seed 函式呼叫後立即 `db.close()`。
