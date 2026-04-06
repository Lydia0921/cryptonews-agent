---
name: relevance-analyzer
description: 調整或審查 agents/monitor_agent.py 的相關性判斷邏輯時使用，包含評分標準、情緒分類規則、Gemini prompt 設計原則、常見錯誤案例。
---

# 新聞相關性分析 Skill

## 觸發時機
- 修改 `agents/monitor_agent.py` 的 `ANALYSIS_PROMPT` 或 `analyze_article()`
- 判斷結果品質不佳（誤判、漏判）需要調校
- 新增評分維度或情緒分類邏輯

---

## 評分標準（整數 0–10）

Gemini prompt 要求回傳整數，存入 DB 前除以 10 正規化為 0.0–1.0：

```python
relevance_score=analysis.get("relevance_score", 0) / 10  # in monitor_agent.py
```

| 分數 | 說明 | `is_relevant` |
|------|------|--------------|
| 9–10 | 主標題直接報導，含具體數字/事件（ETF 通過、SEC 起訴） | `true` |
| 7–8  | 深度相關，文章主體涉及 crypto 市場影響 | `true` ← 門檻 |
| 5–6  | 間接提及，作為背景或比較基準 | `false` |
| 0–4  | 幾乎不相關（廣告、技術教學、無市場影響） | `false` |

`is_relevant` 門檻固定在 **score >= 7**，由 prompt 中明確要求（`true if relevance_score >= 7`），不要讓 Gemini 自己判斷門檻。

---

## 情緒分類規則（Bullish / Bearish / Neutral）

| 情緒 | 判斷依據 | 典型關鍵字 |
|------|---------|-----------|
| **Bullish** | 利多消息，預期價格上漲 | ETF approved, institutional adoption, SEC win, whale accumulation, all-time high |
| **Bearish** | 利空消息，預期價格下跌 | ban, crackdown, hack, rug pull, liquidation, SEC lawsuit, exchange collapse |
| **Neutral** | 技術分析、數據報告、無明確方向 | on-chain data, market report, protocol upgrade (無明確漲跌預期) |

**注意：** 欄位值必須首字大寫（`Bullish` 而非 `bullish`），前端 CSS class `badge-Bullish` 直接依此對應。

---

## 現行 Prompt（monitor_agent.py 實際版本）

```python
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
```

**設計原則：**
1. `Return JSON only, no other text` — 防止 Gemini 在 JSON 前後加說明文字導致解析失敗
2. `is_relevant` 門檻明確寫在 prompt 裡，避免 Gemini 自行決定
3. `coin_symbol` 要求 null 而非空字串，否則 DB 存入 `""` 導致 ticker 顯示空標籤
4. `content[:800]` 截斷 — 標題 + 首段已足夠判斷，節省 token 且加快回應
5. 必須設定 `response_mime_type="application/json"` 確保 Gemini 輸出合法 JSON

---

## Gemini API 呼叫模板

```python
from google import genai
from google.genai import types

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def analyze_article(title: str, content: str) -> dict:
    prompt = ANALYSIS_PROMPT.format(title=title, content=content[:800])
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
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
```

---

## 加分關鍵字（高相關性觸發詞）

這些詞出現在標題時，score 通常在 8–10：

```
SEC, CFTC, ETF, spot ETF, approval, lawsuit, crackdown
whale, liquidation, short squeeze, all-time high, ATH
exchange hack, rug pull, insolvency, bankruptcy
Federal Reserve, interest rate (crypto 脈絡下)
Bitcoin halving, Ethereum upgrade, layer 2
```

---

## 排除條件（score 應給 0–3）

直接排除或給低分的模式：
- 標題含 `sponsored`, `advertisement`, `partner content`
- 文章主體是價格技術分析教學，無市場事件
- 提及 crypto 只是比喻（"volatile as Bitcoin"）
- NFT 個人藝術品拍賣，無市場規模數據

---

## 常見錯誤案例

### 誤判 1：情緒首字未大寫
```json
// ❌ Gemini 回傳
{"sentiment": "bullish"}

// 前端 CSS class 找不到 badge-bullish，badge 不顯示
// 修正：prompt 明確列舉 "Bullish | Bearish | Neutral"
```

### 誤判 2：coin_symbol 回傳空字串
```json
// ❌
{"coin_symbol": ""}

// DB 存入空字串，前端顯示空白 badge chip
// 修正：prompt 明確說 "null if none specifically mentioned"
```

### 誤判 3：JSON 解析失敗（Gemini 加了 markdown）
```
// ❌ Gemini 回傳
```json
{"relevance_score": 8, ...}
```

// json.loads() 失敗，fallback 給 is_relevant=False
// 修正：已有 response_mime_type="application/json"，通常不會發生
// 若仍發生，可用 response.text.strip().lstrip("```json").rstrip("```")
```

### 誤判 4：rate limit（免費版 5 RPM）
```python
# ❌ 連續呼叫觸發 429
for item in articles:
    analyze_article(...)  # 無 delay

# ✅ 現行實作
time.sleep(13)  # 5 RPM = 12s/req minimum，加 1s buffer
```

---

## 調校流程

1. 從 DB 撈出誤判案例：`SELECT title, relevance_score, is_relevant FROM news_articles WHERE is_relevant=0 ORDER BY relevance_score DESC LIMIT 10`
2. 手動判斷這些文章是否應該入選
3. 修改 `ANALYSIS_PROMPT` 的評分說明或範例
4. 用 `python -m agents.monitor_agent` 重跑，比對新舊結果
