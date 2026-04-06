# Crypto News Monitor

AI 驅動的加密貨幣新聞監控系統，聚焦三大核心：**監管新聞警報**、**市場情緒分類**、**RAG 問答**。

---

## 功能介紹

### Price Ticker Bar
頁面頂部自動滾動顯示主流幣種（BTC / ETH / SOL / XRP …）即時價格與 24h 漲跌幅，來源為 CoinGecko API。Hover 暫停滾動。

### 新聞列表
- 依相關性分數、情緒（Bullish / Bearish / Neutral）、分類（regulation / market / technical）篩選
- 支援分頁載入（Load more）
- 每篇顯示來源、時間、幣種標籤、AI 評分

### QA 問答
輸入自然語言問題，系統從資料庫檢索相關新聞（RAG），由 Gemini 2.5 Flash 生成回答並引用來源。

---

## 安裝步驟

**需求：** Python 3.10+、Node.js（製作 PPTX 時用到，非必要）

```bash
# 1. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝相依套件
pip install -r requirements.txt
```

---

## 環境變數設定

複製範本並填入 API 金鑰：

```bash
cp .env.example .env
```

`.env` 內容：

```env
GEMINI_API_KEY=        # Google Gemini API 金鑰（必填）
NEWSDATA_API_KEY=      # NewsData.io API 金鑰（必填）
DATABASE_URL=sqlite:///./news.db   # 預設值，可不改
MONITOR_INTERVAL=30               # 自動抓取間隔（分鐘）
```

> **注意：** `.env` 已加入 `.gitignore`，不會被提交。

---

## 啟動

```bash
# 啟動開發伺服器（含 hot reload）
uvicorn main:app --reload --port 8000
```

開啟瀏覽器訪問 [http://localhost:8000](http://localhost:8000)

啟動時會自動：
1. 初始化 SQLite 資料庫（`news.db`）
2. 立即執行一次新聞抓取與分析
3. 啟動排程，每 `MONITOR_INTERVAL` 分鐘自動執行

---

## 手動觸發

```bash
# 手動跑一次完整 pipeline（fetch + analyze）
python -m agents.monitor_agent

# 或透過 API
curl -X POST "http://localhost:8000/api/monitor/trigger"
```

---

## 執行測試

```bash
pytest
```

測試使用 in-memory SQLite，不影響正式資料庫。Gemini API 呼叫全部 mock。

---

## 技術架構

```
small_project/
├── main.py                  # FastAPI 進入點 + APScheduler
├── database.py              # SQLite 連線與資料表初始化
├── models.py                # SQLAlchemy 資料模型
├── agents/
│   ├── monitor_agent.py     # Orchestrator：串接 fetcher + analyzer
│   ├── fetcher_agent.py     # HTTP 抓取 NewsData.io + URL 去重
│   ├── analyzer_agent.py    # Gemini 分析 + 寫入 DB
│   └── qa_agent.py          # RAG 問答（檢索 + Gemini 生成）
├── routers/
│   ├── news.py              # 新聞 CRUD API + 手動觸發
│   ├── qa.py                # QA API + 歷史記錄
│   └── prices.py            # CoinGecko 即時價格
├── static/
│   ├── index.html           # 主頁面
│   └── app.js               # 前端邏輯
└── tests/
    ├── conftest.py          # pytest fixtures
    ├── test_news.py         # news 路由測試
    └── test_qa.py           # QA 路由測試（mock Gemini）
```

### 資料流

```
NewsData.io
    │
    ▼
fetcher_agent       ← HTTP GET + URL 去重（DB query）
    │
    ▼
analyzer_agent      ← Gemini 2.5 Flash 判斷相關性、情緒、幣種
    │
    ▼
SQLite (news.db)
    │
    ├──▶ FastAPI REST API
    │         └──▶ 前端（HTML/JS）
    │
    └──▶ qa_agent（RAG）
              └──▶ Gemini 2.5 Flash 生成回答
```

### API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/api/news` | 新聞列表（支援分頁、情緒/分類/幣種篩選）|
| `GET` | `/api/news/{id}` | 單篇新聞 |
| `POST` | `/api/monitor/trigger` | 手動觸發一次監控 |
| `POST` | `/api/qa` | 送出問題，取得 RAG 回答 |
| `GET` | `/api/qa/history` | 問答歷史 |
| `GET` | `/api/prices` | 幣種即時價格與 24h 漲跌幅 |

---

## Claude Code 整合

本專案使用 [Claude Code](https://claude.ai/code) 作為主要開發工具，並配置了以下自動化機制：

### CLAUDE.md
記錄完整的專案規範：技術棧、API 使用規範、Gemini SDK 初始化方式、DB 操作規範、前端規範等，讓 Claude 在每次對話中都有正確 context，減少重複說明。

### Skills（`.claude/skills/`）

| Skill | 觸發時機 | 用途 |
|-------|---------|------|
| `news-monitor-setup` | 設定/修改監控需求 | 產出關鍵字清單與 monitor_agent prompt 模板 |
| `relevance-analyzer` | 審查相關性判斷邏輯 | 提供評分標準、情緒分類規則、Gemini prompt 設計原則 |
| `test-generator` | 新增 endpoint 或 agent 後 | 生成符合本專案風格的 pytest 測試 |
| `report-formatter` | 輸出報告或 debug 日誌 | 統一輸出格式 |

### MCP Server（SQLite）

在 Claude Code 對話中直接查詢 `news.db`，不需離開對話視窗：

```json
// .claude/settings.local.json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/path/to/news.db"]
    }
  }
}
```

使用範例：
```
# 在 Claude Code 對話中
查詢 news_articles 有幾筆 Bullish 的新聞
→ Claude 直接 query DB 並回傳結果
```

### PreToolUse Hook（寫入保護）

自動攔截所有檔案寫入操作（`Write` / `Edit` / `MultiEdit`），確保只能修改專案目錄內的檔案：

```bash
# .claude/hooks/check_write_path.sh
# 寫入路徑超出專案目錄時印出警告並攔截
⚠️ BLOCKED: Attempt to write outside project directory: /tmp/test.txt
```

---

## 技術選型說明

| 決策 | 選擇 | 原因 |
|------|------|------|
| AI 模型 | Gemini 2.5 Flash | 支援大型 context window，free tier 可用，JSON output mode |
| 新聞來源 | NewsData.io `/crypto` endpoint | Crypto 專用 API，非 `/news?category=cryptocurrency` |
| 前端 | 原生 HTML/JS | 零框架依賴，降低部署複雜度 |
| ORM | SQLAlchemy | 防 SQL Injection，型別安全 |
| 去重 | URL unique constraint | 同一新聞多來源轉載，以 URL 為唯一鍵 |

---

## 已知限制

- **語意搜尋缺失**：QA 使用 keyword ilike，BTC ≠ Bitcoin 需靠關鍵字覆蓋
- **中文問答效果較差**：Gemini 中文理解弱於英文
- **Startup blocking**：初始 fetch 期間 API 不回應（Gemini 分析同步執行）
- **重複新聞**：同事件多家媒體轉載，URL 去重無法合併

改進方向：embedding 語意搜尋、SimHash 去重、cross-encoder reranking、Claude API 中文支援。
