# 金融新聞監控網站 — 專案指引

## 協作風格

DO NOT GIVE ME HIGH LEVEL SHIT, IF I ASK FOR FIX OR EXPLANATION, I WANT ACTUAL CODE OR EXPLANATION!!! I DON'T WANT "Here's how you can blablabla"

- Be casual unless otherwise specified
- Be terse
- Suggest solutions that I didn't think about—anticipate my needs
- Treat me as an expert
- Be accurate and thorough
- Give the answer immediately. Provide detailed explanations and restate my query in your own words if necessary after giving the answer
- Value good arguments over authorities, the source is irrelevant
- Consider new technologies and contrarian ideas, not just the conventional wisdom
- You may use high levels of speculation or prediction, just flag it for me
- No moral lectures
- Discuss safety only when it's crucial and non-obvious
- Cite sources whenever possible at the end, not inline
- No need to mention your knowledge cutoff
- Please respect my prettier preferences when you provide code.
- Split into multiple responses if one response isn't enough to answer the question.

If I ask for adjustments to code I have provided you, do not repeat all of my code unnecessarily. Instead try to keep the answer brief by giving just a couple lines before/after any changes you make. Multiple code blocks are ok.

---


## 專案概覽

Crypto 新聞監控網站，聚焦三大核心功能：監管新聞警報（SEC、ETF、各國法規）、市場情緒分類（Bullish / Bearish / Neutral）、事件追蹤（同一事件的後續報導串在一起）。新聞來源為 NewsData.io Crypto News API，情緒與相關性判斷由 Gemini 負責。

**技術棧：**
- 後端：Python + FastAPI
- 資料庫：SQLite
- 前端：HTML / JavaScript（原生，無框架）
- AI Agent：Google Gemini API
- 新聞來源：NewsData.io（Crypto News API）

---

## 專案架構

```
small_project/
├── main.py                  # FastAPI 應用程式進入點
├── database.py              # SQLite 連線與資料表初始化
├── models.py                # SQLAlchemy 資料模型
├── agents/
│   ├── monitor_agent.py     # 新聞監控 Agent（抓取 + 相關性判斷）
│   └── qa_agent.py          # 新聞問答 Agent（RAG）
├── routers/
│   ├── news.py              # 新聞相關 API 路由
│   ├── qa.py                # 問答相關 API 路由
│   └── prices.py            # 幣種即時價格（CoinGecko）
├── static/
│   ├── index.html           # 主頁面
│   └── app.js               # 前端邏輯
├── tests/
│   ├── conftest.py          # pytest fixtures（in-memory SQLite + DI override）
│   ├── test_news.py         # news 路由測試（9 cases）
│   └── test_qa.py           # QA 路由測試（6 cases，mock Gemini）
├── requirements.txt
└── CLAUDE.md
```

---

## 開發指令

```bash
# 安裝相依套件
pip install -r requirements.txt

# 啟動開發伺服器
uvicorn main:app --reload --port 8000

# 執行測試
pytest

# 手動觸發新聞監控（測試用）
python -m agents.monitor_agent
```

---

## 核心功能說明

### 1. 新聞監控 Agent（`agents/monitor_agent.py`）

- **職責：** 定期從 NewsData.io 抓取 Crypto 新聞，透過 Gemini 判斷相關性並分類情緒，將符合條件的新聞存入 SQLite。
- **觸發方式：** 排程（APScheduler）或手動呼叫 API。
- **Gemini 判斷輸出：** `is_relevant`, `relevance_score`, `sentiment`（Bullish/Bearish/Neutral）, `category`（regulation/market/technical）, `coin_symbol`
- **資料表：** `news_articles`（id, title, content, url, source, published_at, relevance_score, is_relevant, coin_symbol, sentiment, category, created_at）

### 2. 新聞問答 Agent（`agents/qa_agent.py`）

- **職責：** 接受使用者的自然語言問題，從資料庫檢索相關新聞（RAG），組成 context 後呼叫 **Gemini API** 產生回答。
- **⚠️ 注意：** 使用 **Gemini**（非 Claude API）。英文問答效果較佳；中文問題會搜到結果，但 Gemini 回答品質不如英文。
- **資料表：** `qa_sessions`（id, question, answer, referenced_articles, created_at）

#### RAG 流程設計

```
使用者問題
    │
    ▼
[1. Query Parsing]
    - 用 regex 提取 ASCII token（ticker、英文關鍵字）+ CJK 字串段落
    - 上限 6 個 token，避免 OR 條件爆炸
    │
    ▼
[2. Retrieval — SQLite keyword search]
    - 對 title + content 做 ilike OR-filter
    - 僅搜 is_relevant=True 的文章（過濾低品質）
    - ORDER BY published_at DESC，取最新 8 篇
    - 限制：無語意理解，同義詞、縮寫（e.g. BTC vs Bitcoin）需靠 keyword 覆蓋
    │
    ▼
[3. Context Assembly]
    - 每篇格式：標題 / 來源 / 日期 / 內容前 300 字
    - 全部串接，總長約 ~3000 tokens（遠低於 gemini-2.5-flash 上限）
    │
    ▼
[4. Generation — Gemini]
    - System instruction 要求：只根據提供的文章回答、引用來源、資訊不足時直說
    - 不限制輸出格式（讓 Gemini 自由發揮較自然）
    │
    ▼
[5. Persist]
    - 儲存 question / answer / referenced article ids → qa_sessions
```

#### 已知限制與改進方向（未實作）

| 問題 | 現況 | 改進方向 |
|------|------|---------|
| 語意搜尋 | keyword ilike | 加 embedding（e.g. text-embedding-004）+ cosine similarity |
| 同義詞 | BTC ≠ Bitcoin | Query expansion：問題先過一次 LLM 展開同義詞 |
| 中文效果差 | Gemini 中文理解弱 | 換 Claude API 或 Gemini 1.5 Pro（中文較強） |
| Reranking | 取前 8 直接用 | 加 cross-encoder reranker 篩最相關 3-4 篇 |

---

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/news` | 取得新聞列表（支援分頁、過濾） |
| GET | `/api/news/{id}` | 取得單篇新聞 |
| POST | `/api/monitor/trigger` | 手動觸發一次新聞監控 |
| POST | `/api/qa` | 送出問題，取得 RAG 回答 |
| GET | `/api/qa/history` | 取得問答歷史 |
| GET | `/api/prices` | 取得幣種即時價格與 24h 漲跌幅 |

---

## 環境變數

```
GEMINI_API_KEY=        # Google Gemini API 金鑰（必填）
NEWSDATA_API_KEY=      # NewsData.io API 金鑰（必填）
DATABASE_URL=          # SQLite 路徑，預設 sqlite:///./news.db
MONITOR_INTERVAL=      # 監控間隔（分鐘），預設 30
```

使用 `.env` 檔案搭配 `python-dotenv` 載入，**不可將 `.env` 提交至版本控制**。

---

## NewsData.io 使用規範

- **Crypto 專用 endpoint：** `GET https://newsdata.io/api/1/crypto`（不是 `/news` 加 category，`cryptocurrency` 不是合法 category 值）
- 常用參數：`apikey`, `q`（關鍵字）, `language`（`en` / `zh`）
- 同一則新聞常被多個來源轉載，`news_articles.url` 已設 `unique=True` 自動去重
- 免費版延遲約 12 小時，付費版才有即時新聞
- API 回傳欄位對應 model：

| NewsData.io 欄位 | model 欄位 |
|-----------------|-----------|
| `title` | `title` |
| `content` | `content` |
| `link` | `url` |
| `source_id` | `source` |
| `pubDate` | `published_at` |

---

## Gemini API 使用規範

- 套件：`google-genai`（新 SDK，舊的 `google-generativeai` 已棄用）
- 所有 Gemini API 呼叫集中在 `agents/` 目錄，不在路由層直接呼叫。
- 預設模型：`gemini-2.5-flash`（`gemini-1.5-flash` 已下架；`2.0-flash-lite` 有 quota 問題時用此替代）
- 相關性判斷 prompt 需明確要求回傳結構化 JSON，使用 `response_mime_type="application/json"` 確保格式。
- 問答 Agent 的 context 長度需控制在合理範圍，`gemini-2.5-flash` 支援大型 context window。
- 初始化方式：

```python
from google import genai
from google.genai import types

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 一般文字生成
response = _client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(response_mime_type="application/json"),
)

# 帶 system instruction
response = _client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[types.Content(role="user", parts=[types.Part(text=question)])],
    config=types.GenerateContentConfig(system_instruction=system_prompt),
)
```

---

## 資料庫規範

- 使用 SQLAlchemy ORM，不直接拼接 SQL 字串（防 SQL Injection）。
- 資料庫初始化在 `database.py` 的 `init_db()` 函式，應用程式啟動時呼叫一次。
- 修改資料表結構時，需同步更新 `models.py` 與對應的初始化邏輯。

---

## 前端規範

- 原生 HTML/JS，不引入前端框架。
- API 呼叫使用 `fetch()`，錯誤需顯示友善訊息給使用者。
- 新聞列表支援無限捲動或分頁載入，避免一次載入過多資料。
- 問答介面需顯示引用的新聞來源連結。

### Price Ticker Bar

- 頁面載入時呼叫 `/api/prices` 一次，失敗時靜默隱藏（不顯示 ticker bar），不影響主頁。
- 幣種來源：DB distinct `coin_symbol` ∪ 固定主流幣（BTC/ETH/SOL/XRP），順序以主流幣優先。
- 價格顯示規則：`>= $1` 顯示兩位小數；`>= $0.0001` 顯示六位小數；更小用科學記號（`toExponential(2)`）。
- Hover 暫停捲動動畫（CSS `animation-play-state: paused`）。
- 幣種 → CoinGecko ID 的 mapping 維護在 `routers/prices.py` 的 `SYMBOL_TO_ID`，新幣種需手動新增。

---

## 測試規範

- 使用 `pytest` 搭配 `httpx.AsyncClient` 測試 FastAPI 路由。
- Agent 測試使用 mock Gemini API 回應，不在 CI 中消耗真實 API 配額。
- 測試資料庫使用 in-memory SQLite（`:memory:`），測試結束後自動清除。
