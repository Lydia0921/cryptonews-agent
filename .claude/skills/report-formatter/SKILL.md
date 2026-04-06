---
name: report-formatter
description: 新聞摘要與監控報告的標準輸出格式，涵蓋 debug 日誌、前端卡片、QA 引用區塊、以及面試 demo 展示格式。
---

# Crypto 報告格式化 Skill

## 觸發時機
- 設計或修改前端卡片顯示邏輯（`static/app.js` 的 `cardHTML()`）
- 新增 email / CLI 報告輸出功能
- 面試 demo 需要展示系統輸出範例

---

## Type A — 前端新聞卡片（現行實作）

對應 `static/app.js` 的 `cardHTML()` 函式：

```
┌─────────────────────────────────────────┬──────────┐
│ [標題，可點擊連結]                         │ Bullish  │
│ coindesk · Jan 15, 10:30 AM · regulation │ BTC      │
│                                          │ Score 9/10│
└─────────────────────────────────────────┴──────────┘
```

**情緒 badge CSS class**（必須首字大寫）：
- `badge-Bullish` → 綠底
- `badge-Bearish` → 紅底
- `badge-Neutral` → 橘底

**Score 顯示邏輯**：`(relevance_score * 10).toFixed(0)` → DB 0.0–1.0 轉回 0–10 整數顯示

---

## Type B — CLI Debug 輸出格式

用於 `python -m agents.monitor_agent` 或開發時 log，快速確認處理結果：

```
[+] Added: Bitcoin ETF approved by SEC
    Source: coindesk | 2024-01-15 12:00
    Score: 9/10 | Bullish | BTC | regulation

[~] Skipped (duplicate): https://example.com/same-url

[-] Filtered (score 4): Minor crypto mention in tech article
```

```python
def log_article(article: NewsArticle, status: str):
    if status == "added":
        print(f"[+] Added: {article.title}")
        print(f"    Source: {article.source} | {article.published_at:%Y-%m-%d %H:%M}")
        score_int = int((article.relevance_score or 0) * 10)
        print(f"    Score: {score_int}/10 | {article.sentiment} | {article.coin_symbol} | {article.category}")
    elif status == "duplicate":
        print(f"[~] Skipped (duplicate): {article.url}")
    elif status == "filtered":
        score_int = int((article.relevance_score or 0) * 10)
        print(f"[-] Filtered (score {score_int}): {article.title}")
```

---

## Type C — QA Agent 引用區塊（現行實作）

對應 `static/app.js` 的 `askQuestion()` 與 `routers/qa.py` 的回應格式：

**API 回應結構：**
```json
{
  "id": 42,
  "answer": "The SEC approved a Bitcoin spot ETF on January 10, 2024...",
  "articles": [
    {
      "id": 1,
      "title": "SEC approves Bitcoin ETF",
      "url": "https://coindesk.com/...",
      "coin_symbol": "BTC"
    }
  ]
}
```

**前端顯示：**
```
[Answer text rendered in .qa-answer]

Sources:
  SEC approves Bitcoin ETF    BlackRock files for ETH ETF
  (clickable links to original articles)
```

---

## Type D — 面試 Demo 展示格式

展示系統端到端能力時使用，格式清晰、重點突出：

```
═══════════════════════════════════════════════
  CRYPTO NEWS MONITOR — Live Demo
  Fetched: 2024-01-15 12:00 UTC
═══════════════════════════════════════════════

HIGH RELEVANCE (9–10/10)
────────────────────────
• [Bullish][BTC] SEC Officially Approves Bitcoin Spot ETF
  coindesk.com · Jan 15, 10:30 AM
  → First ever spot Bitcoin ETF approval, historic milestone

• [Bearish][ETH] Ethereum Foundation Wallets Under Investigation
  theblock.co · Jan 15, 09:15 AM
  → Swiss authorities examining foundation finances

MEDIUM RELEVANCE (7–8/10)
──────────────────────────
• [Neutral][SOL] Solana Network Processes Record 65K TPS
  decrypt.co · Jan 15, 08:00 AM

═══════════════════════════════════════════════
  Q&A: "What are the latest SEC crypto decisions?"
───────────────────────────────────────────────
  The SEC has approved the first Bitcoin spot ETF on Jan 10,
  marking a turning point for institutional crypto adoption.
  Previously, the SEC had rejected 20+ similar applications
  since 2013. (Source: coindesk.com)
═══════════════════════════════════════════════
```

```python
def format_demo_report(articles: list[NewsArticle]) -> str:
    lines = ["HIGH RELEVANCE (9–10/10)", "─" * 40]
    for a in articles:
        if a.relevance_score >= 0.9:
            score_int = int(a.relevance_score * 10)
            coin = f"[{a.coin_symbol}]" if a.coin_symbol else ""
            lines.append(f"• [{a.sentiment}]{coin} {a.title}")
            lines.append(f"  {a.source} · {a.published_at:%b %d, %H:%M}")
    return "\n".join(lines)
```

---

## 格式化工具函式

```python
from models import NewsArticle

SENTIMENT_EMOJI = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}

def score_to_tier(score: float) -> str:
    if score >= 0.9: return "high"
    if score >= 0.7: return "medium"
    return "low"

def format_published_at(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%b %d, %H:%M")

def format_score_display(score: float) -> str:
    """DB 0.0–1.0 → display '9/10' (matches frontend logic)"""
    return f"{int(score * 10)}/10"
```

---

## 注意事項

- `summary` 欄位**不在** `news_articles` schema 中。若需要摘要，需在格式化時呼叫 Gemini 或用 `content[:150]` 替代。
- `relevance_score` 在 DB 中是 0.0–1.0（float），前端顯示 `* 10` 轉回整數，CLI/report 輸出也應一致。
- 情緒首字大寫（`Bullish` 非 `bullish`）— 前端 CSS class `badge-Bullish` 直接對應，大小寫錯誤會導致 badge 樣式消失。
- 日期格式建議統一用 `%b %d, %H:%M`（Jan 15, 10:30）或 ISO 8601，避免混用。
